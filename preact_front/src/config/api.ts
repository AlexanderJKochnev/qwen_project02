// src/config/api.ts

// Типизация для window (для TypeScript)
declare global {
    interface Window {
        __RUNTIME_CONFIG__?: {
            API_URL: string;
        };
    }
}

// Кэшируем значение после первого чтения
let cachedApiUrl: string | null = null;

/**
 * Получает базовый URL API с приоритетом:
 * 1. Runtime конфигурация из window (устанавливается в HTML)
 * 2. Переменная окружения Vite (только для разработки)
 * 3. Значение по умолчанию
 */
export const API_BASE_URL = (() => {
    // Если уже кэшировали - возвращаем
    if (cachedApiUrl !== null) {
        return cachedApiUrl;
    }

    // Определяем URL по приоритету
    if (typeof window !== 'undefined' && window.__RUNTIME_CONFIG__?.API_URL) {
        // 1. Runtime конфигурация (из HTML)
        cachedApiUrl = window.__RUNTIME_CONFIG__.API_URL;
        console.log('[Config] Using runtime API URL:', cachedApiUrl);
    }
    else if (import.meta.env.VITE_API_URL) {
        // 2. Переменная окружения (только для dev, т.к. в prod переменные не подставляются)
        cachedApiUrl = import.meta.env.VITE_API_URL;
        console.log('[Config] Using env API URL:', cachedApiUrl);
    }
    else {
        // 3. Значение по умолчанию
        cachedApiUrl = 'https://api.abc8888.ru';
        console.log('[Config] Using default API URL:', cachedApiUrl);
    }

    return cachedApiUrl;
})();

// Для обратной совместимости
export const IMAGE_BASE_URL = API_BASE_URL;

// Для отладки (можно закомментировать в production)
console.log('[Config] API_BASE_URL initialized:', API_BASE_URL);