#!/bin/bash

# Validate 7 processed questions and capture summary

echo "Validating 7 processed questions..."
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

questions=(
    "cvcor25002"
    "cvcor25003"
    "cvmcq24001"
    "enmcq24001"
    "fcmcq24001"
    "gimcq24001"
    "pmmcq24048"
)

total=0
passed=0
failed=0
total_errors=0
total_warnings=0
total_info=0

for q in "${questions[@]}"; do
    echo "Validating $q..."
    result=$("$ROOT_DIR/scripts/python" -m src.main validate --question-id "$q" 2>&1)

    # Count totals
    ((total++))

    # Check if passed or failed
    if echo "$result" | grep -q "Passed: 1"; then
        ((passed++))
        echo "  ✓ PASS"
    else
        ((failed++))
        echo "  ✗ FAIL"

        # Extract issue counts
        errors=$(echo "$result" | grep -oP "Errors: \K\d+" || echo "0")
        warnings=$(echo "$result" | grep -oP "Warnings: \K\d+" || echo "0")
        info=$(echo "$result" | grep -oP "Info: \K\d+" || echo "0")

        ((total_errors += errors))
        ((total_warnings += warnings))
        ((total_info += info))

        echo "    Errors: $errors, Warnings: $warnings, Info: $info"
    fi
    echo ""
done

echo "========================================"
echo "VALIDATION SUMMARY"
echo "========================================"
echo "Total questions: $total"
echo "Passed: $passed ($(echo "scale=1; $passed * 100 / $total" | bc)%)"
echo "Failed: $failed ($(echo "scale=1; $failed * 100 / $total" | bc)%)"
echo ""
echo "Total issues:"
echo "  Errors: $total_errors"
echo "  Warnings: $total_warnings"
echo "  Info: $total_info"
echo "========================================"
