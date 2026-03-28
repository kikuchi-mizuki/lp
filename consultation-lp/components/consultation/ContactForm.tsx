'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Send, CheckCircle } from 'lucide-react'
import type { ConsultationFormData } from '@/types'

const schema = z.object({
  company_name: z.string().min(1, '会社名または屋号を入力してください'),
  name: z.string().min(1, 'お名前を入力してください'),
  email: z.string().email('有効なメールアドレスを入力してください'),
  phone: z.string().optional(),
  inquiry: z.string().min(10, '相談内容は10文字以上で入力してください'),
})

export default function ContactForm() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ConsultationFormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: ConsultationFormData) => {
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/consultation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (response.ok) {
        setIsSuccess(true)
        reset()
      } else {
        alert('送信に失敗しました。もう一度お試しください。')
      }
    } catch (error) {
      console.error('Error submitting form:', error)
      alert('送信に失敗しました。もう一度お試しください。')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isSuccess) {
    return (
      <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 max-w-2xl mx-auto text-center animate-scale-in">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-2xl font-bold mb-4 text-gray-900">
          お問い合わせありがとうございます
        </h3>
        <p className="text-gray-600 mb-6 leading-relaxed">
          ご相談内容を確認次第、担当者より2営業日以内にご連絡いたします。
          <br />
          まずは現状を整理するところから始めましょう。
        </p>
        <button
          onClick={() => setIsSuccess(false)}
          className="btn-secondary"
        >
          もう一度相談する
        </button>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h3 className="text-2xl md:text-3xl font-bold mb-3">
          無料相談<span className="gradient-text">お申し込み</span>
        </h3>
        <p className="text-gray-600">
          以下のフォームよりお気軽にご相談ください
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* 会社名 */}
        <div>
          <label htmlFor="company_name" className="label">
            会社名または屋号 <span className="text-red-500">*</span>
          </label>
          <input
            id="company_name"
            type="text"
            className={errors.company_name ? 'input-error' : 'input'}
            placeholder="株式会社サンプル"
            {...register('company_name')}
          />
          {errors.company_name && (
            <p className="error-message">{errors.company_name.message}</p>
          )}
        </div>

        {/* お名前 */}
        <div>
          <label htmlFor="name" className="label">
            お名前 <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            type="text"
            className={errors.name ? 'input-error' : 'input'}
            placeholder="山田太郎"
            {...register('name')}
          />
          {errors.name && (
            <p className="error-message">{errors.name.message}</p>
          )}
        </div>

        {/* メールアドレス */}
        <div>
          <label htmlFor="email" className="label">
            メールアドレス <span className="text-red-500">*</span>
          </label>
          <input
            id="email"
            type="email"
            className={errors.email ? 'input-error' : 'input'}
            placeholder="example@company.com"
            {...register('email')}
          />
          {errors.email && (
            <p className="error-message">{errors.email.message}</p>
          )}
        </div>

        {/* 電話番号 */}
        <div>
          <label htmlFor="phone" className="label">
            電話番号（任意）
          </label>
          <input
            id="phone"
            type="tel"
            className="input"
            placeholder="03-1234-5678"
            {...register('phone')}
          />
        </div>

        {/* 相談内容 */}
        <div>
          <label htmlFor="inquiry" className="label">
            相談内容 <span className="text-red-500">*</span>
          </label>
          <textarea
            id="inquiry"
            rows={6}
            className={errors.inquiry ? 'input-error textarea' : 'textarea'}
            placeholder="現在の課題や相談したい内容をご記入ください&#10;&#10;例：&#10;・請求書作成に毎月50時間かかっており、自動化したい&#10;・顧客対応に追われて本来の業務ができない&#10;・スケジュール調整に時間がかかりすぎている"
            {...register('inquiry')}
          />
          {errors.inquiry && (
            <p className="error-message">{errors.inquiry.message}</p>
          )}
        </div>

        {/* プライバシー */}
        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
          <p className="mb-2">
            ※ ご入力いただいた個人情報は、お問い合わせ対応のみに使用いたします。
          </p>
          <p>
            ※ 無理な営業は一切行いませんので、安心してご相談ください。
          </p>
        </div>

        {/* 送信ボタン */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full btn-primary-large disabled:opacity-50 disabled:cursor-not-allowed group"
        >
          {isSubmitting ? (
            '送信中...'
          ) : (
            <>
              無料相談を申し込む
              <Send className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </button>
      </form>
    </div>
  )
}
