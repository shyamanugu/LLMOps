import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base "./" keeps asset paths relative so a static build works
// even when the dist/ folder is opened from a subpath.
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 5173,
    open: true
  }
})
