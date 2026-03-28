'use client'

import { X, Play } from 'lucide-react'
import type { CaseData } from '@/lib/googleSheets'
import { getCaseMetricHighlight } from '@/lib/caseStudyUtils'

type Props = {
  selectedCase: CaseData
  onClose: () => void
}

function VideoEmbed({ videoUrl }: { videoUrl: string }) {
  if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
    let videoId = ''
    if (videoUrl.includes('youtube.com/watch?v=')) {
      videoId = videoUrl.split('v=')[1]?.split('&')[0] || ''
    } else if (videoUrl.includes('youtu.be/')) {
      videoId = videoUrl.split('youtu.be/')[1]?.split('?')[0] || ''
    } else if (videoUrl.includes('youtube.com/embed/')) {
      videoId = videoUrl.split('embed/')[1]?.split('?')[0] || ''
    }

    if (videoId) {
      return (
        <iframe
          width="100%"
          height="100%"
          src={`https://www.youtube.com/embed/${videoId}`}
          title="YouTube video"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="absolute inset-0 h-full w-full"
        />
      )
    }
  }

  if (videoUrl.includes('vimeo.com')) {
    const videoId = videoUrl.split('vimeo.com/')[1]?.split('?')[0] || ''
    if (videoId) {
      return (
        <iframe
          src={`https://player.vimeo.com/video/${videoId}`}
          width="100%"
          height="100%"
          frameBorder="0"
          allow="autoplay; fullscreen; picture-in-picture"
          allowFullScreen
          className="absolute inset-0 h-full w-full"
        />
      )
    }
  }

  if (videoUrl.match(/\.(mp4|webm|ogg)$/i)) {
    return (
      <video controls className="h-full w-full object-contain">
        <source src={videoUrl} type={`video/${videoUrl.split('.').pop()}`} />
        お使いのブラウザは動画タグに対応していません。
      </video>
    )
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
      <a
        href={videoUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex flex-col items-center text-white hover:text-gray-300"
      >
        <Play className="mb-2 h-16 w-16" />
        <span className="text-sm">動画を見る</span>
      </a>
    </div>
  )
}

export default function CaseStudyDetailModal({ selectedCase, onClose }: Props) {
  const { headline, sub } = getCaseMetricHighlight(selectedCase)
  const industry = (selectedCase.industry || '').trim()

  return (
    <div
      className="animate-fade-in fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="animate-scale-in max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-[var(--radius-large)] bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="case-detail-title"
      >
        <div
          className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-[var(--border-light)] bg-white/95 p-5 backdrop-blur-sm md:p-6"
        >
          <div className="min-w-0 flex-1">
            {industry && (
              <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[var(--primary-color)]">
                {industry}
              </p>
            )}
            <p className="mb-1 text-sm font-semibold text-[var(--text-gray)]">{selectedCase.target}</p>
            <h2 id="case-detail-title" className="text-xl font-bold text-[var(--text-dark)] md:text-2xl">
              {selectedCase.title}
            </h2>
            <div className="mt-4 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 ring-1 ring-blue-100">
              <p className="text-center text-xl font-extrabold text-[var(--primary-dark)] md:text-2xl">{headline}</p>
              {sub && sub !== headline && (
                <p className="mt-1 text-center text-sm text-[var(--text-gray)]">{sub}</p>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg p-2 transition-colors hover:bg-gray-100"
            aria-label="閉じる"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-6 p-5 md:p-6">
          {selectedCase.videoUrl && (
            <div
              className="relative w-full overflow-hidden rounded-[var(--radius-medium)] bg-gray-900"
              style={{ aspectRatio: '16/9' }}
            >
              <VideoEmbed videoUrl={selectedCase.videoUrl} />
            </div>
          )}

          {selectedCase.tags && selectedCase.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedCase.tags.map((tag) => (
                <span key={tag} className="badge-primary">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {selectedCase.catchCopy && (
            <div
              className="rounded-[var(--radius-medium)] p-5"
              style={{
                background: 'linear-gradient(90deg, var(--primary-light), var(--accent-light))',
              }}
            >
              <p className="text-lg font-semibold text-[var(--text-dark)]">{selectedCase.catchCopy}</p>
            </div>
          )}

          {selectedCase.beforeProblem && (
            <section>
              <h3 className="mb-3 flex items-center text-lg font-bold">
                <span className="mr-2 h-6 w-1.5 rounded-full bg-red-500" />
                導入前の悩み
              </h3>
              <p className="rounded-[var(--radius-small)] bg-[var(--background-light)] p-4 leading-relaxed text-[var(--text-gray)]">
                {selectedCase.beforeProblem}
              </p>
            </section>
          )}

          {selectedCase.solution && (
            <section>
              <h3 className="mb-3 flex items-center text-lg font-bold">
                <span className="mr-2 h-6 w-1.5 rounded-full bg-[var(--accent-color)]" />
                改善内容
              </h3>
              <p className="rounded-[var(--radius-small)] bg-[var(--background-light)] p-4 leading-relaxed text-[var(--text-gray)]">
                {selectedCase.solution}
              </p>
            </section>
          )}

          {selectedCase.result && (
            <section>
              <h3 className="mb-3 flex items-center text-lg font-bold">
                <span className="mr-2 h-6 w-1.5 rounded-full bg-emerald-500" />
                成果
              </h3>
              <div className="rounded-[var(--radius-medium)] border-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-blue-50 p-5">
                <p className="font-semibold leading-relaxed text-[var(--text-dark)]">{selectedCase.result}</p>
              </div>
            </section>
          )}

          {selectedCase.detailText && (
            <section>
              <h3 className="mb-3 text-lg font-bold">詳細説明</h3>
              <p className="whitespace-pre-wrap rounded-[var(--radius-small)] bg-[var(--background-light)] p-4 leading-relaxed text-[var(--text-gray)]">
                {selectedCase.detailText}
              </p>
            </section>
          )}

          <div
            className="rounded-[var(--radius-medium)] p-8 text-center text-white"
            style={{
              background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%)',
            }}
          >
            <p className="mb-2 text-xl font-bold">同じように、自社の優先順位を整理できます</p>
            <p className="mb-6 text-sm opacity-95">
              事例と近い課題かどうかは問いません。無料相談で現状を一緒に整理しましょう。
            </p>
            <a
              href="#contact"
              onClick={onClose}
              className="inline-block rounded-[var(--radius-small)] bg-white px-10 py-4 text-base font-bold text-[var(--primary-color)] shadow-lg transition-transform hover:scale-[1.02]"
            >
              無料で相談する
            </a>
            <p className="mt-4 text-xs opacity-90">無理な営業は一切ありません</p>
          </div>
        </div>
      </div>
    </div>
  )
}
