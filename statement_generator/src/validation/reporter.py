"""
Validation report generation utilities.

Generates summary and detailed reports for validation results.
"""

import json
from collections import Counter
from pathlib import Path
from typing import List
from .validator import ValidationResult


def generate_summary_report(results: List[ValidationResult]) -> str:
    """
    Generate summary validation report.

    Args:
        results: List of validation results

    Returns:
        Formatted summary report as string
    """
    if not results:
        return "No questions validated."

    total = len(results)
    passed = len([r for r in results if r.valid])
    failed = len([r for r in results if not r.valid])

    # Count issues by severity
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_info = sum(len(r.info) for r in results)

    # Count issues by category
    category_counts = Counter()
    for result in results:
        for issue in result.errors + result.warnings + result.info:
            category_counts[issue.category] += 1

    # Count top issue types
    issue_type_counts = Counter()
    for result in results:
        for issue in result.errors + result.warnings + result.info:
            issue_type_counts[issue.message] += 1

    # Build report
    lines = []
    lines.append("=" * 70)
    lines.append("VALIDATION SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Questions validated: {total}")
    lines.append(f"Passed: {passed} ({passed/total*100:.1f}%)")
    lines.append(f"Failed: {failed} ({failed/total*100:.1f}%)")
    lines.append("")

    lines.append("Issues by severity:")
    lines.append(f"  - Errors: {total_errors}")
    lines.append(f"  - Warnings: {total_warnings}")
    lines.append(f"  - Info: {total_info}")
    lines.append("")

    lines.append("Issues by category:")
    for category, count in category_counts.most_common():
        lines.append(f"  - {category.capitalize()}: {count}")
    lines.append("")

    lines.append("Top issues:")
    for i, (message, count) in enumerate(issue_type_counts.most_common(10), 1):
        # Truncate long messages
        short_message = message[:60] + "..." if len(message) > 60 else message
        lines.append(f"  {i}. {short_message} ({count} questions)")
    lines.append("")

    if failed > 0:
        lines.append("Failed questions:")
        failed_questions = [r for r in results if not r.valid]
        for result in failed_questions[:20]:  # Show first 20
            error_count = len(result.errors)
            warning_count = len(result.warnings)
            issue_summary = []
            if error_count:
                issue_summary.append(f"{error_count} error{'s' if error_count != 1 else ''}")
            if warning_count:
                issue_summary.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")

            lines.append(f"  - {result.question_id}: {', '.join(issue_summary)}")

        if len(failed_questions) > 20:
            lines.append(f"  ... and {len(failed_questions) - 20} more")

    lines.append("=" * 70)

    return "\n".join(lines)


def generate_detailed_report(results: List[ValidationResult]) -> str:
    """
    Generate detailed validation report with all issues.

    Args:
        results: List of validation results

    Returns:
        Formatted detailed report as string
    """
    if not results:
        return "No questions validated."

    lines = []
    lines.append("=" * 70)
    lines.append("DETAILED VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append("")

    for result in results:
        # Only show questions with issues
        if not result.errors and not result.warnings and not result.info:
            continue

        lines.append(f"Question: {result.question_id}")
        lines.append(f"Status: {'PASSED' if result.valid else 'FAILED'}")
        lines.append(f"Issues: {len(result.errors)} errors, {len(result.warnings)} warnings, {len(result.info)} info")
        lines.append("")

        # Show errors
        if result.errors:
            lines.append("  ERRORS:")
            for issue in result.errors:
                location_str = f" [{issue.location}]" if issue.location else ""
                lines.append(f"    - {issue.message}{location_str}")
            lines.append("")

        # Show warnings
        if result.warnings:
            lines.append("  WARNINGS:")
            for issue in result.warnings:
                location_str = f" [{issue.location}]" if issue.location else ""
                lines.append(f"    - {issue.message}{location_str}")
            lines.append("")

        # Show info
        if result.info:
            lines.append("  INFO:")
            for issue in result.info:
                location_str = f" [{issue.location}]" if issue.location else ""
                lines.append(f"    - {issue.message}{location_str}")
            lines.append("")

        lines.append("-" * 70)
        lines.append("")

    # Add summary at end
    lines.append("")
    lines.append(generate_summary_report(results))

    return "\n".join(lines)


def export_to_json(results: List[ValidationResult], path: Path) -> None:
    """
    Export validation results to JSON file.

    Args:
        results: List of validation results
        path: Output file path
    """
    # Convert to JSON-serializable format
    data = [result.model_dump() for result in results]

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def export_to_csv(results: List[ValidationResult], path: Path) -> None:
    """
    Export validation results to CSV file.

    Args:
        results: List of validation results
        path: Output file path
    """
    import csv

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "question_id",
            "valid",
            "error_count",
            "warning_count",
            "info_count",
            "structure_issues",
            "quality_issues",
            "cloze_issues",
            "hallucination_issues"
        ])

        # Data rows
        for result in results:
            writer.writerow([
                result.question_id,
                result.valid,
                len(result.errors),
                len(result.warnings),
                len(result.info),
                result.stats.get("structure", 0),
                result.stats.get("quality", 0),
                result.stats.get("cloze", 0),
                result.stats.get("hallucination", 0),
            ])
