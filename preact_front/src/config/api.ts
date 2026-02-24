// src/config/api.ts

// Определяем базовый URL в зависимости от среды
// export const API_BASE_URL = import.meta.env.COMPOSE_PROJECT_NAME
//   ? '/proxy-api' // Для разработки (через Vite proxy) будет проксироваться через Vite → http://app:8091
//   : 'https://api.abc8888.ru'; // Для продакшена (через Nginx шлюз)

export const API_BASE_URL = (() => {
  if (appEnv === 'dev') return '/proxy-api';
  if (appEnv === 'test') return 'https://api.test.abc8888.ru';
  return 'https://api.abc8888.ru'; // По умолчанию Prod
})();

export const IMAGE_BASE_URL = `${API_BASE_URL}`;