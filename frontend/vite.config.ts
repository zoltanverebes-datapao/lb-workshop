import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/app/' : '/',
  plugins: [
    tailwindcss(),
    react(),
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
}))
