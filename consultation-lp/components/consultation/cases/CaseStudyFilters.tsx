'use client'

type Props = {
  industries: string[]
  tags: string[]
  industry: string | null
  tag: string | null
  onIndustry: (v: string | null) => void
  onTag: (v: string | null) => void
  resultCount: number
}

export default function CaseStudyFilters({
  industries,
  tags,
  industry,
  tag,
  onIndustry,
  onTag,
  resultCount,
}: Props) {
  const chipBase =
    'rounded-full border px-3 py-1.5 text-sm font-semibold transition-all duration-200 md:px-4 md:py-2'

  return (
    <div className="mx-auto mb-10 max-w-4xl space-y-6">
      <p className="text-center text-sm text-[var(--text-gray)]">
        業種やタグで絞り込み、自分に近い事例からイメージできます（該当{' '}
        <span className="font-bold text-[var(--primary-color)]">{resultCount}</span> 件）
      </p>

      {industries.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--text-light)]">業種</p>
          <div className="flex flex-wrap justify-center gap-2">
            <button
              type="button"
              className={`${chipBase} ${
                industry == null
                  ? 'border-[var(--primary-color)] bg-[var(--primary-light)] text-[var(--primary-dark)]'
                  : 'border-[var(--border-light)] bg-white text-[var(--text-gray)] hover:border-primary-300'
              }`}
              onClick={() => onIndustry(null)}
            >
              すべて
            </button>
            {industries.map((ind) => (
              <button
                key={ind}
                type="button"
                className={`${chipBase} ${
                  industry === ind
                    ? 'border-[var(--primary-color)] bg-[var(--primary-light)] text-[var(--primary-dark)]'
                    : 'border-[var(--border-light)] bg-white text-[var(--text-gray)] hover:border-primary-300'
                }`}
                onClick={() => onIndustry(industry === ind ? null : ind)}
              >
                {ind}
              </button>
            ))}
          </div>
        </div>
      )}

      {tags.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--text-light)]">タグ</p>
          <div className="flex flex-wrap justify-center gap-2">
            <button
              type="button"
              className={`${chipBase} ${
                tag == null
                  ? 'border-[var(--primary-color)] bg-[var(--primary-light)] text-[var(--primary-dark)]'
                  : 'border-[var(--border-light)] bg-white text-[var(--text-gray)] hover:border-primary-300'
              }`}
              onClick={() => onTag(null)}
            >
              すべて
            </button>
            {tags.map((t) => (
              <button
                key={t}
                type="button"
                className={`${chipBase} ${
                  tag === t
                    ? 'border-[var(--primary-color)] bg-[var(--primary-light)] text-[var(--primary-dark)]'
                    : 'border-[var(--border-light)] bg-white text-[var(--text-gray)] hover:border-primary-300'
                }`}
                onClick={() => onTag(tag === t ? null : t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
