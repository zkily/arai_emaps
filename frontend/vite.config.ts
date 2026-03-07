import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
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
    proxy: {
      // APIリクエストをバックエンドにプロキシ
      // 相対パス /api で始まるすべてのリクエストをバックエンドに転送
      '/api': {
        target: 'http://localhost:8005', // バックエンドサーバー（start.py の backend_port と一致）
        changeOrigin: true,
        secure: false,
        // リライト設定（必要に応じて）
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // WebSocket接続をバックエンドにプロキシ
      '/ws': {
        target: 'ws://localhost:8005',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})

