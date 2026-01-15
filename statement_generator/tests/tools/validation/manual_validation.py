"""
Test script for validation framework.

Tests ambiguity detection, enumeration detection, and overall validation
on baseline and enhanced question outputs.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.validation.validator import StatementValidator, ValidationResult


def print_validation_results(result: ValidationResult, verbose: bool = False):
    """
    Print validation results in a readable format.

    Args:
        result: ValidationResult to print
        verbose: If True, show all issues; if False, show summary only
    """
    print(f"\n{'='*80}")
    print(f"VALIDATION REPORT: {result.question_id}")
    print(f"{'='*80}")

    print(f"\n📊 Summary:")
    print(f"  Valid: {'✅ YES' if result.valid else '❌ NO'}")
    print(f"  Total Issues: {result.stats['total_issues']}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Info: {len(result.info)}")

    print(f"\n📈 Issues by Category:")
    categories = ['structure', 'quality', 'cloze', 'hallucination', 'ambiguity', 'enumeration']
    for cat in categories:
        count = result.stats.get(cat, 0)
        if count > 0:
            print(f"  {cat.capitalize()}: {count}")

    if verbose:
        # Print errors
        if result.errors:
            print(f"\n❌ ERRORS ({len(result.errors)}):")
            for i, issue in enumerate(result.errors, 1):
                print(f"  {i}. [{issue.category}] {issue.message}")
                if issue.location:
                    print(f"     Location: {issue.location}")

        # Print warnings
        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for i, issue in enumerate(result.warnings, 1):
                print(f"  {i}. [{issue.category}] {issue.message}")
                if issue.location:
                    print(f"     Location: {issue.location}")

        # Print info
        if result.info:
            print(f"\nℹ️  INFO ({len(result.info)}):")
            for i, issue in enumerate(result.info, 1):
                print(f"  {i}. [{issue.category}] {issue.message}")
                if issue.location:
                    print(f"     Location: {issue.location}")


def test_baseline_vs_enhanced(baseline_file: str, enhanced_file: str):
    """
    Compare validation results between baseline and enhanced outputs.

    Args:
        baseline_file: Path to baseline JSON
        enhanced_file: Path to enhanced JSON
    """
    validator = StatementValidator()

    print("\n" + "="*80)
    print("BASELINE VS ENHANCED VALIDATION COMPARISON")
    print("="*80)

    # Load baseline
    with open(baseline_file) as f:
        baseline_data = json.load(f)

    # Load enhanced
    with open(enhanced_file) as f:
        enhanced_data = json.load(f)

    # Validate both
    print("\n🔍 Validating BASELINE...")
    baseline_result = validator.validate_question(baseline_data)
    print_validation_results(baseline_result, verbose=False)

    print("\n\n🔍 Validating ENHANCED...")
    enhanced_result = validator.validate_question(enhanced_data)
    print_validation_results(enhanced_result, verbose=False)

    # Comparison
    print(f"\n{'='*80}")
    print("📊 IMPROVEMENT ANALYSIS")
    print(f"{'='*80}")

    print(f"\nIssue Count Comparison:")
    print(f"  Total Issues: {baseline_result.stats['total_issues']} → {enhanced_result.stats['total_issues']} "
          f"({enhanced_result.stats['total_issues'] - baseline_result.stats['total_issues']:+d})")

    print(f"\n  By Category:")
    categories = ['quality', 'cloze', 'hallucination', 'ambiguity', 'enumeration']
    for cat in categories:
        base_count = baseline_result.stats.get(cat, 0)
        enh_count = enhanced_result.stats.get(cat, 0)
        if base_count > 0 or enh_count > 0:
            change = enh_count - base_count
            print(f"    {cat.capitalize()}: {base_count} → {enh_count} ({change:+d})")

    # Ambiguity improvements
    baseline_ambiguity = [w for w in baseline_result.warnings if w.category == "ambiguity"]
    enhanced_ambiguity = [w for w in enhanced_result.warnings if w.category == "ambiguity"]

    if baseline_ambiguity or enhanced_ambiguity:
        print(f"\n🎯 Ambiguity Detection:")
        print(f"  Baseline: {len(baseline_ambiguity)} ambiguous statements")
        print(f"  Enhanced: {len(enhanced_ambiguity)} ambiguous statements")
        if len(enhanced_ambiguity) < len(baseline_ambiguity):
            print(f"  ✅ IMPROVEMENT: {len(baseline_ambiguity) - len(enhanced_ambiguity)} fewer ambiguities")
        elif len(enhanced_ambiguity) > len(baseline_ambiguity):
            print(f"  ⚠️  REGRESSION: {len(enhanced_ambiguity) - len(baseline_ambiguity)} more ambiguities")


def test_single_question(question_file: str, verbose: bool = True):
    """
    Test validation on a single question file.

    Args:
        question_file: Path to question JSON
        verbose: Show detailed issues
    """
    validator = StatementValidator()

    with open(question_file) as f:
        data = json.load(f)

    result = validator.validate_question(data)
    print_validation_results(result, verbose=verbose)

    return result


def main():
    """Main test execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Test validation framework")
    parser.add_argument('--baseline', help='Path to baseline JSON file')
    parser.add_argument('--enhanced', help='Path to enhanced JSON file')
    parser.add_argument('--question', help='Path to single question JSON')
    parser.add_argument('--verbose', action='store_true', help='Show detailed issues')

    args = parser.parse_args()

    if args.baseline and args.enhanced:
        test_baseline_vs_enhanced(args.baseline, args.enhanced)
    elif args.question:
        test_single_question(args.question, verbose=args.verbose)
    else:
        # Default: test pmmcq24048 baseline vs enhanced
        print("Testing pmmcq24048 (baseline vs enhanced)...")
        baseline_path = ROOT_DIR / "artifacts" / "runs" / "baseline" / "baseline_run1.json"
        data_root = os.getenv("MKSAP_DATA_ROOT")
        if data_root:
            data_root_path = Path(data_root)
            if not data_root_path.is_absolute():
                data_root_path = ROOT_DIR.parent / data_root_path
        else:
            data_root_path = ROOT_DIR.parent / "test_mksap_data"

        enhanced_path = data_root_path / "pm" / "pmmcq24048" / "pmmcq24048.json"

        if Path(baseline_path).exists() and Path(enhanced_path).exists():
            test_baseline_vs_enhanced(baseline_path, enhanced_path)
        else:
            print("Error: Default test files not found.")
            print("Usage:")
            print("  ./scripts/python statement_generator/tools/validation/test_validation.py --baseline baseline.json --enhanced enhanced.json")
            print("  ./scripts/python statement_generator/tools/validation/test_validation.py --question question.json")


if __name__ == "__main__":
    main()
