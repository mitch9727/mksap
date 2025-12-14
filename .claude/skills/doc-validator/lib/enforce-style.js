/**
 * Style Enforcement Module
 *
 * Enforces documentation standards including heading structure,
 * formatting consistency, and required sections.
 */

const fs = require('fs');
const path = require('path');

/**
 * Enforce documentation style standards
 * @param {Object} options - Style options
 * @param {string} options.standardsFile - Path to standards JSON file
 * @param {boolean} options.verbose - Detailed output
 * @returns {Promise<Array>} Array of style violations
 */
async function enforceStyle(options = {}) {
  const {
    standardsFile = '.claude/doc-standards.json',
    verbose = false
  } = options;

  const violations = [];

  try {
    // Load standards
    let standards = {};
    if (fs.existsSync(standardsFile)) {
      const content = fs.readFileSync(standardsFile, 'utf8');
      standards = JSON.parse(content);
    }

    // Get default standards if not provided
    const defaultStandards = getDefaultStandards();
    standards = { ...defaultStandards, ...standards };

    // Check all markdown files in docs/
    const docsPath = 'docs';
    if (fs.existsSync(docsPath)) {
      const mdFiles = collectMarkdownFiles(docsPath);

      for (const filePath of mdFiles) {
        const content = fs.readFileSync(filePath, 'utf8');
        const fileViolations = checkFileStyle(filePath, content, standards, verbose);
        violations.push(...fileViolations);
      }
    }

    return violations;
  } catch (error) {
    return [{
      type: 'error',
      severity: 'error',
      file: 'unknown',
      issue: error.message
    }];
  }
}

/**
 * Check style of a single file
 */
function checkFileStyle(filePath, content, standards, verbose) {
  const violations = [];
  const lines = content.split('\n');

  // Check heading structure
  let headingLevel = 0;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const headingMatch = line.match(/^(#+)\s+(.+)/);

    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];

      // Check heading level progression
      if (level > headingLevel + 1) {
        violations.push({
          type: 'heading-level',
          severity: 'warning',
          file: filePath,
          line: i + 1,
          issue: `Heading level jumped from H${headingLevel} to H${level}`,
          suggestion: `Use H${headingLevel + 1} instead`
        });
      }

      // Check heading capitalization
      if (standards.formatting?.headings?.capitalization === 'Title Case') {
        const words = text.split(' ');
        const isTitleCase = words.every(w => /^[A-Z]/.test(w) || w.length < 2);

        if (!isTitleCase) {
          violations.push({
            type: 'heading-capitalization',
            severity: 'info',
            file: filePath,
            line: i + 1,
            issue: 'Heading should use Title Case',
            current: text,
            suggestion: toTitleCase(text)
          });
        }
      }

      headingLevel = level;
    }
  }

  // Check for required sections based on file type
  const fileName = path.basename(filePath);
  const docType = determineDocType(fileName, filePath);
  const requiredSections = standards.fileTypes?.[docType]?.required || [];

  for (const section of requiredSections) {
    const hasSection = content.includes(`## ${section}`) || content.includes(`# ${section}`);
    if (!hasSection) {
      violations.push({
        type: 'missing-section',
        severity: 'error',
        file: filePath,
        issue: `Missing required section: "${section}"`,
        suggestion: `Add "## ${section}" section`
      });
    }
  }

  // Check line length
  const maxLineLength = standards.content?.maxLineLength || 120;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].length > maxLineLength) {
      violations.push({
        type: 'line-length',
        severity: 'info',
        file: filePath,
        line: i + 1,
        issue: `Line exceeds ${maxLineLength} characters`,
        length: lines[i].length
      });
    }
  }

  // Check for proper spacing between sections
  const blankLineViolations = checkBlankLineSpacing(lines, filePath);
  violations.push(...blankLineViolations);

  return violations;
}

/**
 * Check blank line spacing between sections
 */
function checkBlankLineSpacing(lines, filePath) {
  const violations = [];

  for (let i = 1; i < lines.length - 1; i++) {
    const prevLine = lines[i - 1];
    const currLine = lines[i];
    const nextLine = lines[i + 1];

    // Check spacing after headings
    if (prevLine.match(/^#+\s+/) && currLine !== '' && nextLine !== '') {
      violations.push({
        type: 'spacing',
        severity: 'info',
        file: filePath,
        line: i,
        issue: 'Should have blank line after heading',
        suggestion: 'Add blank line after heading'
      });
    }
  }

  return violations;
}

/**
 * Determine document type
 */
function determineDocType(fileName, filePath) {
  const lower = fileName.toLowerCase();

  if (filePath.includes('.claude/commands')) return 'commands';
  if (filePath.includes('.claude/skills')) return 'skills';
  if (lower.includes('readme')) return 'documentation';
  if (lower.includes('spec') || lower.includes('technical')) return 'documentation';

  return 'documentation';
}

/**
 * Convert text to Title Case
 */
function toTitleCase(text) {
  return text
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Collect all markdown files
 */
function collectMarkdownFiles(dirPath) {
  const files = [];

  const collect = (dir) => {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          collect(fullPath);
        } else if (entry.name.endsWith('.md')) {
          files.push(fullPath);
        }
      }
    } catch (e) {
      // Ignore
    }
  };

  collect(dirPath);
  return files;
}

/**
 * Get default documentation standards
 */
function getDefaultStandards() {
  return {
    structure: {
      requireHeadings: true,
      requireTableOfContents: false,
      maxHeadingDepth: 4,
      requireBlankLinesBetween: true
    },
    links: {
      checkInternal: true,
      checkExternal: false,
      preferRelative: true
    },
    content: {
      requireLastUpdated: false,
      requireAuthor: false,
      maxLineLength: 120,
      preferMarkdownSyntax: true
    },
    formatting: {
      headings: {
        style: 'ATX',
        capitalization: 'Title Case'
      },
      links: {
        style: '[Text](path)',
        reference: 'Avoid reference-style links'
      }
    }
  };
}

module.exports = enforceStyle;
