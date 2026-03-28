'use client'

import type { ReactNode } from 'react'
import { ArrowRight, MessageCircleHeart } from 'lucide-react'

type Variant = 'after-cases' | 'after-faq'

const copy: Record<
  Variant,
  { eyebrow: string; title: ReactNode; body: string; button: string }
> = {
  'after-cases': {
    eyebrow: '次の一歩',
    title: (
      <>
        事例のあとに残るのは、
        <br className="sm:hidden" />
        <span className="gradient-text">「自社ならどうする？」</span>です
      </>
    ),
    body:
      '同じ業種でなくても大丈夫です。課題の型は似ています。無料相談で、優先して直す順番だけ一緒に決めましょう。',
    button: '無料で相談してみる',
  },
  'after-faq': {
    eyebrow: '最後のひと押し',
    title: (
      <>
        不安がひとつでも残っているなら、
        <br className="sm:hidden" />
        <span className="gradient-text">その場で解消</span>できます
      </>
    ),
    body: 'メールだけでも構いません。まずは現状を書き出すところから。相談したからといって必ず契約になるわけではありません。',
    button: '無料相談に進む',
  },
}

export default function ConsultationCTASection({ variant }: { variant: Variant }) {
  const c = copy[variant]

  return (
    <section
      className="section-container"
      style={{
        background:
          'linear-gradient(180deg, var(--background-white) 0%, var(--primary-light) 35%, var(--accent-light) 100%)',
      }}
    >
      <div className="mx-auto max-w-3xl rounded-[var(--radius-large)] border border-white/80 bg-white/90 p-8 text-center shadow-[var(--shadow-medium)] backdrop-blur-sm md:p-12">
        <p className="mb-3 text-xs font-bold uppercase tracking-widest text-[var(--primary-color)]">{c.eyebrow}</p>
        <h2 className="section-heading mb-4 text-2xl md:text-3xl">{c.title}</h2>
        <p className="mx-auto mb-8 max-w-xl text-[var(--text-gray)] leading-relaxed">{c.body}</p>
        <a href="#contact" className="btn-primary-large group inline-flex items-center gap-2">
          <MessageCircleHeart className="h-5 w-5" aria-hidden />
          {c.button}
          <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden />
        </a>
        <p className="mt-6 text-sm text-[var(--text-light)]">無理な営業は一切ありません</p>
      </div>
    </section>
  )
}
