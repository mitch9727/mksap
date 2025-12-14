/**
 * Link Validation Module
 *
 * Checks all links in documentation for validity,
 * detects broken references, and suggests fixes.
 */

const fs = require('fs');
const path = require('path');

/**
 * Check all links in documentation
 * @param {Object} options - Validation options
 * @param {string} options.scope - Scope to check (default: 'docs/')
 * @param {boolean} options.verbose - Detailed output
 * @returns {Promise<Object>} Link validation results
 */
async function checkLinks(options = {}) {
  const {
    scope = 'docs/',
    verbose = false,
    checkExternal = false
  } = options;

  const results = {
    scope,
    checked: 0,
    valid: 0,
    broken: 0,
    external: 0,
    brokenLinks: [],
    warnings: []
  };

  try {
    const projectRoot = process.cwd();
    const targetPath = path.join(projectRoot, scope);

    if (!fs.existsSync(targetPath)) {
      return { ...results, error: `Scope path not found: ${scope}` };
    }

    // Collect all markdown files
    const mdFiles = collectMarkdownFiles(targetPath);

    if (verbose) {
      console.log(`Found ${mdFiles.length} markdown files`);
    }

    // Check links in each file
    for (const filePath of mdFiles) {
      const content = fs.readFileSync(filePath, 'utf8');
      const relFilePath = path.relative(projectRoot, filePath);

      // Find all markdown links
      const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
      let match;

      while ((match = linkRegex.exec(content)) !== null) {
        results.checked++;
        const linkText = match[1];
        const linkTarget = match[2];
        const lineNumber = content.substring(0, match.index).split('\n').length;

        // Skip anchor-only links
        if (linkTarget.startsWith('#')) {
          results.valid++;
          continue;
        }

        // Check if external
        if (linkTarget.startsWith('http://') || linkTarget.startsWith('https://')) {
          results.external++;
          if (checkExternal) {
            // Would do HTTP check here
            results.valid++;
          }
          continue;
        }

        // Resolve relative path
        const resolvedPath = resolvePath(filePath, linkTarget);

        if (fs.existsSync(resolvedPath)) {
          results.valid++;
        } else {
          results.broken++;
          results.brokenLinks.push({
            file: relFilePath,
            line: lineNumber,
            linkText,
            linkTarget,
            issue: `File not found: ${resolvedPath}`,
            suggestion: suggestFix(filePath, linkTarget, projectRoot)
          });
        }
      }
    }

    return results;
  } catch (error) {
    return { ...results, error: error.message };
  }
}

/**
 * Collect all markdown files in directory
 */
function collectMarkdownFiles(dirPath) {
  const files = [];

  const collect = (dir) => {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        // Skip common exclusions
        if (['.git', 'node_modules', '.Claude', 'scraper/lib'].includes(entry.name)) {
          continue;
        }

        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          collect(fullPath);
        } else if (entry.name.endsWith('.md')) {
          files.push(fullPath);
        }
      }
    } catch (e) {
      // Ignore permission errors
    }
  };

  collect(dirPath);
  return files;
}

/**
 * Resolve relative path
 */
function resolvePath(sourceFile, linkTarget) {
  // Parse link target (handle anchors)
  const [filePart] = linkTarget.split('#');

  if (!filePart) {
    // Just an anchor, reference is to same file
    return sourceFile;
  }

  // Resolve relative to source file directory
  const sourceDir = path.dirname(sourceFile);
  const absolutePath = path.resolve(sourceDir, filePart);

  return absolutePath;
}

/**
 * Suggest fix for broken link
 */
function suggestFix(sourceFile, linkTarget, projectRoot) {
  const sourceDir = path.dirname(sourceFile);
  const filePart = linkTarget.split('#')[0];

  // Try to find similar file
  const fileName = path.basename(filePart);
  const similarFiles = findSimilarFiles(projectRoot, fileName);

  if (similarFiles.length > 0) {
    const suggestion = similarFiles[0];
    const relativePath = path.relative(sourceDir, suggestion);

    return `Try: [${path.basename(suggestion)}](${relativePath})`;
  }

  return 'File may have been moved or deleted';
}

/**
 * Find files with similar names
 */
function findSimilarFiles(dirPath, fileName, maxResults = 3) {
  const results = [];
  const searchName = fileName.toLowerCase();

  const search = (dir) => {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          search(fullPath);
        } else if (entry.name.toLowerCase().includes(searchName)) {
          results.push(fullPath);
          if (results.length >= maxResults) return;
        }
      }
    } catch (e) {
      // Ignore
    }
  };

  search(dirPath);
  return results;
}

module.exports = checkLinks;
