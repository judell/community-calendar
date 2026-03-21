import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import fs from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Plugin to externalize XMLUI's CSS import so it doesn't go through PostCSS/Tailwind
function externalizeXmluiCss() {
  return {
    name: 'externalize-xmlui-css',
    enforce: 'pre',
    resolveId(source, importer) {
      if (source === './index.css' && importer && importer.includes('xmlui')) {
        return { id: 'virtual:xmlui-css', external: false }
      }
    },
    load(id) {
      if (id === 'virtual:xmlui-css') {
        return ''
      }
    },
    generateBundle() {
      const cssPath = path.resolve(__dirname, 'node_modules/xmlui/dist/lib/index.css')
      if (fs.existsSync(cssPath)) {
        this.emitFile({
          type: 'asset',
          fileName: 'xmlui.css',
          source: fs.readFileSync(cssPath),
        })
      }
      // Copy XMLUI Inspector files
      const xmluiDir = path.resolve(__dirname, '../xmlui')
      for (const file of ['xs-diff.html', 'xmlui-parser.es.js']) {
        const filePath = path.resolve(xmluiDir, file)
        if (fs.existsSync(filePath)) {
          this.emitFile({
            type: 'asset',
            fileName: file,
            source: fs.readFileSync(filePath),
          })
        }
      }
    },
    transformIndexHtml() {
      return [
        {
          // Load XMLUI CSS FIRST so its @layer order declaration takes precedence
          tag: 'link',
          attrs: { rel: 'stylesheet', href: './xmlui.css' },
          injectTo: 'head',
        },
      ]
    },
  }
}

export default defineConfig({
  plugins: [
    externalizeXmluiCss(),
    react(),
  ],
  base: './',
  build: {
    outDir: '../../react-build',
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      xmlui: path.resolve(__dirname, 'node_modules/xmlui/dist/lib/xmlui.js'),
      react: path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
    },
  },
  test: {
    globals: true,
  },
})
