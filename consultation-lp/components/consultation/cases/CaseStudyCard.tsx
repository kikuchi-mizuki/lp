'use client'

import { useRef, useState } from 'react'
import { Sparkles, ExternalLink, Play } from 'lucide-react'
import type { CaseData } from '@/lib/googleSheets'
import { getCaseMetricHighlight, normalizeMediaUrl } from '@/lib/caseStudyUtils'

type Props = {
  caseItem: CaseData
  onOpen: (c: CaseData) => void
  index: number
}

function Thumbnail({ src }: { src: string }) {
  const normalized = normalizeMediaUrl(src)
  const [failed, setFailed] = useState(false)

  if (!normalized || failed) {
    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 bg-gradient-to-br from-slate-100 to-blue-50 px-4 text-center">
        <span className="text-xs font-medium text-slate-400">画像を表示できません</span>
        <span className="line-clamp-2 text-[10px] leading-tight text-slate-300">URL・パスをご確認ください</span>
      </div>
    )
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={normalized}
      alt=""
      className="absolute inset-0 h-full w-full object-cover"
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  )
}

function YoutubeThumb({ videoId }: { videoId: string }) {
  const triedFallback = useRef(false)
  const [src, setSrc] = useState(`https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`)

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt=""
      className="absolute inset-0 h-full w-full object-cover"
      loading="lazy"
      decoding="async"
      onError={() => {
        if (!triedFallback.current) {
          triedFallback.current = true
          setSrc(`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`)
        }
      }}
    />
  )
}

function VideoPreview({ videoUrl }: { videoUrl: string }) {
  if (videoUrl.match(/\.(mp4|webm|ogg)$/i)) {
    return (
      <video
        className="absolute inset-0 h-full w-full object-cover"
        muted
        loop
        playsInline
        preload="metadata"
      >
        <source src={normalizeMediaUrl(videoUrl)} type={`video/${videoUrl.split('.').pop()}`} />
      </video>
    )
  }

  if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
    let videoId = ''
    if (videoUrl.includes('youtube.com/watch?v=')) {
      videoId = videoUrl.split('v=')[1]?.split('&')[0] || ''
    } else if (videoUrl.includes('youtu.be/')) {
      videoId = videoUrl.split('youtu.be/')[1]?.split('?')[0] || ''
    }

    if (videoId) {
      return <YoutubeThumb videoId={videoId} />
    }
  }

  return (
    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-slate-800 to-blue-900 text-white">
      <Play className="h-16 w-16 opacity-50" />
    </div>
  )
}

export default function CaseStudyCard({ caseItem, onOpen, index }: Props) {
  const { headline, sub } = getCaseMetricHighlight(caseItem)
  const industryLabel = (caseItem.industry || '').trim() || caseItem.target.split(/[・｜|]/)[0]?.trim() || '事例'

  return (
    <article
      className="card-hover animate-fade-in flex h-full cursor-pointer flex-col overflow-hidden rounded-[var(--radius-medium)] border border-[var(--border-light)] bg-[var(--background-white)] shadow-[var(--shadow-card)] transition-shadow hover:shadow-[var(--shadow-medium)]"
      style={{ animationDelay: `${index * 70}ms` }}
      onClick={() => onOpen(caseItem)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onOpen(caseItem)
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-gradient-to-br from-slate-100 to-blue-50">
        {caseItem.thumbnailUrl ? (
          <Thumbnail src={caseItem.thumbnailUrl} />
        ) : caseItem.videoUrl ? (
          <VideoPreview videoUrl={caseItem.videoUrl} />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm font-medium text-slate-400">
            導入事例
          </div>
        )}
        {caseItem.isFeatured && (
          <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/95 px-2.5 py-1 text-xs font-bold text-[var(--primary-color)] shadow-sm backdrop-blur-sm">
            <Sparkles className="h-3.5 w-3.5" aria-hidden />
            おすすめ
          </span>
        )}
        {caseItem.videoUrl && (
          <>
            <div className="absolute right-3 top-3 flex items-center gap-1 rounded-full bg-red-600 px-2.5 py-1 text-xs font-bold text-white shadow-md">
              <Play className="h-3 w-3 fill-white" aria-hidden />
              動画
            </div>
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 transition-opacity hover:opacity-100">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/95 shadow-xl backdrop-blur-sm">
                <Play className="h-8 w-8 fill-[var(--primary-color)] text-[var(--primary-color)]" aria-hidden />
              </div>
            </div>
          </>
        )}
        <span className="absolute bottom-3 left-3 rounded-full bg-[var(--primary-color)] px-3 py-1 text-xs font-bold text-white shadow-md">
          {industryLabel}
        </span>
      </div>

      <div className="flex flex-1 flex-col p-5">
        <div className="mb-3 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 ring-1 ring-blue-100/80">
          <p className="text-center text-lg font-extrabold tracking-tight text-[var(--primary-dark)] md:text-xl">
            {headline}
          </p>
          {sub && sub !== headline && (
            <p className="mt-1 line-clamp-2 text-center text-xs font-medium text-[var(--text-gray)]">{sub}</p>
          )}
        </div>

        <h3 className="mb-2 line-clamp-2 text-lg font-bold leading-snug text-[var(--text-dark)]">
          {caseItem.title}
        </h3>

        {caseItem.catchCopy && (
          <p className="mb-4 line-clamp-2 text-sm leading-relaxed text-[var(--text-gray)]">
            {caseItem.catchCopy}
          </p>
        )}

        {caseItem.tags && caseItem.tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1.5">
            {caseItem.tags.slice(0, 4).map((tag) => (
              <span key={tag} className="badge-primary text-xs font-medium">
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="mt-auto flex items-center justify-between border-t border-[var(--border-light)] pt-4 text-sm font-bold text-[var(--primary-color)]">
          <span className="inline-flex items-center gap-1">
            詳しく見る
            <ExternalLink className="h-4 w-4 opacity-80" aria-hidden />
          </span>
        </div>
      </div>
    </article>
  )
}
