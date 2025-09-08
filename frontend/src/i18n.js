import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend'; // New import

i18n
  .use(Backend) // Use the HTTP backend
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    debug: true,
    fallbackLng: 'es', // Default language
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
    backend: {
      loadPath: '/locales/{{lng}}/translation.json', // Path to your translation files
    },
    // resources: { // Remove this section, as the backend will load them
    //   es: {
    //     translation: {
    //       // Spanish translations will go here
    //     }
    //   },
    //   en: {
    //     translation: {
    //       // English translations will go here
    //     }
    //   }
    // }
  });

export default i18n;