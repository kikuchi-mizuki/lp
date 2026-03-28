import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-6 text-center bg-white">
      <p className="text-sm font-semibold text-[var(--primary-color)] mb-2">404</p>
      <h1 className="text-2xl md:text-3xl font-bold text-[var(--text-dark)] mb-4">
        ページが見つかりません
      </h1>
      <p className="text-[var(--text-gray)] max-w-md mb-8 leading-relaxed">
        URLが間違っているか、ページが移動した可能性があります。業務改善無料相談のLPはトップからご覧いただけます。
      </p>
      <Link href="/" className="btn-primary-large">
        トップ（無料相談LP）へ
      </Link>
    </div>
  )
}
