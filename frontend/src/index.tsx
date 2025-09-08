import React from 'react';
import ReactDOM from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css'; // Import Bootstrap CSS
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import './i18n'; // Import i18n configuration
import { I18nextProvider } from 'react-i18next'; // Import I18nextProvider
import i18n from './i18n'; // Import i18n instance
import moment from 'moment';
import 'moment/locale/es'; // Import Spanish locale for moment

// Set moment.js locale globally based on the initial language of i18next
moment.locale(i18n.language);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <I18nextProvider i18n={i18n}> {/* Wrap App with I18nextProvider */}
      <App />
    </I18nextProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
