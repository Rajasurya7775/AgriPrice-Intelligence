// translations.js — Client-side translation stubs to prevent crashes
// and handle essential validation messages.

var currentLang = 'en';

function applyTranslations(lang) {
  if (lang) {
    currentLang = lang;
  }
  // Stub function. UI translations are in English, advisory translations are done via AI.
}

function t(key) {
  const dictionary = {
    'error_no_commodity': 'Please select a commodity',
    'error_no_district': 'Please select a district'
  };
  return dictionary[key] || key;
}
