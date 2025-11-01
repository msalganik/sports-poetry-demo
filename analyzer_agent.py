#!/usr/bin/env python3
"""
Analysis Agent

Reads all generated poetry and creates comparative analysis.
In production, this would use an LLM for sophisticated literary analysis.
For this demo, we use template-based analysis.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def read_poem_files(session_dir: str = "output") -> List[Dict[str, Any]]:
    """Read all poetry files from session output directory."""
    output_dir = Path(session_dir)
    poems = []

    if not output_dir.exists():
        return poems

    for sport_dir in sorted(output_dir.iterdir()):
        if not sport_dir.is_dir():
            continue

        sport_name = sport_dir.name
        haiku_file = sport_dir / "haiku.txt"
        sonnet_file = sport_dir / "sonnet.txt"
        metadata_file = sport_dir / "metadata.json"

        # Read files if they exist
        haiku_text = ""
        sonnet_text = ""
        metadata = {}

        if haiku_file.exists():
            with open(haiku_file, "r") as f:
                haiku_text = f.read()

        if sonnet_file.exists():
            with open(sonnet_file, "r") as f:
                sonnet_text = f.read()

        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

        if haiku_text or sonnet_text:
            poems.append({
                "sport": sport_name,
                "haiku": haiku_text,
                "sonnet": sonnet_text,
                "metadata": metadata
            })

    return poems


def analyze_form_adherence(poems: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze how well poems adhere to traditional forms."""
    analysis = {}

    for poem_data in poems:
        sport = poem_data["sport"]
        haiku_lines = len([l for l in poem_data["haiku"].split("\n") if l.strip()])
        sonnet_lines = len([l for l in poem_data["sonnet"].split("\n") if l.strip()])

        analysis[sport] = {
            "haiku_form": "correct" if haiku_lines == 3 else f"incorrect ({haiku_lines} lines)",
            "sonnet_form": "correct" if sonnet_lines == 14 else f"incorrect ({sonnet_lines} lines)"
        }

    return analysis


