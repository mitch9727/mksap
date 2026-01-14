"""
Table processor - Extracts testable statements from clinical tables.

Filters out lab-values tables and processes clinical/educational tables.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from bs4 import BeautifulSoup

from .llm_client import ClaudeClient
from .models import TableStatement

logger = logging.getLogger(__name__)


class TableProcessor:
    """Extract statements from clinical tables in question directories"""

    def __init__(self, client: ClaudeClient, prompt_path: Path):
        """
        Initialize table processor.

        Args:
            client: LLM client for statement extraction
            prompt_path: Path to table_extraction.md prompt template
        """
        self.client = client
        self.prompt_template = self._load_prompt(prompt_path)
        self.last_skipped_count = 0  # Track skipped lab-values tables

    def _load_prompt(self, path: Path) -> str:
        """Load prompt template from file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt template {path}: {e}")
            raise

    def is_lab_values_table(self, html_content: str) -> bool:
        """
        Check if table is a lab-values table (should be skipped).

        Primary check: className contains "lab-values"
        Secondary check: No <thead> element

        Args:
            html_content: Raw HTML content of table file

        Returns:
            True if lab-values table, False if clinical/educational table
        """
        try:
            soup = BeautifulSoup(html_content, "lxml")
            table = soup.find("table")

            if not table:
                logger.warning("No <table> element found in HTML")
                return False

            # Primary check: className attribute
            class_attr = table.get("class", [])
            if isinstance(class_attr, list):
                class_str = " ".join(class_attr)
            else:
                class_str = str(class_attr)

            if "lab-values" in class_str:
                logger.debug(f"Lab-values table detected (className={class_str})")
                return True

            # Secondary check: No thead indicates lab-values table
            has_thead = table.find("thead") is not None
            if not has_thead:
                logger.debug("Lab-values table detected (no <thead>)")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking table type: {e}")
            return False  # Default to processing if unsure

    def parse_table_html(self, html_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse table HTML to extract caption, headers, and rows.

        Args:
            html_path: Path to table HTML file

        Returns:
            Dict with 'caption', 'headers', 'rows', 'filename'
            None if lab-values table or parsing error
        """
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Check if lab-values table (skip if so)
            if self.is_lab_values_table(html_content):
                logger.debug(f"Skipping lab-values table: {html_path.name}")
                self.last_skipped_count += 1
                return None

            soup = BeautifulSoup(html_content, "lxml")
            table = soup.find("table")

            if not table:
                logger.warning(f"No <table> found in {html_path.name}")
                return None

            # Extract caption
            caption_tag = table.find("caption")
            caption = caption_tag.get_text(strip=True) if caption_tag else "No caption"

            # Extract headers (from <thead>)
            headers = []
            thead = table.find("thead")
            if thead:
                header_row = thead.find("tr")
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

            # Extract rows (from <tbody>)
            rows = []
            tbody = table.find("tbody")
            if tbody:
                for tr in tbody.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if cells:  # Skip empty rows
                        rows.append(cells)

            logger.debug(
                f"Parsed {html_path.name}: caption='{caption[:50]}...', "
                f"{len(headers)} headers, {len(rows)} rows"
            )

            return {
                "caption": caption,
                "headers": headers,
                "rows": rows,
                "filename": html_path.name,
            }

        except Exception as e:
            logger.error(f"Failed to parse {html_path}: {e}", exc_info=True)
            return None

    def _format_table_for_llm(self, table_data: Dict[str, Any]) -> str:
        """
        Format parsed table data as structured text for LLM.

        Args:
            table_data: Dict from parse_table_html

        Returns:
            Formatted string representation of table
        """
        lines = []

        # Add headers if present
        if table_data["headers"]:
            header_line = " | ".join(table_data["headers"])
            lines.append(header_line)
            lines.append("-" * len(header_line))  # Separator

        # Add rows
        for row in table_data["rows"]:
            row_line = " | ".join(row)
            lines.append(row_line)

        return "\n".join(lines)

    def _extract_statements_from_table(
        self, table_data: Dict[str, Any]
    ) -> List[TableStatement]:
        """
        Call LLM to extract statements from single table.

        Args:
            table_data: Parsed table data (caption, headers, rows, filename)

        Returns:
            List of TableStatement objects
        """
        try:
            # Format table for LLM
            table_content = self._format_table_for_llm(table_data)

            # Build prompt
            prompt = self.prompt_template.format(
                table_caption=table_data["caption"], table_content=table_content
            )

            # Call LLM
            logger.debug(f"Calling LLM for table: {table_data['filename']}")
            response = self.client.generate(prompt)

            # Parse response
            response_data = json.loads(response)
            statements_data = response_data.get("statements", [])

            # Build TableStatement objects
            table_statements = []
            for stmt in statements_data:
                table_statements.append(
                    TableStatement(
                        statement=stmt["statement"],
                        extra_field=stmt.get("extra_field"),
                        cloze_candidates=[],  # Filled in later by cloze identifier
                        table_source=table_data["filename"],
                    )
                )

            logger.info(
                f"✓ Extracted {len(table_statements)} statements from {table_data['filename']}"
            )
            return table_statements

        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON response for {table_data['filename']}: {e}",
                exc_info=True,
            )
            return []
        except Exception as e:
            logger.error(
                f"Failed to extract statements from {table_data['filename']}: {e}",
                exc_info=True,
            )
            return []

    def extract_statements(self, question_dir: Path) -> List[TableStatement]:
        """
        Extract statements from all clinical tables in question directory.

        Skips lab-values tables automatically.

        Args:
            question_dir: Path to question directory (contains tables/ subfolder)

        Returns:
            Aggregated list of TableStatement objects from all tables
        """
        self.last_skipped_count = 0  # Reset counter
        all_statements = []

        tables_dir = question_dir / "tables"

        # Check if tables directory exists
        if not tables_dir.exists():
            logger.debug(f"No tables directory in {question_dir.name}")
            return []

        # Find all HTML files
        table_files = list(tables_dir.glob("*.html"))
        if not table_files:
            logger.debug(f"No table files found in {tables_dir}")
            return []

        logger.debug(f"Found {len(table_files)} table files in {question_dir.name}")

        # Process each table
        for table_path in sorted(table_files):
            table_data = self.parse_table_html(table_path)

            if table_data is None:
                # Lab-values table or parsing error (already logged)
                continue

            # Extract statements from this table
            statements = self._extract_statements_from_table(table_data)
            all_statements.extend(statements)

        logger.info(
            f"Processed {len(table_files)} tables: {len(all_statements)} statements extracted, "
            f"{self.last_skipped_count} lab-values tables skipped"
        )

        return all_statements
