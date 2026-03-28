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
    async function fetchCases() {
      try {
        const response = await fetch('/api/cases')
        const data = await response.json()

        if (data.success) {
          setCases(data.cases)
        } else {
          setError('導入事例の取得に失敗しました')
        }
      } catch (err) {
        console.error('Error fetching cases:', err)
        setError('導入事例の取得に失敗しました')
      } finally {
        setLoading(false)
      }
    }

    fetchCases()
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
        <p className="section-subheading">同じ課題を持つ企業の改善ストーリーをご紹介します</p>
        <div className="text-center">
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
        <p className="section-subheading max-w-2xl mx-auto">
          数字の変化と、導入前の悩みまで見えるので「うちも近いかも」とイメージしやすくなっています。気になる事例から詳細を開いてください。
        </p>

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
