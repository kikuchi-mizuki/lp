import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '業務改善無料相談 | AIコレクションズ',
  description: 'AIで変えたいのに、正しい順番が見えず止まっている方へ。業務に合った改善の順番を無料で整理します。',
  icons: {
    icon: [{ url: '/images/logo.png', type: 'image/png' }],
    apple: '/images/logo.png',
  },
  keywords: ['業務改善', 'AI導入', '自動化', '無料相談', 'DX', '効率化'],
  openGraph: {
    title: '業務改善無料相談 | AIコレクションズ',
    description: 'AIで変えたいのに、正しい順番が見えず止まっている方へ。無料で改善の順番を整理します。',
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
    <html lang="ja">
      <body className="antialiased min-h-screen">
        {children}
      </body>
    </html>
  )
}
