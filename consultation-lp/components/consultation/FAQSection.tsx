'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { FAQ } from '@/types'

const faqs: FAQ[] = [
  {
    question: '本当に無料ですか？',
    answer:
      'はい、完全無料です。相談料や診断料などは一切かかりません。まずは現状の業務について気軽にお話しいただき、改善の方向性を一緒に考えます。',
  },
  {
    question: 'AIに詳しくなくても大丈夫ですか？',
    answer:
      '大丈夫です。むしろ、ITやAIに詳しくない方の方が多いです。専門用語を使わず、わかりやすく説明しますので、安心してご相談ください。',
  },
  {
    question: '相談したら必ず契約が必要ですか？',
    answer:
      'いいえ、相談後に必ず契約していただく必要はありません。まずは無料相談で現状を整理し、改善の方向性を確認していただきます。その上で、必要だと感じた場合にのみ、次のステップに進んでいただければと思います。',
  },
  {
    question: 'どんな業種でも相談できますか？',
    answer:
      'はい。小売業、製造業、サービス業、士業など、様々な業種の方からご相談いただいています。業種を問わず、「手作業が多い」「人手不足」「ミスが多い」といった課題は共通していることが多いです。',
  },
  {
    question: '相談はオンラインでも可能ですか？',
    answer:
      'はい、Zoom等を使ったオンライン相談が可能です。全国どこからでもご相談いただけます。もちろん、対面での相談をご希望の場合も対応可能です。',
  },
  {
    question: 'どのくらいの規模の会社が対象ですか？',
    answer:
      '従業員数に関わらず、ご相談いただけます。個人事業主の方から、従業員100名以上の企業まで、幅広くサポートしています。業務改善は規模に関わらず効果があります。',
  },
  {
    question: '具体的にどんな相談ができますか？',
    answer:
      '請求書作成の自動化、顧客対応の効率化、スケジュール調整の自動化、在庫管理の改善など、日々の業務で「時間がかかっている」「ミスが多い」と感じる部分について、ご相談いただけます。',
  },
  {
    question: '相談から導入までどのくらい時間がかかりますか？',
    answer:
      '内容によりますが、簡単な改善であれば1〜2週間、システム構築が必要な場合は1〜3ヶ月程度です。まずは無料相談で、スケジュール感も含めてご説明します。',
  },
]

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index)
  }

  return (
    <section id="faq" className="section-container bg-white">
      <div className="text-center mb-16">
        <h2 className="section-heading">
          <span className="gradient-text">よくある質問</span>
        </h2>
        <p className="section-subheading">
          無料相談について、よくいただく質問にお答えします
        </p>
      </div>

      <div className="max-w-3xl mx-auto space-y-4">
        {faqs.map((faq, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg overflow-hidden hover:border-primary-300 transition-colors animate-fade-in"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <button
              onClick={() => toggleFAQ(index)}
              className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors"
            >
              <span className="font-semibold text-gray-900 pr-4">
                {faq.question}
              </span>
              <ChevronDown
                className={`w-5 h-5 text-primary-600 flex-shrink-0 transition-transform duration-300 ${
                  openIndex === index ? 'rotate-180' : ''
                }`}
              />
            </button>

            <div
              className={`overflow-hidden transition-all duration-300 ${
                openIndex === index ? 'max-h-96' : 'max-h-0'
              }`}
            >
              <div className="px-6 pb-6 text-gray-600 leading-relaxed">
                {faq.answer}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center">
        <p className="text-gray-600 mb-4">
          その他のご質問がある方は、お気軽にお問い合わせください
        </p>
        <a href="#contact" className="btn-primary">
          無料相談する
        </a>
      </div>
    </section>
  )
}
