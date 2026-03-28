'use client'

import { Clock, Users, FileText, TrendingDown, AlertCircle, Repeat } from 'lucide-react'
import type { CommonProblem } from '@/types'

const problems: CommonProblem[] = [
  {
    title: '手作業が多くて時間がかかる',
    description: '毎日同じ作業の繰り返しで、本来の業務に集中できない',
    icon: 'Clock',
  },
  {
    title: '人手不足で業務が回らない',
    description: '採用しても定着しない。少ない人数で多くの業務をこなす必要がある',
    icon: 'Users',
  },
  {
    title: 'ミスやヌケモレが多発',
    description: '手作業によるヒューマンエラーが発生し、確認作業に時間を取られる',
    icon: 'AlertCircle',
  },
  {
    title: '情報が分散して管理できない',
    description: 'Excel、メール、紙など様々な場所に情報が散らばっている',
    icon: 'FileText',
  },
  {
    title: '売上が伸びても利益が増えない',
    description: '業務量が増えるほど人件費も増え、利益率が改善しない',
    icon: 'TrendingDown',
  },
  {
    title: '同じ質問への対応に追われる',
    description: '顧客やスタッフからの問い合わせ対応で本来の業務ができない',
    icon: 'Repeat',
  },
]

const iconMap = {
  Clock,
  Users,
  FileText,
  TrendingDown,
  AlertCircle,
  Repeat,
}

export default function ProblemsSection() {
  return (
    <section id="problems" className="section-container bg-white">
      <div className="text-center mb-16">
        <h2 className="section-heading">
          こんなお悩み、<br className="sm:hidden" />
          <span className="gradient-text">ありませんか？</span>
        </h2>
        <p className="section-subheading">
          多くの企業が抱える、業務効率化の課題
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {problems.map((problem, index) => {
          const Icon = iconMap[problem.icon as keyof typeof iconMap]
          return (
            <div
              key={index}
              className="card-hover animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900">
                {problem.title}
              </h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                {problem.description}
              </p>
            </div>
          )
        })}
      </div>

      <div className="mt-16 max-w-3xl mx-auto text-center px-2">
        <p className="text-base md:text-lg text-gray-700 leading-relaxed mb-6">
          課題のリストアップまではできても、
          <span className="font-semibold text-gray-900">「どれを先に潰すと効くか」</span>
          が見えないまま、検討だけが長引く——というパターンはとても多いです。
        </p>
        <p className="text-sm md:text-base text-gray-600 leading-relaxed mb-10">
          ツール選定の前に、業務の流れと優先順位を一緒に整理する。それがこの無料相談の役割です。
        </p>
      </div>

      <div className="mt-4 text-center">
        <div className="inline-block bg-gradient-to-r from-primary-50 to-accent-50 rounded-2xl p-8 max-w-3xl shadow-[var(--shadow-soft)]">
          <p className="text-lg md:text-xl font-semibold text-gray-900 mb-4">
            これらの悩みは、AIや自動化で解決できます
          </p>
          <p className="text-gray-600 mb-6">
            でも、「何から手をつければいいかわからない」という声をよく聞きます。<br />
            だからこそ、まずは無料相談で現状を整理しましょう。
          </p>
          <a href="#contact" className="btn-primary">
            無料で相談してみる
          </a>
        </div>
      </div>
    </section>
  )
}
