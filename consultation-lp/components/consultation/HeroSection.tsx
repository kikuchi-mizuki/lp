'use client'

import { ArrowRight } from 'lucide-react'

export default function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-section-overlay" aria-hidden />

      <div className="hero-section-inner">
        <h1 className="hero-title">
          AIがあなたの
          <br />
          右腕になる時代
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
          3時間かかっていた業務が15分に。
          <br />
          活用事例を参考にしてみてください。
        </p>

        <div className="hero-cta-row">
          <a
            href="https://line.me/ti/p/EZPuFuksS3"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary-large group inline-flex items-center"
          >
            LINEで相談してみる
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </a>
        </div>

        <p className="hero-note">まずは事例を見て、あなたに合うか確かめてください</p>
      </div>
    </section>
  )
}
