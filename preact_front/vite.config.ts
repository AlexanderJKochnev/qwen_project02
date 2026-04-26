// vite.config.ts
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
// Считываем порт из переменных окружения. Если его нет — берем 5173
const PORT = process.env.VITE_PORT ? parseInt(process.env.VITE_PORT) : 5173;

export default defineConfig({
  plugins: [preact()],
  resolve: {
    alias: {
      'react': 'preact/compat',
      'react-dom': 'preact/compat',
    },
  },
  server: {
    host: '0.0.0.0',
    port: PORT,
    strictPort: true,
    hmr: {
      port: PORT,
      host: '0.0.0.0',
    },
    proxy: {
      '/proxy-api': {
        target: 'http://app:8091',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/proxy-api/, ''),
        // ДОБАВЬТЕ ЭТОТ БЛОК ДЛЯ ОТОБРАЖЕНИЯ ЛОГОВ В ТЕРМИНАЛЕ 👇
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log(`[Proxy] Отправка запроса: ${req.method} ${req.url}`);
          });
        },
      },
    },
  },
});