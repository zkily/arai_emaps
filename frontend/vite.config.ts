import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** VITE_DEV_HTTPS=true 時: 証明書パスがあれば使用、なければ Vite 既定の自己署名 */
function resolveDevHttps(
  env: Record<string, string>
): boolean | { key: Buffer; cert: Buffer } {
  const on = env.VITE_DEV_HTTPS === 'true' || env.VITE_DEV_HTTPS === '1'
  if (!on) return false
  const certEnv = env.VITE_SSL_CERTFILE
  const keyEnv = env.VITE_SSL_KEYFILE
  if (certEnv && keyEnv) {
    const certPath = path.isAbsolute(certEnv) ? certEnv : path.resolve(__dirname, certEnv)
    const keyPath = path.isAbsolute(keyEnv) ? keyEnv : path.resolve(__dirname, keyEnv)
    try {
      if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
        return { cert: fs.readFileSync(certPath), key: fs.readFileSync(keyPath) }
      }
    } catch {
      /* フォールバック */
    }
  }
  return true
}

function wsTargetFromApiTarget(apiTarget: string): string {
  if (apiTarget.startsWith('https://')) return 'wss://' + apiTarget.slice('https://'.length)
  if (apiTarget.startsWith('http://')) return 'ws://' + apiTarget.slice('http://'.length)
  return 'ws://localhost:8005'
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  const apiHttps = env.VITE_API_HTTPS === 'true' || env.VITE_API_HTTPS === '1'
  const apiProxyTarget =
    env.VITE_API_PROXY_TARGET ||
    (apiHttps ? 'https://localhost:8005' : 'http://localhost:8005')
  const wsProxyTarget = env.VITE_WS_PROXY_TARGET || wsTargetFromApiTarget(apiProxyTarget)

  const define: Record<string, string> = {}
  if (mode === 'production') {
    let prodApiBase = env.VITE_API_BASE_URL
    if (!prodApiBase && apiHttps) {
      prodApiBase = env.VITE_API_PROXY_TARGET || 'https://localhost:8005'
    }
    if (prodApiBase) {
      define['import.meta.env.VITE_API_BASE_URL'] = JSON.stringify(prodApiBase)
    }
  }

  return {
    define,
    // 開発サーバー起動を高速化：重い依存を事前バンドル（初回後はキャッシュで速くなる）
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'element-plus',
        '@element-plus/icons-vue',
        'echarts',
        'vue-echarts',
        'axios',
        'dayjs',
        'xlsx',
        'file-saver',
        'chart.js',
      ],
      exclude: [],
    },
    plugins: [
      vue(),
      AutoImport({
        resolvers: [ElementPlusResolver()],
        imports: ['vue', 'vue-router', 'pinia'],
        dts: 'src/auto-imports.d.ts',
      }),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: 'src/components.d.ts',
      }),
    ],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      host: '0.0.0.0', // すべてのネットワークインターフェースでリッスン
      port: 5000,
      // VITE_DEV_HTTPS=true で https://localhost:5000（証明書は VITE_SSL_* または Vite 自己署名）
      https: resolveDevHttps(env),
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false,
        },
        '/ws': {
          target: wsProxyTarget,
          ws: true,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
