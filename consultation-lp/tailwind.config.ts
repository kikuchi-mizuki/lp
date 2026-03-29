import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // AIコレクションズの既存カラーパレットに完全一致
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6', // accent-color
          600: '#1E40AF', // primary-color
          700: '#1E3A8A', // primary-dark
          800: '#1E3A8A',
          900: '#1E3A8A',
        },
        secondary: {
          100: '#F1F5F9', // secondary-light
          500: '#64748B', // secondary-color
          700: '#475569', // text-gray
          800: '#334155',
          900: '#0F172A', // text-dark
        },
        accent: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',
          600: '#2563EB',
        },
      },
      fontFamily: {
        sans: ['Noto Sans JP', 'sans-serif'],
      },
      borderRadius: {
        'small': '12px',
        'medium': '16px',
        'large': '24px',
      },
      boxShadow: {
        'soft': '0 4px 25px rgba(30, 64, 175, 0.08)',
        'medium': '0 8px 35px rgba(30, 64, 175, 0.12)',
        'card': '0 2px 15px rgba(0, 0, 0, 0.08)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'scale-in': 'scaleIn 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
export default config
