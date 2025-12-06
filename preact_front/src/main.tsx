// src/main.tsx
import { render } from 'preact';
import { LocationProvider } from 'preact-iso';
import { App } from './App';
import { LanguageProvider } from './contexts/LanguageContext';
import './style.css'; // Подключаем стили

render(
  <LocationProvider>
    <App />
  </LocationProvider>,
  document.getElementById('app')!
);