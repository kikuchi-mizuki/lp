'use client'

import { ArrowRight } from 'lucide-react'

export default function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-section-overlay" aria-hidden />

      <div className="hero-section-inner">
        <h1 className="hero-title">
          AIで変えたいのに、
          <br />
          正しい順番が
          <br />
          見えないまま
          <br />
          <span className="gradient-text">止まっている方へ</span>
        </h1>

        <div
          style={{
            width: '88px',
            height: '6px',
            margin: '14px auto 0',
            borderRadius: '999px',
            background: 'linear-gradient(90deg, var(--primary-color), var(--accent-color))',
            marginBottom: '2rem',
          }}
        />

        <p className="hero-lead">
          あなたの業務に合った改善方法を、無料で整理します。
          <br />
          まずは現状を整理するところから始めましょう。
        </p>

        <div className="hero-cta-row">
          <a href="#contact" className="btn-primary-large group inline-flex items-center">
            無料で相談してみる
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </a>
          <a href="#cases" className="btn-secondary px-8 py-4">
            導入事例を見る
          </a>
        </div>

        <p className="hero-note">無理な営業は一切ありません。お気軽にご相談ください。</p>
      </div>
    </section>
  )
}
