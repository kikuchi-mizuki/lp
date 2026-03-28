import type { Metadata } from 'next'
import { Inter, Noto_Sans_JP } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const notoSansJP = Noto_Sans_JP({ subsets: ['latin'], variable: '--font-noto-sans-jp' })

export const metadata: Metadata = {
  title: '業務改善無料相談 | AIコレクションズ',
  description: 'AIや自動化で業務を改善したいけど、何から始めればいいかわからない方へ。あなたの業務に合った改善方法を無料で整理します。',
  keywords: ['業務改善', 'AI導入', '自動化', '無料相談', 'DX', '効率化'],
  openGraph: {
    title: '業務改善無料相談 | AIコレクションズ',
    description: 'AIや自動化で業務を改善したいけど、何から始めればいいかわからない方へ。',
    type: 'website',
    locale: 'ja_JP',
  },
  twitter: {
    card: 'summary_large_image',
    title: '業務改善無料相談 | AIコレクションズ',
    description: 'あなたの業務に合った改善方法を無料で整理します。',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja" className={`${inter.variable} ${notoSansJP.variable}`}>
      <body className="font-sans antialiased bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  )
}
