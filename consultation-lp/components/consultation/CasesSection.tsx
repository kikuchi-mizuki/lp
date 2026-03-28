'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { X, Play, ExternalLink } from 'lucide-react'
import type { CaseData } from '@/lib/googleSheets'

export default function CasesSection() {
  const [cases, setCases] = useState<CaseData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCase, setSelectedCase] = useState<CaseData | null>(null)

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

  if (loading) {
    return (
      <section id="cases" className="section-container" style={{ background: 'var(--background-light)' }}>
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
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
        <p className="section-subheading">
          実際の導入事例をご紹介します
        </p>
        <div className="text-center">
          <p style={{ color: 'var(--text-gray)' }}>
            {error || '現在表示できる導入事例がありません'}
          </p>
        </div>
      </section>
    )
  }

  return (
    <>
      <section id="cases" className="section-container" style={{ background: 'var(--background-light)' }}>
        {/* セクションヘッダー */}
        <h2 className="section-heading">
          <span className="gradient-text">導入事例</span>
        </h2>
        <p className="section-subheading">
          実際に業務改善を実現した企業の事例をご紹介します
        </p>

        {/* 事例カードグリッド */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '2rem',
            marginTop: '3rem',
          }}
        >
          {cases.map((caseItem, index) => (
            <div
              key={caseItem.id || index}
              className="card-hover animate-fade-in"
              style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                cursor: 'pointer',
                animationDelay: `${index * 100}ms`,
              }}
              onClick={() => setSelectedCase(caseItem)}
            >
              {/* サムネイル画像 */}
              {caseItem.thumbnailUrl && (
                <div
                  style={{
                    position: 'relative',
                    width: '100%',
                    height: '200px',
                    borderRadius: 'var(--radius-small)',
                    overflow: 'hidden',
                    marginBottom: '1rem',
                    background: '#f0f0f0',
                  }}
                >
                  <Image
                    src={caseItem.thumbnailUrl}
                    alt={caseItem.title}
                    fill
                    style={{ objectFit: 'cover' }}
                  />
                </div>
              )}

              {/* タグ */}
              {caseItem.tags && caseItem.tags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  {caseItem.tags.slice(0, 2).map((tag, idx) => (
                    <span key={idx} className="badge-primary">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* 対象業種・職種 */}
              {caseItem.target && (
                <p
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--primary-color)',
                    fontWeight: 'bold',
                    marginBottom: '0.5rem',
                  }}
                >
                  {caseItem.target}
                </p>
              )}

              {/* タイトル */}
              <h3
                style={{
                  fontSize: '1.25rem',
                  fontWeight: 'bold',
                  color: 'var(--text-dark)',
                  marginBottom: '0.75rem',
                  lineHeight: 1.4,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {caseItem.title}
              </h3>

              {/* キャッチコピー */}
              {caseItem.catchCopy && (
                <p
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--text-gray)',
                    marginBottom: '1rem',
                    lineHeight: 1.7,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {caseItem.catchCopy}
                </p>
              )}

              {/* 結果（ハイライト表示） */}
              {caseItem.result && (
                <div
                  style={{
                    padding: '0.75rem',
                    background: 'var(--primary-light)',
                    borderRadius: 'var(--radius-small)',
                    borderLeft: '4px solid var(--primary-color)',
                    marginTop: 'auto',
                  }}
                >
                  <p
                    style={{
                      fontSize: '0.875rem',
                      color: 'var(--text-dark)',
                      lineHeight: 1.6,
                      fontWeight: 600,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {caseItem.result}
                  </p>
                </div>
              )}

              {/* 詳しく見る */}
              <div
                style={{
                  marginTop: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  color: 'var(--primary-color)',
                  fontWeight: 'bold',
                  fontSize: '0.875rem',
                }}
              >
                詳しく見る
                <ExternalLink style={{ width: '1rem', height: '1rem', marginLeft: '0.25rem' }} />
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div style={{ textAlign: 'center', marginTop: '4rem' }}>
          <p
            style={{
              fontSize: '1.125rem',
              color: 'var(--text-dark)',
              marginBottom: '1.5rem',
              fontWeight: 500,
            }}
          >
            あなたの業務にも同じような改善ができます
          </p>
          <a href="#contact" className="btn-primary-large">
            無料で相談してみる
          </a>
        </div>
      </section>

      {/* 詳細モーダル */}
      {selectedCase && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 animate-fade-in"
          onClick={() => setSelectedCase(null)}
          style={{ zIndex: 9999 }}
        >
          <div
            className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-scale-in"
            onClick={(e) => e.stopPropagation()}
            style={{ borderRadius: 'var(--radius-large)' }}
          >
            {/* ヘッダー */}
            <div
              className="sticky top-0 bg-white p-6 flex items-start justify-between z-10"
              style={{ borderBottom: '1px solid var(--border-light)' }}
            >
              <div className="flex-1">
                {/* タグ */}
                {selectedCase.tags && selectedCase.tags.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    {selectedCase.tags.map((tag, idx) => (
                      <span key={idx} className="badge-primary">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {/* 対象 */}
                <p
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--primary-color)',
                    fontWeight: 'bold',
                    marginBottom: '0.25rem',
                  }}
                >
                  {selectedCase.target}
                </p>
                {/* タイトル */}
                <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--text-dark)' }}>
                  {selectedCase.title}
                </h3>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-4"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* コンテンツ */}
            <div className="p-6 space-y-6">
              {/* 動画 */}
              {selectedCase.videoUrl && (
                <div
                  className="relative w-full bg-gray-900 rounded-lg overflow-hidden"
                  style={{ aspectRatio: '16/9', borderRadius: 'var(--radius-medium)' }}
                >
                  {(() => {
                    const videoUrl = selectedCase.videoUrl

                    // YouTube動画の場合
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
                            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                          />
                        )
                      }
                    }

                    // Vimeo動画の場合
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
                            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                          />
                        )
                      }
                    }

                    // MP4などの動画ファイルの場合
                    if (videoUrl.match(/\.(mp4|webm|ogg)$/i)) {
                      return (
                        <video
                          controls
                          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        >
                          <source src={videoUrl} type={`video/${videoUrl.split('.').pop()}`} />
                          お使いのブラウザは動画タグに対応していません。
                        </video>
                      )
                    }

                    // その他のURL（リンクとして表示）
                    return (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <a
                          href={videoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex flex-col items-center text-white hover:text-gray-300 transition-colors"
                        >
                          <Play className="w-16 h-16 mb-2" />
                          <span className="text-sm">動画を見る</span>
                        </a>
                      </div>
                    )
                  })()}
                </div>
              )}

              {/* キャッチコピー */}
              {selectedCase.catchCopy && (
                <div
                  style={{
                    background: 'linear-gradient(90deg, var(--primary-light), var(--accent-light))',
                    borderRadius: 'var(--radius-medium)',
                    padding: '1.5rem',
                  }}
                >
                  <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-dark)' }}>
                    {selectedCase.catchCopy}
                  </p>
                </div>
              )}

              {/* 導入前の悩み */}
              {selectedCase.beforeProblem && (
                <div>
                  <h4
                    style={{
                      fontSize: '1.125rem',
                      fontWeight: 'bold',
                      marginBottom: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <span
                      style={{
                        width: '0.5rem',
                        height: '1.5rem',
                        background: '#EF4444',
                        borderRadius: '999px',
                        marginRight: '0.5rem',
                      }}
                    />
                    導入前の悩み
                  </h4>
                  <p
                    style={{
                      color: 'var(--text-gray)',
                      lineHeight: 1.7,
                      background: 'var(--background-light)',
                      padding: '1rem',
                      borderRadius: 'var(--radius-small)',
                    }}
                  >
                    {selectedCase.beforeProblem}
                  </p>
                </div>
              )}

              {/* 改善内容 */}
              {selectedCase.solution && (
                <div>
                  <h4
                    style={{
                      fontSize: '1.125rem',
                      fontWeight: 'bold',
                      marginBottom: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <span
                      style={{
                        width: '0.5rem',
                        height: '1.5rem',
                        background: 'var(--accent-color)',
                        borderRadius: '999px',
                        marginRight: '0.5rem',
                      }}
                    />
                    改善内容
                  </h4>
                  <p
                    style={{
                      color: 'var(--text-gray)',
                      lineHeight: 1.7,
                      background: 'var(--background-light)',
                      padding: '1rem',
                      borderRadius: 'var(--radius-small)',
                    }}
                  >
                    {selectedCase.solution}
                  </p>
                </div>
              )}

              {/* 成果 */}
              {selectedCase.result && (
                <div>
                  <h4
                    style={{
                      fontSize: '1.125rem',
                      fontWeight: 'bold',
                      marginBottom: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <span
                      style={{
                        width: '0.5rem',
                        height: '1.5rem',
                        background: '#10B981',
                        borderRadius: '999px',
                        marginRight: '0.5rem',
                      }}
                    />
                    得られた成果
                  </h4>
                  <div
                    style={{
                      background: 'linear-gradient(135deg, #ECFDF5 0%, #DBEAFE 100%)',
                      padding: '1.5rem',
                      borderRadius: 'var(--radius-medium)',
                      border: '2px solid #86EFAC',
                    }}
                  >
                    <p style={{ color: 'var(--text-dark)', fontWeight: 600, lineHeight: 1.7 }}>
                      {selectedCase.result}
                    </p>
                  </div>
                </div>
              )}

              {/* 詳細説明 */}
              {selectedCase.detailText && (
                <div>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '0.75rem' }}>詳細</h4>
                  <p
                    style={{
                      color: 'var(--text-gray)',
                      lineHeight: 1.7,
                      background: 'var(--background-light)',
                      padding: '1rem',
                      borderRadius: 'var(--radius-small)',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {selectedCase.detailText}
                  </p>
                </div>
              )}

              {/* CTA */}
              <div
                style={{
                  background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%)',
                  borderRadius: 'var(--radius-medium)',
                  padding: '2rem',
                  textAlign: 'center',
                  color: 'white',
                }}
              >
                <p style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                  あなたの業務でも改善できることがあります
                </p>
                <p style={{ marginBottom: '1.5rem', opacity: 0.9 }}>
                  まずは無料相談で、現状を整理しましょう
                </p>
                <a
                  href="#contact"
                  onClick={() => setSelectedCase(null)}
                  className="inline-block bg-white px-8 py-4 font-semibold hover:bg-gray-100 transition-colors"
                  style={{
                    color: 'var(--primary-color)',
                    borderRadius: 'var(--radius-small)',
                  }}
                >
                  無料相談する
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
