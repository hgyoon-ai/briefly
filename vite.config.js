import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => {
  // command: 'serve' (dev) | 'build' (prod build)
  const repo = 'briefly'

  return {
    base: command === 'build' ? `/${repo}/` : '/',
    plugins: [react()],
    server: {
      port: 5173,
      open: true
    }
  }
})