import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../../react-build',
    emptyOutDir: true,
  },
  test: {
    globals: true,
  },
})
