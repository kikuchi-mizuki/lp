import Link from 'next/link'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* ブランド */}
          <div>
            <div className="text-2xl font-bold text-white mb-4">
              AIコレクションズ
            </div>
            <p className="text-gray-400 text-sm">
              業務改善の第一歩は、無料相談から。<br />
              あなたの業務に最適なソリューションを一緒に見つけましょう。
            </p>
          </div>

          {/* リンク */}
          <div>
            <h3 className="text-white font-semibold mb-4">サービス</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="hover:text-primary-400 transition-colors">
                  業務改善無料相談
                </Link>
              </li>
              <li>
                <a href="#cases" className="hover:text-primary-400 transition-colors">
                  導入事例
                </a>
              </li>
              <li>
                <a href="#faq" className="hover:text-primary-400 transition-colors">
                  よくある質問
                </a>
              </li>
              <li>
                <a
                  href="https://lp-production-9e2c.up.railway.app/main"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary-400 transition-colors"
                >
                  AI秘書サービス
                </a>
              </li>
            </ul>
          </div>

          {/* お問い合わせ */}
          <div>
            <h3 className="text-white font-semibold mb-4">お問い合わせ</h3>
            <p className="text-sm text-gray-400 mb-2">
              お気軽にご相談ください
            </p>
            <a
              href="#contact"
              className="inline-block btn-primary mt-2"
            >
              無料相談する
            </a>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-500">
          <p>&copy; {currentYear} AIコレクションズ. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
