/**
 * MKSAP Medical Systems Configuration
 *
 * Defines all 12 medical systems with:
 * - Code: URL parameter (e.g., 'cv', 'en')
 * - Name: Full system name
 * - Emoji: System emoji for logging/display
 * - Folder: Output folder name (no spaces, filesystem-safe)
 *
 * @module systems
 * @exports {Object} System configuration keyed by system code
 */

module.exports = {
  cv: {
    code: 'cv',
    name: 'Cardiovascular Medicine',
    emoji: '🫀',
    folder: 'Cardiovascular'
  },
  en: {
    code: 'en',
    name: 'Endocrinology and Metabolism',
    emoji: '🦋',
    folder: 'Endocrinology'
  },
  fccs: {
    code: 'fccs',
    name: 'Foundations of Clinical Practice: Common Symptoms',
    emoji: '🤒',
    folder: 'Foundations'
  },
  gihp: {
    code: 'gihp',
    name: 'Gastroenterology and Hepatology',
    emoji: '🍽️',
    folder: 'Gastroenterology'
  },
  hm: {
    code: 'hm',
    name: 'Hematology',
    emoji: '🩸',
    folder: 'Hematology'
  },
  id: {
    code: 'id',
    name: 'Infectious Disease',
    emoji: '🦠',
    folder: 'Infectious_Disease'
  },
  dmin: {
    code: 'dmin',
    name: 'Interdisciplinary Medicine and Dermatology',
    emoji: '🩹',
    folder: 'Dermatology'
  },
  np: {
    code: 'np',
    name: 'Nephrology',
    emoji: '💧',
    folder: 'Nephrology'
  },
  nr: {
    code: 'nr',
    name: 'Neurology',
    emoji: '🧠',
    folder: 'Neurology'
  },
  on: {
    code: 'on',
    name: 'Oncology',
    emoji: '🎗️',
    folder: 'Oncology'
  },
  pmcc: {
    code: 'pmcc',
    name: 'Pulmonary and Critical Care Medicine',
    emoji: '🫁',
    folder: 'Pulmonary'
  },
  rm: {
    code: 'rm',
    name: 'Rheumatology',
    emoji: '🦴',
    folder: 'Rheumatology'
  }
};
