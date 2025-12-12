/**
 * JSON Schema Definition for MKSAP Questions
 *
 * Defines expected structure, required fields, optional fields,
 * and validation rules for extracted question data.
 *
 * Used by DataQualityValidator Skill to verify extraction completeness.
 *
 * @module schema
 */

module.exports = {
  /**
   * Required fields (must be present and non-empty)
   */
  required: [
    'ID',
    'Reference',
    'Last Updated',
    'Educational Objective',
    'Care type',
    'Answer and Critique',
    'Key Point'
  ],

  /**
   * Optional fields (may be empty or missing)
   */
  optional: [
    'Figures',
    'Tables',
    'Videos',
    'Related Text'
  ],

  /**
   * Field validation rules
   */
  validation: {
    'ID': {
      pattern: /^[A-Z]{2,6}MCQ\d{5}$/,
      message: 'ID must match pattern: {System}MCQ{5 digits} (e.g., CVMCQ24042)',
      examples: ['CVMCQ24042', 'ENMCQ24001', 'FCCSMCQ24010']
    },

    'Reference': {
      minLength: 10,
      message: 'Reference must be at least 10 characters',
      pattern: /PMID:|doi:|ISBN/i, // Should contain citation identifier
      warning: 'Reference should contain PMID, DOI, or ISBN'
    },

    'Last Updated': {
      pattern: /^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$/,
      message: 'Last Updated must be in format: "Month YYYY" (e.g., "January 2025")',
      examples: ['January 2025', 'June 2024']
    },

    'Educational Objective': {
      minLength: 10,
      message: 'Educational Objective must be at least 10 characters',
      warning: 'Educational Objective should be a complete sentence or phrase'
    },

    'Care type': {
      type: 'array',
      minLength: 1,
      message: 'Care type must be a non-empty array',
      validValues: [
        'Ambulatory Care',
        'Hospital Care',
        'Critical Care',
        'Emergency Care',
        'Palliative Care',
        'Preventive Care'
      ],
      warning: 'Care type contains unexpected value'
    },

    'Answer and Critique': {
      minLength: 50,
      message: 'Answer and Critique must be at least 50 characters',
      warning: 'Answer and Critique seems unusually short - verify extraction'
    },

    'Key Point': {
      type: 'array',
      minLength: 1,
      message: 'Key Point must be a non-empty array',
      itemMinLength: 10,
      warning: 'Key Point items should be complete sentences'
    },

    'Figures': {
      type: 'array',
      optional: true,
      itemSchema: {
        path: { required: true, pattern: /^\.\/.*\.(png|jpg|jpeg|gif|svg)$/i },
        alt: { required: false },
        caption: { required: false }
      }
    },

    'Tables': {
      type: 'array',
      optional: true,
      itemSchema: {
        path: { required: true, pattern: /^\.\/.*\.html$/i },
        html: { required: false }
      }
    },

    'Videos': {
      type: 'array',
      optional: true,
      itemSchema: {
        title: { required: true },
        url: { required: true, pattern: /^https?:\/\// }
      }
    },

    'Related Text': {
      optional: true,
      minLength: 10,
      message: 'Related Text should be at least 10 characters if present'
    }
  },

  /**
   * Semantic validation checks
   * These require AI analysis to verify
   */
  semanticChecks: {
    referencePresent: {
      description: 'Reference field contains valid citation',
      check: 'Contains PMID, DOI, or ISBN identifier'
    },

    educationalObjectiveMakesSense: {
      description: 'Educational Objective is coherent and medically relevant',
      check: 'Is a complete, meaningful medical learning objective'
    },

    answerAndCritiqueIsComplete: {
      description: 'Answer and Critique appears to be complete explanation',
      check: 'Contains medical reasoning and does not end abruptly'
    },

    keyPointsAreAtomic: {
      description: 'Key Points are atomic, testable facts',
      check: 'Each Key Point is a single, standalone fact'
    },

    figuresMatchedToMentions: {
      description: 'Figures referenced in text are present in Figures array',
      check: 'If text mentions "Figure 1", it should exist in Figures array'
    },

    tablesMatchedToMentions: {
      description: 'Tables referenced in text are present in Tables array',
      check: 'If text mentions "Table 1", it should exist in Tables array'
    }
  },

  /**
   * Expected data types
   */
  types: {
    'ID': 'string',
    'Reference': 'string',
    'Last Updated': 'string',
    'Educational Objective': 'string',
    'Care type': 'array',
    'Answer and Critique': 'string',
    'Key Point': 'array',
    'Figures': 'array',
    'Tables': 'array',
    'Videos': 'array',
    'Related Text': 'string'
  },

  /**
   * Completeness thresholds
   */
  completeness: {
    minimal: 0.7, // 70% of required fields present
    acceptable: 0.9, // 90% of required fields present
    perfect: 1.0 // 100% of required fields present
  },

  /**
   * System folder validation
   * Maps system codes to expected folder names
   */
  systemFolders: {
    'cv': 'Cardiovascular',
    'en': 'Endocrinology',
    'fccs': 'Foundations',
    'gihp': 'Gastroenterology',
    'hm': 'Hematology',
    'id': 'Infectious_Disease',
    'dmin': 'Dermatology',
    'np': 'Nephrology',
    'nr': 'Neurology',
    'on': 'Oncology',
    'pmcc': 'Pulmonary',
    'rm': 'Rheumatology'
  }
};
