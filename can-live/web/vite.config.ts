import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// dev サーバ(5273)。/api を can-live バックエンド(8100)へプロキシ（WS 対応）。
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5273,
    proxy: {
      '/api': {
        target: 'http://localhost:8100',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
