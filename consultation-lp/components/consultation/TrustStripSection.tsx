'use client'

import { Building2, Headphones, ShieldCheck } from 'lucide-react'

const items = [
  { icon: Building2, label: '50+', sub: '企業の支援・相談実績' },
  { icon: Headphones, label: '相談無料', sub: 'オンライン可' },
  { icon: ShieldCheck, label: '無理な営業なし', sub: 'まずは現状整理' },
]

export default function TrustStripSection() {
  return (
    <section
      className="border-y border-[var(--border-light)] bg-white/80 py-8 backdrop-blur-sm"
      aria-label="信頼のポイント"
    >
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-center gap-6 px-4 sm:flex-row sm:gap-10 md:gap-16">
        {items.map(({ icon: Icon, label, sub }) => (
          <div
            key={label}
            className="flex flex-1 items-center justify-center gap-4 md:gap-5"
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-100 text-[var(--primary-color)] shadow-sm">
              <Icon className="h-6 w-6" aria-hidden />
            </div>
            <div className="text-left">
              <p className="text-lg font-extrabold text-[var(--text-dark)] md:text-xl">{label}</p>
              <p className="text-sm text-[var(--text-gray)]">{sub}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
