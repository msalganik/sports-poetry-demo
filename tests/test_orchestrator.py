"""Integration tests for orchestrator.py

These tests run the full workflow end-to-end.
"""

import pytest
import json
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOrchestratorIntegration:
    """Integration tests for full orchestrator workflow."""

    @pytest.mark.integration
    def test_template_single_sport(self, tmp_path):
        """Test full workflow with template mode and one sport."""
        repo_root = Path(__file__).parent.parent
        config_path = repo_root / "config.json"
        backup_path = repo_root / "config.json.pytest_backup"

        # Backup existing config if it exists
        if config_path.exists():
            config_path.rename(backup_path)

        try:
            # Create test config
            config = {
                "sports": ["basketball"],
                "timestamp": "2025-11-01T18:00:00Z",
                "session_id": "test_integration_single",
                "retry_enabled": False,
                "generation_mode": "template"
            }

            with open(config_path, "w") as f:
                json.dump(config, f)

            # Run orchestrator
            result = subprocess.run(
                [sys.executable, "orchestrator.py"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check it succeeded
            assert result.returncode == 0, f"Orchestrator failed: {result.stderr}"

            # Check output files exist
            output_dir = repo_root / "output" / "test_integration_single"
            assert output_dir.exists()

        finally:
            # Restore original config
            if config_path.exists():
                config_path.unlink()
            if backup_path.exists():
                backup_path.rename(config_path)

        basketball_dir = output_dir / "basketball"
        assert basketball_dir.exists()
        assert (basketball_dir / "haiku.txt").exists()
        assert (basketball_dir / "sonnet.txt").exists()
        assert (basketball_dir / "metadata.json").exists()

        # Check metadata
        with open(basketball_dir / "metadata.json") as f:
            metadata = json.load(f)

        assert metadata["sport"] == "basketball"
        assert metadata["generation_mode"] == "template"
        assert metadata["haiku_lines"] == 3
        assert metadata["sonnet_lines"] in [14, 16]

        # Check analysis report
        assert (output_dir / "analysis_report.md").exists()

    @pytest.mark.skip(reason="TODO: Fix backup/restore pattern for multiple tests")
    @pytest.mark.integration
    def test_template_multiple_sports(self, tmp_path):
        """Test full workflow with template mode and multiple sports."""
        # Create config
        config = {
            "sports": ["basketball", "soccer", "tennis"],
            "timestamp": "2025-11-01T18:00:00Z",
            "session_id": "test_integration_multi",
            "retry_enabled": False,
            "generation_mode": "template"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Run orchestrator
        result = subprocess.run(
            [sys.executable, "orchestrator.py"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Check it succeeded
        assert result.returncode == 0, f"Orchestrator failed: {result.stderr}"

        # Check all sports generated
        output_dir = Path(__file__).parent.parent / "output" / "test_integration_multi"

        for sport in ["basketball", "soccer", "tennis"]:
            sport_dir = output_dir / sport
            assert sport_dir.exists(), f"{sport} directory not created"
            assert (sport_dir / "haiku.txt").exists()
            assert (sport_dir / "sonnet.txt").exists()
            assert (sport_dir / "metadata.json").exists()

        # Check analysis report includes all sports
        analysis = (output_dir / "analysis_report.md").read_text()
        assert "basketball" in analysis.lower()
        assert "soccer" in analysis.lower()
        assert "tennis" in analysis.lower()

    @pytest.mark.skip(reason="TODO: Fix backup/restore pattern")
    @pytest.mark.integration
    @pytest.mark.requires_api_key
    @pytest.mark.slow
    def test_llm_single_sport(self, tmp_path, api_key):
        """Test full workflow with LLM mode."""
        # Create config
        config = {
            "sports": ["cricket"],
            "timestamp": "2025-11-01T18:00:00Z",
            "session_id": "test_integration_llm",
            "retry_enabled": False,
            "generation_mode": "llm",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Run orchestrator with API key
        env = {
            "PYTHONPATH": str(Path(__file__).parent.parent),
            "TOGETHER_API_KEY": api_key
        }

        result = subprocess.run(
            [sys.executable, "orchestrator.py"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=120  # LLM takes longer
        )

        # Check it succeeded
        assert result.returncode == 0, f"Orchestrator failed: {result.stderr}"

        # Check output files
        output_dir = Path(__file__).parent.parent / "output" / "test_integration_llm"
        cricket_dir = output_dir / "cricket"

        assert (cricket_dir / "haiku.txt").exists()
        assert (cricket_dir / "sonnet.txt").exists()

        # Check metadata shows LLM mode
        with open(cricket_dir / "metadata.json") as f:
            metadata = json.load(f)

        assert metadata["generation_mode"] == "llm"
        assert metadata["llm_model"] == "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

        # Check poem is NOT template (cricket doesn't have a specific template)
        haiku = (cricket_dir / "haiku.txt").read_text()
        assert "Athletes prepare well" not in haiku  # Not default template

    @pytest.mark.skip(reason="TODO: Fix backup/restore pattern")
    @pytest.mark.integration
    def test_session_directory_creation(self, tmp_path):
        """Test that session directories are created correctly."""
        config = {
            "sports": ["basketball"],
            "timestamp": "2025-11-01T18:00:00Z",
            "session_id": "test_session_dir",
            "retry_enabled": False,
            "generation_mode": "template"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Run orchestrator
        result = subprocess.run(
            [sys.executable, "orchestrator.py"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0

        # Check session directory exists
        output_dir = Path(__file__).parent.parent / "output"
        session_dir = output_dir / "test_session_dir"
        assert session_dir.exists()
        assert session_dir.is_dir()

        # Check latest symlink
        latest_link = output_dir / "latest"
        assert latest_link.exists()
        assert latest_link.is_symlink()

    @pytest.mark.integration
    def test_logging_creates_files(self, tmp_path):
        """Test that execution logs are created in session directory."""
        repo_root = Path(__file__).parent.parent
        config_path = repo_root / "config.json"
        backup_path = repo_root / "config.json.pytest_backup"

        # Backup existing config if it exists
        if config_path.exists():
            config_path.rename(backup_path)

        try:
            # Create test config
            config = {
                "sports": ["basketball"],
                "timestamp": "2025-11-01T18:00:00Z",
                "session_id": "test_logging",
                "retry_enabled": False,
                "generation_mode": "template"
            }

            with open(config_path, "w") as f:
                json.dump(config, f)

            # Run orchestrator
            result = subprocess.run(
                [sys.executable, "orchestrator.py"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0

            # Check logs were written to session directory
            session_dir = repo_root / "output" / "test_logging"
            log_file = session_dir / "execution_log.jsonl"
            assert log_file.exists(), f"Execution log not found at {log_file}"

            # Verify log has entries
            with open(log_file) as f:
                entries = f.readlines()
            assert len(entries) > 0, "No log entries written"

            # Check usage log in session directory
            usage_log = session_dir / "usage_log.jsonl"
            assert usage_log.exists(), f"Usage log not found at {usage_log}"

        finally:
            # Restore original config
            if config_path.exists():
                config_path.unlink()
            if backup_path.exists():
                backup_path.rename(config_path)


class TestErrorHandling:
    """Test orchestrator error handling."""

    @pytest.mark.skip(reason="TODO: Fix to use proper config backup/restore")
    @pytest.mark.integration
    def test_missing_config_file(self):
        """Test error when config file doesn't exist."""
        # Remove config.json temporarily
        config_path = Path(__file__).parent.parent / "config.json"
        backup_path = Path(__file__).parent.parent / "config.json.test_backup"

        if config_path.exists():
            config_path.rename(backup_path)

        try:
            result = subprocess.run(
                [sys.executable, "orchestrator.py"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should fail
            assert result.returncode != 0
            assert "Error" in result.stderr or "error" in result.stderr.lower()

        finally:
            # Restore config
            if backup_path.exists():
                backup_path.rename(config_path)

    @pytest.mark.skip(reason="TODO: Fix to use proper config backup/restore")
    @pytest.mark.integration
    def test_llm_mode_without_api_key(self, tmp_path):
        """Test clear error when LLM mode used without API key."""
        config = {
            "sports": ["cricket"],
            "timestamp": "2025-11-01T18:00:00Z",
            "session_id": "test_no_api_key",
            "retry_enabled": False,
            "generation_mode": "llm",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Run without API key in environment
        env = {"PYTHONPATH": str(Path(__file__).parent.parent)}
        # Explicitly unset API keys
        env["TOGETHER_API_KEY"] = ""
        env["HUGGINGFACE_API_TOKEN"] = ""

        result = subprocess.run(
            [sys.executable, "orchestrator.py"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail
        assert result.returncode != 0

        # Check error message is clear
        output = result.stdout + result.stderr
        assert "API" in output or "key" in output.lower()
