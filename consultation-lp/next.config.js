/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost', 'your-supabase-project.supabase.co'],
  },
  // ブラウザ既定の /favicon.ico リクエストを既存ロゴへ（404回避）
  async rewrites() {
    return [{ source: '/favicon.ico', destination: '/images/logo.png' }]
  },
  /**
   * macOS で Watchpack が EMFILE（開けるファイル数上限）に当たると、
   * .next 配下のチャンクが生成されず main-app.js 等が 404 になることがある。
   * NEXT_WEBPACK_USE_POLL=1 でポーリング監視に切り替え（CPUはやや増える）。
   */
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        ...config.watchOptions,
        ignored: ['**/node_modules/**', '**/.git/**'],
      }
      if (process.env.NEXT_WEBPACK_USE_POLL === '1') {
        config.watchOptions.poll = 2000
        config.watchOptions.aggregateTimeout = 300
      }
    }
    return config
  },
}

module.exports = nextConfig
