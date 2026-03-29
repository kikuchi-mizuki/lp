'use client'

import type { ReactNode } from 'react'
import { ArrowRight, MessageCircleHeart } from 'lucide-react'

type Variant = 'after-cases' | 'final'

const copy: Record<
  Variant,
  { eyebrow: string; title: ReactNode; body: string; button: string }
> = {
  'after-cases': {
    eyebrow: '',
    title: (
      <>
        <span className="gradient-text">あなたの業務でも実現できるか</span>
        <br />
        まずは相談してみませんか
      </>
    ),
    body:
      '同じ業種でなくても、課題の型は似ています。LINEで気軽にご相談ください。',
    button: 'LINEで相談する',
  },
  final: {
    eyebrow: '',
    title: (
      <>
        気になったら、
        <br className="sm:hidden" />
        <span className="gradient-text">まずLINEから</span>
      </>
    ),
    body: 'ご質問だけでも大丈夫です。',
    button: 'LINEで相談する',
  },
}

export default function ConsultationCTASection({ variant }: { variant: Variant }) {
  const c = copy[variant]

  return (
    <section
      className="section-container"
      style={{
        background: variant === 'after-cases'
          ? 'linear-gradient(180deg, var(--background-light) 0%, var(--background-white) 100%)'
          : 'var(--background-white)',
      }}
    >
      <div className={`mx-auto max-w-2xl text-center ${variant === 'after-cases' ? 'rounded-[var(--radius-large)] border border-[var(--border-light)] bg-white p-8 md:p-10 shadow-[var(--shadow-soft)]' : 'py-8'}`}>
        {c.eyebrow && (
          <p className="mb-3 text-xs font-bold uppercase tracking-widest text-[var(--primary-color)]">{c.eyebrow}</p>
        )}
        <h2 className={`mb-4 font-bold leading-tight ${variant === 'after-cases' ? 'text-xl md:text-2xl' : 'text-lg md:text-xl'}`}>
          {c.title}
        </h2>
        <p className={`mx-auto max-w-xl text-[var(--text-gray)] leading-relaxed ${variant === 'after-cases' ? 'mb-6' : 'mb-4 text-sm'}`}>
          {c.body}
        </p>
        <a
          href="https://line.me/ti/p/EZPuFuksS3"
          target="_blank"
          rel="noopener noreferrer"
          className={`group inline-flex items-center gap-2 ${variant === 'after-cases' ? 'btn-primary-large' : 'btn-secondary px-6 py-3'}`}
        >
          <MessageCircleHeart className="h-5 w-5" aria-hidden />
          {c.button}
          <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden />
        </a>
      </div>
    </section>
  )
}