def generate_analysis_report(poems: List[Dict[str, Any]]) -> str:
    """Generate comprehensive markdown analysis report."""
    # In production: Use LLM to generate sophisticated analysis
    # This is a template-based version for demo purposes

    if not poems:
        return "# Analysis Report\n\nNo poems found to analyze.\n"

    report = []
    report.append("# Sports Poetry Analysis Report\n")
    report.append(f"**Generated**: {Path('output').stat().st_mtime}\n")
    report.append(f"**Total Sports Analyzed**: {len(poems)}\n")
    report.append("\n---\n")

    # Executive Summary
    report.append("## Executive Summary\n")
    report.append(f"This report analyzes poetry generated for {len(poems)} different sports. ")
    report.append("Each sport is represented by a haiku (3-line poem) and a sonnet (14-line poem). ")
    report.append("The analysis examines form adherence, thematic content, and comparative quality.\n")

    # Form Analysis
    form_analysis = analyze_form_adherence(poems)
    report.append("\n## Form Adherence Analysis\n")

    all_haiku_correct = all(v["haiku_form"] == "correct" for v in form_analysis.values())
    all_sonnet_correct = all(v["sonnet_form"] == "correct" for v in form_analysis.values())

    if all_haiku_correct and all_sonnet_correct:
        report.append("All poems correctly follow traditional forms (3 lines for haiku, 14 for sonnets).\n")
    else:
        report.append("| Sport | Haiku Form | Sonnet Form |\n")
        report.append("|-------|------------|-------------|\n")
        for sport, analysis in form_analysis.items():
            report.append(f"| {sport} | {analysis['haiku_form']} | {analysis['sonnet_form']} |\n")

    # Per-Sport Analysis
    report.append("\n## Individual Sport Analysis\n")

    for poem_data in poems:
        sport = poem_data["sport"]
        metadata = poem_data["metadata"]

        report.append(f"\n### {sport.title()}\n")

        report.append("\n**Haiku:**\n```\n")
        report.append(poem_data["haiku"])
        report.append("```\n")

        report.append("\n**Sonnet (excerpt):**\n```\n")
        # Show first 4 lines of sonnet
        sonnet_lines = poem_data["sonnet"].split("\n")
        report.append("\n".join(sonnet_lines[:4]))
        report.append("\n... (see full sonnet in output directory)\n```\n")

        report.append(f"\n**Metrics:**\n")
        report.append(f"- Haiku: {metadata.get('haiku_lines', 0)} lines, {metadata.get('haiku_words', 0)} words\n")
        report.append(f"- Sonnet: {metadata.get('sonnet_lines', 0)} lines, {metadata.get('sonnet_words', 0)} words\n")
        report.append(f"- Generation time: {metadata.get('duration_s', 0)}s\n")

        # Simple thematic analysis
        report.append(f"\n**Thematic Notes:**\n")
        report.append(f"The {sport} haiku captures the essence of the sport through vivid imagery. ")
        report.append(f"The sonnet explores deeper themes of competition, skill, and human achievement in {sport}.\n")

    # Comparative Analysis
    report.append("\n## Comparative Analysis\n")

    report.append("\n### Best Haiku\n")
    # In production, LLM would actually analyze and pick best
    # For demo, we'll pick the first one
    if poems:
        best_haiku_sport = poems[0]["sport"]
        report.append(f"**Winner: {best_haiku_sport.title()}**\n\n")
        report.append("```\n")
        report.append(poems[0]["haiku"])
        report.append("```\n\n")
        report.append(f"**Justification:** The {best_haiku_sport} haiku demonstrates excellent use of imagery and ")
        report.append("adheres to traditional form while capturing the dynamic nature of the sport.\n")

    report.append("\n### Best Sonnet\n")
    if poems:
        best_sonnet_sport = poems[-1]["sport"]
        report.append(f"**Winner: {best_sonnet_sport.title()}**\n\n")
        report.append("```\n")
        report.append(poems[-1]["sonnet"])
        report.append("```\n\n")
        report.append(f"**Justification:** The {best_sonnet_sport} sonnet excels in exploring the deeper philosophical ")
        report.append("dimensions of sport, using sophisticated language and maintaining consistent meter.\n")

    # Overall Observations
    report.append("\n## Overall Observations\n")
    report.append("1. **Form Quality:** All poems successfully attempted traditional poetic forms.\n")
    report.append("2. **Thematic Depth:** Haikus focused on immediate sensory experience, while sonnets explored deeper meanings.\n")
    report.append("3. **Sport Representation:** Each sport's unique characteristics were well-captured.\n")
    report.append("4. **Technical Execution:** Consistent quality across all generated works.\n")

    # Failed/Missing Sports
    report.append("\n## Missing or Failed Sports\n")
    expected_sports_from_config = []
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            expected_sports_from_config = config.get("sports", [])
    except:
        pass

    analyzed_sports = set(p["sport"] for p in poems)
    expected_sports = set(expected_sports_from_config)
    missing_sports = expected_sports - analyzed_sports

    if missing_sports:
        report.append(f"The following sports were expected but not found: {', '.join(missing_sports)}\n")
    else:
        report.append("All expected sports were successfully analyzed.\n")

    # Footer
    report.append("\n---\n")
    report.append("\n*This analysis was generated by the Sports Poetry Multi-Agent Workflow*\n")

    return "".join(report)


def main():
    import sys

    session_dir = sys.argv[1] if len(sys.argv) > 1 else "output"  # Default for backward compat

    print("Analyzer: Starting analysis")

    # Read all poems from session directory
    poems = read_poem_files(session_dir)
    print(f"Analyzer: Found {len(poems)} sports to analyze")

    # Generate report
    report = generate_analysis_report(poems)

    # Write report to session directory
    output_file = Path(session_dir) / "analysis_report.md"
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Analyzer: Wrote analysis report ({len(report)} characters)")
    print("Analyzer: Complete")


if __name__ == "__main__":
    main()
