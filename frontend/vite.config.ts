/// <reference types="vitest/config" />
/**
 * Vite build, dev server and Vitest configuration.
 * Dev server proxies /api to the FastAPI backend so the browser sees one origin.
 */
import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        // Keep the heavy 3D stack out of the main bundle; it loads only on auditorium pages.
        manualChunks(id: string) {
          if (/node_modules\/(three|@react-three)\//.test(id)) return 'three'
          return undefined
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    restoreMocks: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/main.tsx', 'src/test/**', 'src/**/*.d.ts', 'src/**/types.ts'],
      reporter: ['text', 'html', 'lcov'],
      thresholds: { lines: 85, functions: 85, branches: 85, statements: 85 },
    },
  },
})
