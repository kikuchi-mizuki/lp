'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { X } from 'lucide-react'
import { createBrowserClient } from '@/lib/supabase/client'
import type { Case, CaseInsert, CaseUpdate } from '@/types'

interface CaseFormProps {
  caseData?: Case | null
  onClose: () => void
}

export default function CaseForm({ caseData, onClose }: CaseFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [tags, setTags] = useState<string>('')

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<CaseInsert>({
    defaultValues: caseData
      ? {
          ...caseData,
          tags: caseData.tags || [],
        }
      : {
          sort_order: 0,
          is_published: false,
          tags: [],
        },
  })

  const supabase = createBrowserClient()

  useEffect(() => {
    if (caseData) {
      setTags((caseData.tags || []).join(', '))
    }
  }, [caseData])

  const onSubmit = async (data: CaseInsert) => {
    setIsSubmitting(true)

    try {
      // タグを配列に変換
      const tagsArray = tags
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0)

      const formData = {
        ...data,
        tags: tagsArray,
      }

      let error

      if (caseData) {
        // 更新
        const result = await supabase
          .from('cases')
          .update(formData as CaseUpdate)
          .eq('id', caseData.id)
        error = result.error
      } else {
        // 新規作成
        const result = await supabase.from('cases').insert([formData])
        error = result.error
      }

      if (error) {
        console.error('Error saving case:', error)
        alert('保存に失敗しました')
      } else {
        onClose()
      }
    } catch (error) {
      console.error('Error:', error)
      alert('エラーが発生しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 animate-fade-in overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl max-w-4xl w-full my-8 animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-2xl font-bold">
            {caseData ? '事例を編集' : '新規事例を作成'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* タイトル */}
          <div>
            <label className="label">
              タイトル <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className={errors.title ? 'input-error' : 'input'}
              placeholder="請求書作成を90%自動化"
              {...register('title', { required: 'タイトルは必須です' })}
            />
            {errors.title && (
              <p className="error-message">{errors.title.message}</p>
            )}
          </div>

          {/* ターゲット */}
          <div>
            <label className="label">
              ターゲット <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className={errors.target ? 'input-error' : 'input'}
              placeholder="経理部門2名の小規模EC事業者"
              {...register('target', { required: 'ターゲットは必須です' })}
            />
            {errors.target && (
              <p className="error-message">{errors.target.message}</p>
            )}
          </div>

          {/* キャッチコピー */}
          <div>
            <label className="label">
              キャッチコピー <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className={errors.catch_copy ? 'input-error' : 'input'}
              placeholder="月100時間かかっていた請求書作成が、わずか10時間に"
              {...register('catch_copy', {
                required: 'キャッチコピーは必須です',
              })}
            />
            {errors.catch_copy && (
              <p className="error-message">{errors.catch_copy.message}</p>
            )}
          </div>

          {/* 導入前の悩み */}
          <div>
            <label className="label">
              導入前の悩み <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={4}
              className={errors.before_problem ? 'input-error textarea' : 'textarea'}
              placeholder="毎月の請求書作成に100時間以上を費やし..."
              {...register('before_problem', {
                required: '導入前の悩みは必須です',
              })}
            />
            {errors.before_problem && (
              <p className="error-message">{errors.before_problem.message}</p>
            )}
          </div>

          {/* 改善内容 */}
          <div>
            <label className="label">
              改善内容 <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={4}
              className={errors.solution ? 'input-error textarea' : 'textarea'}
              placeholder="AI-OCRとRPAを組み合わせた自動請求書生成システムを導入..."
              {...register('solution', { required: '改善内容は必須です' })}
            />
            {errors.solution && (
              <p className="error-message">{errors.solution.message}</p>
            )}
          </div>

          {/* 成果 */}
          <div>
            <label className="label">
              成果 <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={4}
              className={errors.result ? 'input-error textarea' : 'textarea'}
              placeholder="請求書作成時間を90%削減（100時間→10時間）..."
              {...register('result', { required: '成果は必須です' })}
            />
            {errors.result && (
              <p className="error-message">{errors.result.message}</p>
            )}
          </div>

          {/* 詳細説明 */}
          <div>
            <label className="label">詳細説明（任意）</label>
            <textarea
              rows={6}
              className="textarea"
              placeholder="システム導入前は、ExcelとWordで1件ずつ請求書を作成していました..."
              {...register('detail_text')}
            />
          </div>

          {/* サムネイルURL */}
          <div>
            <label className="label">サムネイルURL（任意）</label>
            <input
              type="text"
              className="input"
              placeholder="/images/cases/case-invoice.jpg"
              {...register('thumbnail_url')}
            />
          </div>

          {/* 動画URL */}
          <div>
            <label className="label">動画URL（任意）</label>
            <input
              type="text"
              className="input"
              placeholder="https://www.youtube.com/watch?v=..."
              {...register('video_url')}
            />
          </div>

          {/* タグ */}
          <div>
            <label className="label">タグ（カンマ区切り）</label>
            <input
              type="text"
              className="input"
              placeholder="自動化, RPA, AI-OCR, 経理業務"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
            <p className="text-sm text-gray-500 mt-1">
              カンマで区切って複数入力できます
            </p>
          </div>

          {/* 並び順 */}
          <div>
            <label className="label">
              並び順 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              className={errors.sort_order ? 'input-error' : 'input'}
              defaultValue={0}
              {...register('sort_order', {
                required: '並び順は必須です',
                valueAsNumber: true,
              })}
            />
            <p className="text-sm text-gray-500 mt-1">
              数字が小さいほど上に表示されます
            </p>
          </div>

          {/* 公開設定 */}
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                {...register('is_published')}
              />
              <span className="font-semibold text-gray-700">公開する</span>
            </label>
            <p className="text-sm text-gray-500 mt-1">
              チェックを入れると、LPに表示されます
            </p>
          </div>

          {/* ボタン */}
          <div className="flex gap-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn-secondary"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 btn-primary disabled:opacity-50"
            >
              {isSubmitting ? '保存中...' : caseData ? '更新する' : '作成する'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
