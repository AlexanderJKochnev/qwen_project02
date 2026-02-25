// vite.config.js
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';

export default defineConfig({
  envDir: '../', // Это заставит Vite заглянуть в .env на уровень выше
  plugins: [preact()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'abc8888.ru',
    ],
    proxy: {
      // Проксируем все запросы к /proxy-api → FastAPI внутри Docker
      '/proxy-api': {
        target: 'http://app:8091',
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/proxy-api/, ''),
      },
    },
  },
});