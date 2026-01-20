#!/bin/bash

# Documentation Validation Script
# Purpose: Automated health checks for documentation integrity
# Exit codes: 0 = all checks passed, 1 = one or more checks failed

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=3
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
EXTRACTOR_DOCS_DIR="$PROJECT_ROOT/extractor/docs"
STATEMENT_DOCS_DIR="$PROJECT_ROOT/statement_generator/docs"
ANKING_DOCS_DIR="$PROJECT_ROOT/anking_analysis/docs"
ARTIFACTS_DIR="$PROJECT_ROOT/statement_generator/artifacts"

DOC_DIRS=(
    "$DOCS_DIR"
    "$EXTRACTOR_DOCS_DIR"
    "$STATEMENT_DOCS_DIR"
    "$ANKING_DOCS_DIR"
)

echo -e "${BLUE}=== Documentation Validation Report ===${NC}\n"

###############################################################################
# Check 1: Broken Internal Links
###############################################################################
echo -e "${BLUE}[Check 1] Broken Internal Links${NC}"

BROKEN_LINKS=0
TOTAL_LINKS=0

# Find all markdown files in docs/
while IFS= read -r file; do
    # Extract markdown links [text](path.md)
    while IFS= read -r link; do
        TOTAL_LINKS=$((TOTAL_LINKS + 1))

        # Extract the path from the link
        LINK_PATH=$(echo "$link" | sed 's/.*(\(.*\))/\1/')

        # Skip external links (http/https)
        if [[ "$LINK_PATH" =~ ^https?:// ]]; then
            continue
        fi

        # Skip anchor-only links (#section)
        if [[ "$LINK_PATH" =~ ^# ]]; then
            continue
        fi

        # Remove anchor from path if present
        LINK_PATH_NO_ANCHOR=$(echo "$LINK_PATH" | sed 's/#.*//')

        # Construct absolute path
        FILE_DIR=$(dirname "$file")
        if [[ "$LINK_PATH_NO_ANCHOR" = /* ]]; then
            # Absolute path from project root
            TARGET_FILE="$PROJECT_ROOT$LINK_PATH_NO_ANCHOR"
        else
            # Relative path from current file
            TARGET_FILE="$FILE_DIR/$LINK_PATH_NO_ANCHOR"
        fi

        # Normalize path
        TARGET_FILE=$(realpath -m "$TARGET_FILE" 2>/dev/null || echo "$TARGET_FILE")

        # Check if target file exists
        if [ ! -f "$TARGET_FILE" ]; then
            echo -e "  ${RED}✗${NC} Broken link in ${file#$PROJECT_ROOT/}: $LINK_PATH"
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
        fi
    done < <(grep -o '\[^]]*]([^)]*.md[^)]*)' "$file" 2>/dev/null || true)
done < <(find "${DOC_DIRS[@]}" -name "*.md" -type f 2>/dev/null)

if [ "$BROKEN_LINKS" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No broken links found ($TOTAL_LINKS links checked)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗${NC} Found $BROKEN_LINKS broken link(s) out of $TOTAL_LINKS total"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

###############################################################################
# Check 2: Orphaned Documents
###############################################################################
echo -e "${BLUE}[Check 2] Orphaned Documents${NC}"

ORPHANED_DOCS=0

collect_index_refs() {
    local index_file="$1"
    local base_dir="$2"
    local refs=""
    local index_dir
    index_dir=$(dirname "$index_file")

    while IFS= read -r link; do
        local link_path
        link_path=$(echo "$link" | sed 's/.*(\(.*\))/\1/')

        if [[ "$link_path" =~ ^https?:// ]]; then
            continue
        fi

        if [[ "$link_path" =~ ^# ]]; then
            continue
        fi

        local link_path_no_anchor
        link_path_no_anchor=$(echo "$link_path" | sed 's/#.*//')

        local target_file
        if [[ "$link_path_no_anchor" = /* ]]; then
            target_file="$PROJECT_ROOT$link_path_no_anchor"
        else
            target_file="$index_dir/$link_path_no_anchor"
        fi

        target_file=$(realpath -m "$target_file" 2>/dev/null || echo "$target_file")

        if [[ "$target_file" == "$base_dir"* ]]; then
            refs+="$target_file"$'\n'
        fi
    done < <(grep -o '\[[^]]*]([^)]*\.md[^)]*)' "$index_file" 2>/dev/null || true)

    echo "$refs" | sort -u
}

for base_dir in "${DOC_DIRS[@]}"; do
    index_file="$base_dir/INDEX.md"
    if [ ! -f "$index_file" ]; then
        echo -e "  ${YELLOW}⚠${NC}  Missing index: ${index_file#$PROJECT_ROOT/} (skipping orphan check)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        continue
    fi

    all_docs=$(find "$base_dir" -name "*.md" -type f ! -name "INDEX.md" | sort)
    referenced_docs=$(collect_index_refs "$index_file" "$base_dir")

    while IFS= read -r doc_file; do
        if [ -z "$doc_file" ]; then
            continue
        fi

        if ! echo "$referenced_docs" | grep -Fxq "$doc_file"; then
            echo -e "  ${RED}✗${NC} Orphaned document: ${doc_file#$PROJECT_ROOT/}"
            ORPHANED_DOCS=$((ORPHANED_DOCS + 1))
        fi
    done <<< "$all_docs"
done

if [ "$ORPHANED_DOCS" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All documents are linked from INDEX.md"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗${NC} Found $ORPHANED_DOCS orphaned document(s)"
    echo -e "  ${YELLOW}→${NC} These documents should be linked from their INDEX.md or moved to artifacts/"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

###############################################################################
# Check 3: Stale Artifacts (warnings only)
###############################################################################
echo -e "${BLUE}[Check 3] Stale Artifacts (warnings)${NC}"

STALE_FILES=0

# Check if artifacts directory exists
if [ -d "$ARTIFACTS_DIR" ]; then
    # Find files older than 30 days
    while IFS= read -r stale_file; do
        # Get file age in days
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            FILE_AGE=$(( ($(date +%s) - $(stat -f %m "$stale_file")) / 86400 ))
        else
            # Linux
            FILE_AGE=$(( ($(date +%s) - $(stat -c %Y "$stale_file")) / 86400 ))
        fi

        REL_PATH="${stale_file#$PROJECT_ROOT/}"
        echo -e "  ${YELLOW}⚠${NC}  $REL_PATH ($FILE_AGE days old)"
        STALE_FILES=$((STALE_FILES + 1))
    done < <(find "$ARTIFACTS_DIR" -type f -mtime +30 2>/dev/null || true)

    if [ "$STALE_FILES" -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} No stale artifacts found (all files < 30 days old)"
    else
        echo -e "  ${YELLOW}⚠${NC}  Found $STALE_FILES file(s) older than 30 days"
        echo -e "  ${YELLOW}→${NC} Review these files for cleanup or promotion to permanent docs"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    fi
else
    echo -e "  ${YELLOW}⚠${NC}  Artifacts directory not found: $ARTIFACTS_DIR"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

echo ""

###############################################################################
# Summary
###############################################################################
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}✓ Passed:${NC} $PASSED_CHECKS"
echo -e "${RED}✗ Failed:${NC} $FAILED_CHECKS"
echo -e "${YELLOW}⚠ Warnings:${NC} $WARNING_CHECKS"
echo ""

# Exit with appropriate code
if [ "$FAILED_CHECKS" -gt 0 ]; then
    echo -e "${RED}Exit code: 1 (failures detected)${NC}"
    exit 1
else
    echo -e "${GREEN}Exit code: 0 (all checks passed)${NC}"
    exit 0
fi
