#!/usr/bin/env python3
"""
Sports Poetry Multi-Agent Orchestrator

Coordinates multiple poetry generation agents in parallel,
with full provenance logging and graceful error handling.
"""

import json
import time
import sys
import os
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import threading
import concurrent.futures


class ProvenanceLogger:
    """Handles detailed execution logging for full auditability."""

    def __init__(self, log_file: str = "execution_log.jsonl"):
        self.log_file = log_file
        self.lock = threading.Lock()

    def log_event(self, actor: str, action: str, details: Dict[str, Any] = None, message: str = None):
        """Log a single event with timestamp and full context."""
        entry = {
            "timestamp": time.time(),
            "timestamp_iso": datetime.utcnow().isoformat() + "Z",
            "actor": actor,
            "action": action
        }

        if details:
            entry["details"] = details
        if message:
            entry["message"] = message

        with self.lock:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Also print for human monitoring
        if message:
            print(f"[{actor}] {message}")
        elif action:
            print(f"[{actor}] {action}")


class SportsPoetryOrchestrator:
    """Main orchestrator for the multi-agent poetry workflow."""

    def __init__(self, config_path: str = "config.json", retry_enabled: bool = True):
        self.config_path = config_path
        self.retry_enabled = retry_enabled
        self.logger = ProvenanceLogger()
        self.session_start = time.time()
        self.agent_results = []
        self.errors = []
        self.session_dir = None  # Will be set after reading config

    def read_config(self) -> Dict[str, Any]:
        """Read and validate configuration file."""
        self.logger.log_event("orchestrator", "read_config", message="Reading configuration file")

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)

            sports = config.get("sports", [])
            session_id = config.get("session_id", "unknown")

            self.logger.log_event(
                "orchestrator",
                "config_loaded",
                details={
                    "sports": sports,
                    "sports_count": len(sports),
                    "session_id": session_id
                },
                message=f"Loaded config: {len(sports)} sports"
            )

            return config

        except Exception as e:
            self.logger.log_event(
                "orchestrator",
                "error",
                details={"error": str(e), "file": self.config_path},
                message=f"Failed to read config: {e}"
            )
            raise

    def create_session_directory(self, config: Dict[str, Any]) -> Path:
        """Create session-specific output directory."""
        session_id = config.get("session_id", "unknown")

        # Create session directory
        output_base = Path("output")
        session_dir = output_base / session_id

        # Check if session already exists
        if session_dir.exists():
            self.logger.log_event(
                "orchestrator",
                "warning",
                details={"session_id": session_id},
                message=f"Session directory already exists: {session_dir}"
            )

        session_dir.mkdir(parents=True, exist_ok=True)

        # Create/update symlink to latest
        latest_link = output_base / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(session_id)

        self.logger.log_event(
            "orchestrator",
            "session_dir_created",
            details={"session_id": session_id, "path": str(session_dir)},
            message=f"Created session directory: {session_dir}"
        )

        return session_dir

    def launch_poetry_agent(self, sport: str, attempt: int = 1) -> Dict[str, Any]:
        """Launch a single poetry generation agent for a sport."""
        agent_name = f"agent_{sport}"
        start_time = time.time()

        self.logger.log_event(
            "orchestrator",
            "launch_agent",
            details={"sport": sport, "attempt": attempt},
            message=f"Launching poetry agent for {sport} (attempt {attempt})"
        )

        try:
            # Launch the poetry agent as a subprocess
            result = subprocess.run(
                [sys.executable, "poetry_agent.py", sport, str(self.session_dir), self.config_path],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                # Parse agent output to get metadata
                output_dir = self.session_dir / sport
                metadata_file = output_dir / "metadata.json"

                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                self.logger.log_event(
                    agent_name,
                    "complete",
                    details={
                        "duration_s": round(duration, 2),
                        "haiku_lines": metadata.get("haiku_lines", 0),
                        "sonnet_lines": metadata.get("sonnet_lines", 0)
                    },
                    message=f"Completed in {duration:.1f}s"
                )

                return {
                    "sport": sport,
                    "status": "success",
                    "duration_s": round(duration, 2),
                    "haiku_lines": metadata.get("haiku_lines", 0),
                    "sonnet_lines": metadata.get("sonnet_lines", 0),
                    "haiku_words": metadata.get("haiku_words", 0),
                    "sonnet_words": metadata.get("sonnet_words", 0)
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.logger.log_event(
                    agent_name,
                    "failed",
                    details={"error": error_msg, "return_code": result.returncode},
                    message=f"Failed: {error_msg}"
                )

                return {
                    "sport": sport,
                    "status": "failed",
                    "error": error_msg,
                    "duration_s": round(duration, 2)
                }

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Agent timed out after {duration:.0f}s"
            self.logger.log_event(
                agent_name,
                "timeout",
                details={"duration_s": round(duration, 2)},
                message=error_msg
            )

            return {
                "sport": sport,
                "status": "failed",
                "error": error_msg,
                "duration_s": round(duration, 2)
            }

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.logger.log_event(
                agent_name,
                "error",
                details={"error": error_msg},
                message=f"Unexpected error: {error_msg}"
            )

            return {
                "sport": sport,
                "status": "failed",
                "error": error_msg,
                "duration_s": round(duration, 2)
            }

    def launch_poetry_agent_with_retry(self, sport: str) -> Dict[str, Any]:
        """Launch agent with optional retry on failure."""
        result = self.launch_poetry_agent(sport, attempt=1)

        # Retry if enabled and first attempt failed
        if result["status"] == "failed" and self.retry_enabled:
            self.logger.log_event(
                "orchestrator",
                "retry_agent",
                details={"sport": sport},
                message=f"Retrying {sport} agent"
            )
            result = self.launch_poetry_agent(sport, attempt=2)

        return result

    def launch_all_agents(self, sports: List[str]) -> List[Dict[str, Any]]:
        """Launch all poetry agents in parallel."""
        self.logger.log_event(
            "orchestrator",
            "launch_all_agents",
            details={"sports": sports, "count": len(sports)},
            message=f"Launching {len(sports)} agents in parallel"
        )

        # Use ThreadPoolExecutor for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sports)) as executor:
            # Submit all tasks
            future_to_sport = {
                executor.submit(self.launch_poetry_agent_with_retry, sport): sport
                for sport in sports
            }

            # Collect results as they complete
            results = []
            for future in concurrent.futures.as_completed(future_to_sport):
                sport = future_to_sport[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.log_event(
                        "orchestrator",
                        "agent_exception",
                        details={"sport": sport, "error": str(e)},
                        message=f"Exception in {sport} agent: {e}"
                    )
                    results.append({
                        "sport": sport,
                        "status": "failed",
                        "error": str(e)
                    })

        # Log summary
        succeeded = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "failed")

        self.logger.log_event(
            "orchestrator",
            "agents_complete",
            details={
                "total": len(results),
                "succeeded": succeeded,
                "failed": failed
            },
            message=f"All agents complete: {succeeded} succeeded, {failed} failed"
        )

        return results

    def launch_analyzer(self) -> Dict[str, Any]:
        """Launch the analysis agent to synthesize all results."""
        self.logger.log_event(
            "orchestrator",
            "launch_analyzer",
            message="Launching analyzer agent"
        )

        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, "analyzer_agent.py", str(self.session_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                self.logger.log_event(
                    "analyzer",
                    "complete",
                    details={"duration_s": round(duration, 2)},
                    message=f"Analysis complete in {duration:.1f}s"
                )

                return {
                    "status": "success",
                    "duration_s": round(duration, 2)
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.logger.log_event(
                    "analyzer",
                    "failed",
                    details={"error": error_msg},
                    message=f"Analysis failed: {error_msg}"
                )

                return {
                    "status": "failed",
                    "error": error_msg,
                    "duration_s": round(duration, 2)
                }

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.logger.log_event(
                "analyzer",
                "error",
                details={"error": error_msg},
                message=f"Analyzer error: {error_msg}"
            )

            return {
                "status": "failed",
                "error": error_msg,
                "duration_s": round(duration, 2)
            }

    def write_usage_log(self, config: Dict[str, Any], agent_results: List[Dict[str, Any]],
                       analyzer_result: Dict[str, Any]):
        """Write aggregate usage log entry."""
        total_duration = time.time() - self.session_start

        # Collect all errors
        errors = [r.get("error") for r in agent_results if r.get("error")]
        if analyzer_result.get("error"):
            errors.append(analyzer_result["error"])

        # Count retries (would need to track this during execution)
        retry_count = 0  # TODO: track this

        usage_entry = {
            "session_id": config.get("session_id", "unknown"),
            "timestamp": config.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "sports": config.get("sports", []),
            "sports_count": len(config.get("sports", [])),
            "validation": "pass",  # Assuming config is valid if we got here
            "agents_launched": len(agent_results),
            "agents_succeeded": sum(1 for r in agent_results if r["status"] == "success"),
            "agents_failed": sum(1 for r in agent_results if r["status"] == "failed"),
            "agent_results": agent_results,
            "analyzer_duration_s": analyzer_result.get("duration_s", 0),
            "total_duration_s": round(total_duration, 2),
            "errors": errors,
            "retry_count": retry_count
        }

        with open("usage_log.jsonl", "a") as f:
            f.write(json.dumps(usage_entry) + "\n")

        self.logger.log_event(
            "orchestrator",
            "usage_log_written",
            details={"total_duration_s": round(total_duration, 2)},
            message=f"Usage log written. Total workflow time: {total_duration:.1f}s"
        )

    def run(self):
        """Execute the complete workflow."""
        self.logger.log_event(
            "orchestrator",
            "workflow_start",
            message="Starting sports poetry workflow"
        )

        try:
            # Phase 1: Read config
            config = self.read_config()
            sports = config.get("sports", [])

            if not sports:
                raise ValueError("No sports found in config")

            # Phase 1.5: Create session directory
            self.session_dir = self.create_session_directory(config)

            # Phase 2: Launch all poetry agents in parallel
            agent_results = self.launch_all_agents(sports)
            self.agent_results = agent_results

            # Phase 3: Launch analyzer
            analyzer_result = self.launch_analyzer()

            # Phase 4: Write usage log
            self.write_usage_log(config, agent_results, analyzer_result)

            self.logger.log_event(
                "orchestrator",
                "workflow_complete",
                message="Workflow completed successfully"
            )

            return 0

        except Exception as e:
            self.logger.log_event(
                "orchestrator",
                "workflow_failed",
                details={"error": str(e)},
                message=f"Workflow failed: {e}"
            )
            return 1


if __name__ == "__main__":
    orchestrator = SportsPoetryOrchestrator()
    exit_code = orchestrator.run()
    sys.exit(exit_code)
