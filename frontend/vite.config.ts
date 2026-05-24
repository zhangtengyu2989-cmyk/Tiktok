import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

/**
 * 开发时代理 /api → 后端。若后端不在 8000，可在 frontend/.env.development 中设置：
 * VITE_API_PROXY_TARGET=http://localhost:8001
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

  return {
    base: '/app/',
    plugins: [
      react(),
      {
        name: 'serve-landing',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            const url = (req.url || '').split('?')[0]
            // 静态页面直接从 docs 目录读取，不走代理
            const staticPages: Record<string, string> = {
              '/': 'landing.html',
              '/index.html': 'landing.html',
              '/paper': 'research_paper.html',
              '/research': 'research_whitepaper.html',
              '/terms': 'terms.html',
              '/privacy': 'privacy.html',
            }
            const file = staticPages[url]
            if (file) {
              const filePath = path.resolve(__dirname, '../docs', file)
              if (fs.existsSync(filePath)) {
                res.setHeader('Content-Type', 'text/html; charset=utf-8')
                res.end(fs.readFileSync(filePath, 'utf-8'))
                return
              }
            }
            next()
          })
        },
      },
    ],
    server: {
      allowedHosts: ['eliotech.top', 'www.eliotech.top'],
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
        },
        '/health': {
          target,
          changeOrigin: true,
        },
      },
    },
    build: {
      target: 'es2020',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('echarts')) return 'vendor-echarts'
              if (id.includes('framer-motion')) return 'vendor-motion'
              if (id.includes('@mui')) return 'vendor-mui'
              if (id.includes('react-dom') || id.includes('react/') || id.includes('react-router')) return 'vendor-react'
              if (id.includes('html2canvas')) return 'vendor-html2canvas'
            }
          },
        },
      },
    },
  }
})
