// vite.config.js
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';

export default defineConfig({
  // envDir: '../', // Это заставит Vite заглянуть в .env на уровень выше
  plugins: [preact()],

  // Важно: не ищем .env на верхнем уровне,
  // т.к. теперь конфигурация идет через HTML
  envDir: '.',

  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'abc8888.ru',
      'test.abc8888.ru',
      'localhost'
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

  // Оптимизация для production
  build: {
    target: 'es2015',
    minify: 'esbuild',
    terserOptions: {
      compress: {
        drop_console: true, // убираем console.log в production
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        // Хеши для кэширования
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  }
});