'use client'

import { useEffect, useMemo, useState } from 'react'
import type { CaseData } from '@/lib/googleSheets'
import {
  caseMatchesFilters,
  collectAllTags,
  collectIndustries,
} from '@/lib/caseStudyUtils'
import CaseStudyCard from '@/components/consultation/cases/CaseStudyCard'
import CaseStudyDetailModal from '@/components/consultation/cases/CaseStudyDetailModal'
import CaseStudyFilters from '@/components/consultation/cases/CaseStudyFilters'

export default function CasesSection() {
  const [cases, setCases] = useState<CaseData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCase, setSelectedCase] = useState<CaseData | null>(null)
  const [industry, setIndustry] = useState<string | null>(null)
  const [tag, setTag] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()

    const fetchDeadlineMs = 16_000
    const abortTimer = window.setTimeout(() => controller.abort(), fetchDeadlineMs)

    /** fetch 完了後も response.json() が止まることがあるため別タイムアウト */
    const jsonTimeoutMs = 10_000
    async function readJsonBody(response: Response): Promise<unknown> {
      return Promise.race([
        response.json(),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('response.json timeout')), jsonTimeoutMs)
        ),
      ])
    }

    /** いずれの経路でも最終的にスピナーを止める */
    const watchdogMs = 22_000
    const watchdog = window.setTimeout(() => {
      if (cancelled) return
      setLoading(false)
      setError(
        '読み込みが完了しませんでした。通信環境を確認し、ページを再読み込みするか、しばらくしてからお試しください。'
      )
    }, watchdogMs)

    async function fetchCases() {
      try {
        const base = typeof window !== 'undefined' ? window.location.origin : ''
        const response = await fetch(`${base}/api/cases`, {
          signal: controller.signal,
          cache: 'no-store',
          headers: { Accept: 'application/json' },
        })
        window.clearTimeout(abortTimer)

        if (cancelled) return

        if (!response.ok) {
          setError('導入事例の取得に失敗しました（サーバーエラー）')
          return
        }

        const data = (await readJsonBody(response)) as {
          success?: boolean
          cases?: CaseData[]
          degraded?: boolean
        }

        if (cancelled) return

        if (data.success && Array.isArray(data.cases)) {
          setCases(data.cases)
          setError(null)
        } else {
          setError('導入事例の取得に失敗しました')
        }
      } catch (err) {
        window.clearTimeout(abortTimer)
        if (cancelled) return
        console.error('Error fetching cases:', err)
        if (err instanceof Error && err.name === 'AbortError') {
          setError(
            '接続がタイムアウトしました。開発サーバーが起動しているか、ネットワークをご確認ください。'
          )
        } else if (err instanceof Error && err.message === 'response.json timeout') {
          setError('サーバーからの応答の解析に失敗しました。再読み込みしてください。')
        } else {
          setError('導入事例の取得に失敗しました')
        }
      } finally {
        window.clearTimeout(watchdog)
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchCases()

    return () => {
      cancelled = true
      window.clearTimeout(abortTimer)
      window.clearTimeout(watchdog)
      controller.abort()
    }
  }, [])

  const industries = useMemo(() => collectIndustries(cases), [cases])
  const allTags = useMemo(() => collectAllTags(cases), [cases])

  const filtered = useMemo(
    () => cases.filter((c) => caseMatchesFilters(c, industry, tag)),
    [cases, industry, tag]
  )

  if (loading) {
    return (
      <section id="cases" className="section-container" style={{ background: 'var(--background-light)' }}>
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-primary-600" />
          <p style={{ marginTop: '1rem', color: 'var(--text-gray)' }}>導入事例を読み込み中...</p>
        </div>
      </section>
    )
  }

  if (error || cases.length === 0) {
    return (
      <section id="cases" className="section-container" style={{ background: 'var(--background-light)' }}>
        <h2 className="section-heading">
          <span className="gradient-text">導入事例</span>
        </h2>
        <div className="text-center mt-8">
          <p style={{ color: 'var(--text-gray)' }}>{error || '現在表示できる導入事例がありません'}</p>
        </div>
      </section>
    )
  }

  return (
    <>
      <section id="cases" className="section-container" style={{ background: 'var(--background-light)' }}>
        <h2 className="section-heading">
          <span className="gradient-text">導入事例</span>
        </h2>

        {(industries.length > 0 || allTags.length > 0) && (
          <CaseStudyFilters
            industries={industries}
            tags={allTags}
            industry={industry}
            tag={tag}
            onIndustry={setIndustry}
            onTag={setTag}
            resultCount={filtered.length}
          />
        )}

        {filtered.length === 0 ? (
          <p className="text-center text-[var(--text-gray)]">
            条件に合う事例がありません。フィルターを外して再度お試しください。
          </p>
        ) : (
          <div
            className="grid gap-8"
            style={{
              gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))',
            }}
          >
            {filtered.map((caseItem, index) => (
              <CaseStudyCard key={caseItem.id} caseItem={caseItem} onOpen={setSelectedCase} index={index} />
            ))}
          </div>
        )}

        <p className="mx-auto mt-12 max-w-2xl text-center text-sm leading-relaxed text-[var(--text-gray)]">
          事例はスプレッドシート連携で随時追加できます。公開件数が増えるほど、業種・タグの組み合わせで「自分ごと化」しやすくなります。
        </p>
      </section>

      {selectedCase && (
        <CaseStudyDetailModal selectedCase={selectedCase} onClose={() => setSelectedCase(null)} />
      )}
    </>
  )
}
