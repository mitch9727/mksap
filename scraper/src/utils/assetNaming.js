/**
 * Asset Naming Utilities
 *
 * Extracts meaningful names from figure/table elements on the page
 * and sanitizes them for use as filenames.
 *
 * Strategy (in order of preference):
 * 1. <figcaption> or <caption> text
 * 2. aria-label attribute
 * 3. alt text (figures only)
 * 4. title attribute
 * 5. Fallback: {prefix}_{index}
 *
 * @module assetNaming
 */

/**
 * Extract meaningful name from a figure or table element
 *
 * @param {Locator} element - Playwright locator for the element
 * @param {string} fallbackPrefix - 'figure' or 'table'
 * @param {number} index - Index for fallback naming
 * @returns {Promise<string>} Sanitized filename (without extension)
 */
async function extractAssetName(element, fallbackPrefix, index) {
  try {
    // Strategy 1: Check for figcaption (for figures)
    try {
      const figcaption = element.locator('..').locator('figcaption');
      const text = await figcaption.innerText().catch(() => null);
      if (text && text.trim()) {
        return sanitizeFilename(text.trim());
      }
    } catch (e) {
      // Continue to next strategy
    }

    // Strategy 2: Check for caption (for tables)
    try {
      const caption = element.locator('caption');
      const text = await caption.innerText().catch(() => null);
      if (text && text.trim()) {
        return sanitizeFilename(text.trim());
      }
    } catch (e) {
      // Continue to next strategy
    }

    // Strategy 3: Check for aria-label
    try {
      const ariaLabel = await element.getAttribute('aria-label');
      if (ariaLabel && ariaLabel.trim()) {
        return sanitizeFilename(ariaLabel.trim());
      }
    } catch (e) {
      // Continue to next strategy
    }

    // Strategy 4: Check for alt text (figures only)
    if (fallbackPrefix === 'figure') {
      try {
        const alt = await element.getAttribute('alt');
        if (alt && alt.trim()) {
          return sanitizeFilename(alt.trim());
        }
      } catch (e) {
        // Continue to next strategy
      }
    }

    // Strategy 5: Check for title attribute
    try {
      const title = await element.getAttribute('title');
      if (title && title.trim()) {
        return sanitizeFilename(title.trim());
      }
    } catch (e) {
      // Continue to fallback
    }

    // Fallback: Generic name with index
    return `${fallbackPrefix}_${index}`;
  } catch (error) {
    console.error(`Error extracting asset name: ${error.message}`);
    return `${fallbackPrefix}_${index}`;
  }
}

/**
 * Sanitize a string for use as a filename
 *
 * Rules:
 * - Replace spaces with underscores
 * - Remove special characters (keep alphanumeric, underscores, hyphens)
 * - Truncate to 100 characters max
 * - Lowercase for consistency
 *
 * @param {string} name - Raw name from browser element
 * @returns {string} Sanitized filename (no extension)
 *
 * @example
 * sanitizeFilename("ECG Demonstrating a Type 1 Brugada Pattern")
 * // Returns: "ecg_demonstrating_a_type_1_brugada_pattern"
 *
 * @example
 * sanitizeFilename("Inherited Syndromes Characterized by Sudden Cardiac Death")
 * // Returns: "inherited_syndromes_characterized_by_sudden_cardiac_death"
 */
function sanitizeFilename(name) {
  return name
    // Replace spaces with underscores
    .replace(/\s+/g, '_')
    // Remove special characters (keep alphanumeric, underscore, hyphen)
    .replace(/[^a-zA-Z0-9_-]/g, '')
    // Convert to lowercase for consistency
    .toLowerCase()
    // Remove leading/trailing underscores
    .replace(/^_+|_+$/g, '')
    // Replace multiple consecutive underscores with single
    .replace(/_+/g, '_')
    // Truncate to 100 characters max
    .substring(0, 100);
}

module.exports = {
  extractAssetName,
  sanitizeFilename
};
