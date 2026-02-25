// src/config/api.ts

// Определяем базовый URL в зависимости от среды
// export const API_BASE_URL = import.meta.env.DEV
//  ? '/proxy-api' // Для разработки (через Vite proxy) будет проксироваться через Vite → http://app:8091
//  : 'https://api.abc8888.ru'; // Для продакшена (через Nginx шлюз)

export const API_BASE_URL = import.meta.env.VITE_API_URL;
export const IMAGE_BASE_URL = `${API_BASE_URL}`;