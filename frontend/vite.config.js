import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { buildHelp, DOCS } from './scripts/help/build.mjs'

const target = process.env.FLASK_URL || 'http://127.0.0.1:5000'

function helpDocs() {
  return {
    name: 'help-docs',
    buildStart() {
      buildHelp({ log: (msg) => console.log(msg) })
    },
    configureServer(server) {
      server.watcher.add(DOCS)
      server.watcher.on('change', (file) => {
        if (!file.startsWith(DOCS)) return
        try {
          buildHelp({ log: (msg) => console.log(msg) })
          server.ws.send({ type: 'full-reload' })
        } catch (err) {
          console.error(err.message)
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), helpDocs()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/imprimir': { target, changeOrigin: true },
      '/static': { target, changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: false,
  },
})
