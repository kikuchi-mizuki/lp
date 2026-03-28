'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useState } from 'react'
import { Menu, X } from 'lucide-react'

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="fixed top-0 left-0 right-0 z-50" style={{
      background: 'rgba(255, 255, 255, 0.85)',
      backdropFilter: 'saturate(150%) blur(8px)',
      WebkitBackdropFilter: 'saturate(150%) blur(8px)',
      boxShadow: 'var(--shadow-soft)',
    }}>
      <div className="mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1080px' }}>
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <Image
              src="/images/logo.png"
              alt="AI Collections"
              width={168}
              height={40}
              priority
              className="h-auto"
            />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <a
              href="#cases"
              className="font-medium transition-colors"
              style={{
                color: 'var(--text-gray)',
                fontSize: '0.95rem',
                padding: '0.5rem 0',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary-color)'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-gray)'}
            >
              導入事例
            </a>
            <a
              href="#problems"
              className="font-medium transition-colors"
              style={{
                color: 'var(--text-gray)',
                fontSize: '0.95rem',
                padding: '0.5rem 0',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary-color)'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-gray)'}
            >
              よくある悩み
            </a>
            <a
              href="#faq"
              className="font-medium transition-colors"
              style={{
                color: 'var(--text-gray)',
                fontSize: '0.95rem',
                padding: '0.5rem 0',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary-color)'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-gray)'}
            >
              よくある質問
            </a>
            <a
              href="https://lp-production-9e2c.up.railway.app/main"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium transition-colors"
              style={{
                color: 'var(--text-gray)',
                fontSize: '0.95rem',
                padding: '0.5rem 0',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary-color)'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-gray)'}
            >
              AI秘書サービス
            </a>
            <a
              href="#contact"
              className="btn-primary"
            >
              無料相談する
            </a>
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-gray-100"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="メニュー"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-200 animate-fade-in">
          <nav className="px-4 py-4 space-y-3">
            <a
              href="#cases"
              className="block py-2 text-gray-700 hover:text-primary-600 transition-colors font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              導入事例
            </a>
            <a
              href="#problems"
              className="block py-2 text-gray-700 hover:text-primary-600 transition-colors font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              よくある悩み
            </a>
            <a
              href="#faq"
              className="block py-2 text-gray-700 hover:text-primary-600 transition-colors font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              よくある質問
            </a>
            <a
              href="https://lp-production-9e2c.up.railway.app/main"
              target="_blank"
              rel="noopener noreferrer"
              className="block py-2 text-gray-700 hover:text-primary-600 transition-colors font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              AI秘書サービス
            </a>
            <a
              href="#contact"
              className="block btn-primary text-center mt-4"
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
