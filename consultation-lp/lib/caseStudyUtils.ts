import type { CaseData } from '@/lib/googleSheets'

/** 公開パス・URLをブラウザが正しく解決できる形にする（先頭スラッシュ忘れ・BOM対策） */
export function normalizeMediaUrl(raw: string | undefined | null): string {
  if (raw == null) return ''
  const u = raw.trim().replace(/^\uFEFF/, '')
  if (!u) return ''
  if (/^https?:\/\//i.test(u)) return u
  if (u.startsWith('//')) return `https:${u}`
  const path = u.replace(/^\.+\//, '').replace(/^\.\//, '')
  if (path.startsWith('/')) return path
  return `/${path}`
}

/** 数値列に画像URLが誤って入っているときの検出用 */
export function looksLikeImageUrl(s: string): boolean {
  const t = s.trim().toLowerCase()
  if (!t) return false
  if (/^https?:\/\//i.test(t) && /\.(jpg|jpeg|png|gif|webp|svg)(\?|#|$)/i.test(t)) return true
  if (t.startsWith('/') && /\.(jpg|jpeg|png|gif|webp|svg)(\?|#|$)/i.test(t)) return true
  return false
}

/** サムネ・動画URLの正規化と、列ずれした画像URLの救済 */
export function postProcessCaseMedia(c: CaseData): CaseData {
  let thumbnailUrl = normalizeMediaUrl(c.thumbnailUrl)
  let videoUrl = normalizeMediaUrl(c.videoUrl)
  let numericResult = (c.numericResult || '').trim()

  if (!thumbnailUrl && looksLikeImageUrl(numericResult)) {
    thumbnailUrl = normalizeMediaUrl(numericResult)
    numericResult = ''
  }

  return {
    ...c,
    thumbnailUrl: thumbnailUrl || undefined,
    videoUrl: videoUrl || undefined,
    numericResult,
  }
}

/** 表示用の数値・ビフォーアフター強調（numeric_result 優先、なければ result から推定） */
export function getCaseMetricHighlight(c: CaseData): { headline: string; sub?: string } {
  const raw = (c.numericResult || '').trim()
  if (raw && looksLikeImageUrl(raw)) {
    // 誤配置のURLは見出しに使わない（postProcess で救済済みでも念のため）
  } else if (raw) {
    const arrow = raw.match(/(.+?)(→|⇒|->)(.+)/)
    if (arrow) {
      return {
        headline: `${arrow[1].trim()} → ${arrow[3].trim()}`,
        sub: c.result?.trim() || undefined,
      }
    }
    return { headline: raw, sub: c.result?.trim() || undefined }
  }
  const fromResult = c.result?.match(
    /(\d+(?:\.\d+)?\s*(?:時間|分|日|件|%|％|人|円)[^。]*?(?:→|⇒)\s*[^。]+)/u
  )
  if (fromResult) {
    return { headline: fromResult[1].trim(), sub: c.result?.trim() }
  }
  const pct = c.result?.match(/(\d+(?:\.\d+)?%[^。]{0,40})/u)
  if (pct) {
    return { headline: pct[1].trim(), sub: c.result?.trim() }
  }
  if (c.result?.trim()) {
    const short = c.result.trim().slice(0, 56)
    return { headline: short + (c.result.length > 56 ? '…' : ''), sub: undefined }
  }
  return { headline: '成果を実現', sub: undefined }
}

export function parseTagsCell(cell: string | undefined): string[] {
  if (!cell?.trim()) return []
  return cell
    .split(/[,、;；\n]/)
    .map((t) => t.trim())
    .filter(Boolean)
}

export function parseBoolCell(v: string | undefined, defaultVal: boolean): boolean {
  if (v == null || v.trim() === '') return defaultVal
  const s = v.trim().toLowerCase()
  if (['true', '1', 'yes', 'y', 'はい', '公開', 'featured', '○', '✓'].includes(s)) return true
  if (['false', '0', 'no', 'n', 'いいえ', '非公開', '×'].includes(s)) return false
  return defaultVal
}

export function parseSortOrder(v: string | undefined, fallback: number): number {
  if (v == null || v.trim() === '') return fallback
  const n = parseInt(v.trim(), 10)
  return Number.isFinite(n) ? n : fallback
}

/** API / クライアント共通: メディアURL正規化 → 公開のみ・おすすめ優先・sort_order */
export function prepareCasesForDisplay(cases: CaseData[]): CaseData[] {
  const processed = cases.map(postProcessCaseMedia)
  return processed
    .filter((c) => c.isPublished !== false)
    .sort((a, b) => {
      const af = a.isFeatured === true ? 1 : 0
      const bf = b.isFeatured === true ? 1 : 0
      if (bf !== af) return bf - af
      const ao = a.sortOrder ?? 9999
      const bo = b.sortOrder ?? 9999
      if (ao !== bo) return ao - bo
      return (a.title || '').localeCompare(b.title || '', 'ja')
    })
}

export function collectIndustries(cases: CaseData[]): string[] {
  const set = new Set<string>()
  for (const c of cases) {
    const ind = (c.industry || '').trim()
    if (ind) set.add(ind)
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
}

export function collectAllTags(cases: CaseData[]): string[] {
  const set = new Set<string>()
  for (const c of cases) {
    for (const t of c.tags || []) {
      if (t.trim()) set.add(t.trim())
    }
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
}

export function caseMatchesFilters(
  c: CaseData,
  industry: string | null,
  tag: string | null
): boolean {
  if (industry && (c.industry || '').trim() !== industry) return false
  if (tag && !(c.tags || []).map((t) => t.trim()).includes(tag)) return false
  return true
}
