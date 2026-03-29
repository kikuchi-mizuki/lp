'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useState } from 'react'
import type { CSSProperties } from 'react'
import { Menu, X } from 'lucide-react'

const linkStyle: CSSProperties = {
  color: 'var(--text-gray)',
  fontSize: '0.95rem',
  padding: '0.5rem 0',
  fontWeight: 500,
}

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header
      className="site-header"
      style={{
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'saturate(150%) blur(8px)',
        WebkitBackdropFilter: 'saturate(150%) blur(8px)',
        boxShadow: 'var(--shadow-soft)',
      }}
    >
      <div className="container-wide">
        <div className="header-inner-row">
          <Link href="/" style={{ display: 'flex', alignItems: 'center' }}>
            <Image
              src="/images/logo.png"
              alt="AI Collections"
              width={168}
              height={40}
              priority
              style={{ height: 'auto', width: 'auto', maxWidth: '168px' }}
            />
          </Link>

          <nav className="header-nav-desktop" aria-label="メインナビゲーション">
            <a
              href="#cases"
              style={linkStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--primary-color)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-gray)'
              }}
            >
              導入事例
            </a>
            <a
              href="#problems"
              style={linkStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--primary-color)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-gray)'
              }}
            >
              よくある悩み
            </a>
            <a
              href="#faq"
              style={linkStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--primary-color)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-gray)'
              }}
            >
              よくある質問
            </a>
            <a
              href="https://lp-production-9e2c.up.railway.app/main"
              target="_blank"
              rel="noopener noreferrer"
              style={linkStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--primary-color)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-gray)'
              }}
            >
              AI秘書サービス
            </a>
            <a href="#contact" className="btn-primary">
              無料相談する
            </a>
          </nav>

          <button
            type="button"
            className="header-menu-toggle"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="メニュー"
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {isMenuOpen && (
        <div className="header-mobile-panel">
          <nav className="container-wide" style={{ paddingTop: '1rem', paddingBottom: '1rem' }}>
            <a
              href="#cases"
              style={{ display: 'block', padding: '0.5rem 0', color: '#374151', fontWeight: 500 }}
              onClick={() => setIsMenuOpen(false)}
            >
              導入事例
            </a>
            <a
              href="#problems"
              style={{ display: 'block', padding: '0.5rem 0', color: '#374151', fontWeight: 500 }}
              onClick={() => setIsMenuOpen(false)}
            >
              よくある悩み
            </a>
            <a
              href="#faq"
              style={{ display: 'block', padding: '0.5rem 0', color: '#374151', fontWeight: 500 }}
              onClick={() => setIsMenuOpen(false)}
            >
              よくある質問
            </a>
            <a
              href="https://lp-production-9e2c.up.railway.app/main"
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'block', padding: '0.5rem 0', color: '#374151', fontWeight: 500 }}
              onClick={() => setIsMenuOpen(false)}
            >
              AI秘書サービス
            </a>
            <a
              href="#contact"
              className="btn-primary"
              style={{ display: 'block', textAlign: 'center', marginTop: '1rem' }}
              onClick={() => setIsMenuOpen(false)}
            >
              無料相談する
            </a>
          </nav>
        </div>
      )}
    </header>
  )
}
