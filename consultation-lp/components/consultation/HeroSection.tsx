'use client'

import { ArrowRight } from 'lucide-react'

export default function HeroSection() {
  return (
    <section
      className="relative text-center overflow-hidden"
      style={{
        padding: '6rem 0',
        minHeight: '72vh',
        display: 'grid',
        placeItems: 'center',
        background: `
          radial-gradient(1200px 600px at 20% -10%, rgba(124, 58, 237, 0.12), transparent 60%),
          radial-gradient(1200px 600px at 80% 10%, rgba(37, 99, 235, 0.12), transparent 60%),
          linear-gradient(135deg, var(--primary-light) 0%, var(--background-white) 100%)
        `,
      }}
    >
      {/* Subtle abstract illustration layer */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(600px 280px at 20% 20%, rgba(255,255,255,0.35), transparent 60%),
            radial-gradient(600px 280px at 80% 10%, rgba(255,255,255,0.2), transparent 60%)
          `,
          mixBlendMode: 'overlay',
        }}
      />

      <div className="relative z-10" style={{ maxWidth: '800px', margin: '0 auto', padding: '0 2rem' }}>
        {/* タイトル - 既存LPスタイル */}
        <h1
          className="font-extrabold mb-6"
          style={{
            fontSize: 'clamp(2.5rem, 6vw, 3.6rem)',
            fontWeight: 800,
            lineHeight: 1.2,
            letterSpacing: '0.01em',
            backgroundImage: 'linear-gradient(180deg, #0B1220 0%, #0B1220 45%, #334155 100%)',
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            filter: 'drop-shadow(0 2px 10px rgba(2, 6, 23, 0.06))',
          }}
        >
          AIや自動化で
          <br />
          業務を改善したいけど、
          <br />
          何から始めればいいか
          <br />
          <span className="gradient-text">わからない方へ</span>
        </h1>

        {/* タイトル下の装飾ライン */}
        <div
          style={{
            content: '""',
            display: 'block',
            width: '88px',
            height: '6px',
            margin: '14px auto 0',
            borderRadius: '999px',
            background: 'linear-gradient(90deg, var(--primary-color), var(--accent-color))',
            marginBottom: '2rem',
          }}
        />

        {/* サブタイトル - 既存LPスタイル */}
        <p
          className="mb-10"
          style={{
            fontSize: '1.2rem',
            color: 'var(--text-gray)',
            fontWeight: 400,
            maxWidth: '720px',
            margin: '0 auto 2.5rem',
            lineHeight: 1.7,
          }}
        >
          あなたの業務に合った改善方法を、無料で整理します。
          <br />
          まずは現状を整理するところから始めましょう。
        </p>

        {/* CTAボタン - 既存LPスタイル */}
        <div
          className="mb-8"
          style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <a
            href="#contact"
            className="btn-primary-large group inline-flex items-center"
          >
            無料で相談してみる
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </a>
          <a
            href="#cases"
            className="btn-secondary px-8 py-4"
          >
            導入事例を見る
          </a>
        </div>

        {/* トライアルノート */}
        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-light)',
            marginBottom: '2rem',
          }}
        >
          無理な営業は一切ありません。お気軽にご相談ください。
        </p>

        {/* トラストマーク */}
        <div
          className="mt-12 pt-8"
          style={{
            borderTop: '1px solid var(--border-light)',
          }}
        >
          <p style={{ fontSize: '0.875rem', color: 'var(--text-light)', marginBottom: '1rem' }}>
            信頼の実績
          </p>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '2rem',
              fontSize: '0.875rem',
              color: 'var(--text-gray)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: '2rem', fontWeight: 'bold', marginRight: '0.5rem' }} className="gradient-text">
                50+
              </span>
              <span>企業の導入実績</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: '2rem', fontWeight: 'bold', marginRight: '0.5rem' }} className="gradient-text">
                90%
              </span>
              <span>業務時間削減</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: '2rem', fontWeight: 'bold', marginRight: '0.5rem' }} className="gradient-text">
                0円
              </span>
              <span>相談料</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
