'use client'

import { ArrowRight } from 'lucide-react'

export default function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-section-overlay" aria-hidden />

      <div className="hero-section-inner">
        <h1 className="hero-title">
          AIで変えたいのに、
          <br className="hidden sm:block" />
          <span className="sm:hidden"> </span>
          正しい順番が見えないまま
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
            marginBottom: '1.5rem',
          }}
        />

        <p className="hero-lead">
          あなたの業務に合った改善方法を、無料で整理します。
        </p>

        <div className="hero-cta-row">
          <a
            href="https://line.me/ti/p/EZPuFuksS3"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary-large group inline-flex items-center"
          >
            LINEで無料相談
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </a>
          <a href="#cases" className="btn-secondary px-6 py-3 sm:px-8 sm:py-4">
            導入事例を見る
          </a>
        </div>

        <p className="hero-note">無理な営業は一切ありません</p>
      </div>
    </section>
  )
}
