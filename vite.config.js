import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteSingleFile } from 'vite-plugin-singlefile'

// "single" mode writes one self-contained index.html (handy for sending a preview around).
export default defineConfig(({ mode }) => ({
  base: './',
  plugins: [vue(), ...(mode === 'single' ? [viteSingleFile()] : [])],
  build: { outDir: mode === 'single' ? 'dist-single' : 'dist', chunkSizeWarningLimit: 4000 },
}))
