import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Get DAPI port from environment variable, default to 5000
const dapiPort = process.env.VITE_DAPI_PORT || '5000';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/v5.5': {
        target: `http://localhost:${dapiPort}`,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
