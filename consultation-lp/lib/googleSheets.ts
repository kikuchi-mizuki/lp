import { google } from 'googleapis'
import {
  parseTagsCell,
  parseBoolCell,
  parseSortOrder,
  prepareCasesForDisplay,
} from '@/lib/caseStudyUtils'

export interface CaseData {
  id: string
  title: string
  target: string
  /** 業種（カード・フィルター用。未設定時は空） */
  industry: string
  catchCopy: string
  beforeProblem: string
  solution: string
  result: string
  /** 数字・ビフォーアフター強調用（例: 3時間→15分、90%削減） */
  numericResult: string
  detailText?: string
  thumbnailUrl?: string
  videoUrl?: string
  tags: string[]
  /** レガシー列の status（active/inactive 等）。新形式では参考用 */
  status: string
  createdAt: string
  isFeatured: boolean
  isPublished: boolean
  sortOrder: number
}

function getGoogleSheetsClient() {
  let privateKey = process.env.GOOGLE_PRIVATE_KEY || ''
  const privateKeyBase64 = process.env.GOOGLE_PRIVATE_KEY_BASE64
  const clientEmail = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL

  if (privateKeyBase64) {
    try {
      privateKey = Buffer.from(privateKeyBase64, 'base64').toString('utf-8')
      privateKey = privateKey.replace(/\\\\n/g, '\n').replace(/\\n/g, '\n')
    } catch (error) {
      console.error('Failed to decode base64 private key:', error)
      return null
    }
  } else {
    privateKey = privateKey.replace(/\\\\n/g, '\n').replace(/\\n/g, '\n')
  }

  if (
    !privateKey ||
    !clientEmail ||
    privateKey.includes('your_private_key_here') ||
    clientEmail.includes('your-service-account')
  ) {
    return null
  }

  try {
    const auth = new google.auth.GoogleAuth({
      credentials: {
        client_email: clientEmail,
        private_key: privateKey,
      },
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    })

    return google.sheets({ version: 'v4', auth })
  } catch (error) {
    console.error('Error initializing Google Sheets client:', error)
    return null
  }
}

function getSampleCases(): CaseData[] {
  return prepareCasesForDisplay([
    {
      id: 'sample-001',
      title: '月次報告書作成を自動化し、3時間を15分に短縮',
      target: '製造業・経理部門',
      industry: '製造業',
      catchCopy: 'Excel手作業から解放され、本来の業務に集中できるようになりました',
      beforeProblem:
        '毎月末に3時間かけて手作業でExcelの報告書を作成していた。データの転記ミスも多く、確認作業にも時間がかかっていた。',
      solution:
        'RPAツールを導入し、複数システムからのデータ取得とExcel作成を自動化。人の手を介さずに正確なレポートを生成できるようになった。',
      result: '作業時間を90%削減（3時間→15分）。転記ミスがゼロになり、データの信頼性が向上。',
      numericResult: '3時間 → 15分',
      detailText:
        '初期設定に1週間、運用開始後は毎月15分の確認作業のみで完了。年間で約34時間の工数削減を実現。',
      thumbnailUrl: '/images/secretary_optimized.jpg',
      videoUrl: '',
      tags: ['RPA', '業務自動化', '経理'],
      status: 'active',
      createdAt: new Date().toISOString(),
      isFeatured: true,
      isPublished: true,
      sortOrder: 10,
    },
    {
      id: 'sample-002',
      title: '顧客問い合わせ対応を自動化し、24時間対応を実現',
      target: '小売業・カスタマーサポート',
      industry: '小売業',
      catchCopy: '深夜や休日の問い合わせにも即座に対応できるようになりました',
      beforeProblem:
        '営業時間外の問い合わせに対応できず、翌営業日まで顧客を待たせていた。よくある質問への対応で人的リソースを圧迫。',
      solution:
        'AIチャットボットを導入し、よくある質問の80%を自動対応。複雑な問い合わせのみ人が対応する体制に変更。',
      result: '顧客満足度30%向上。サポート担当者の負担を50%削減し、より複雑な案件に注力できるように。',
      numericResult: '対応負担 50%削減',
      detailText: 'FAQデータベース構築に2週間。月間約200件の問い合わせのうち160件を自動対応。',
      thumbnailUrl: '/images/task_icon_optimized.jpg',
      videoUrl: '',
      tags: ['AI', 'チャットボット', 'CS'],
      status: 'active',
      createdAt: new Date().toISOString(),
      isFeatured: true,
      isPublished: true,
      sortOrder: 20,
    },
    {
      id: 'sample-003',
      title: '在庫管理を効率化し、発注業務の時間を70%削減',
      target: '卸売業・在庫管理部門',
      industry: '卸売業',
      catchCopy: '手動チェックから解放され、在庫切れリスクも大幅に低減',
      beforeProblem:
        '毎日1時間かけて在庫データを確認し、発注が必要な商品をリストアップ。見落としによる在庫切れも発生していた。',
      solution:
        '在庫管理システムとAIを連携し、需要予測に基づいた自動発注アラートを実装。発注業務の大部分を自動化。',
      result: '発注業務の時間を70%削減（1時間→20分）。在庫切れ発生率を80%削減し、販売機会損失を防止。',
      numericResult: '1時間 → 20分',
      detailText: 'システム連携に3週間。過去2年分の販売データを学習し、精度の高い需要予測を実現。',
      thumbnailUrl: '',
      videoUrl: '',
      tags: ['AI', '在庫管理', '需要予測'],
      status: 'active',
      createdAt: new Date().toISOString(),
      isFeatured: false,
      isPublished: true,
      sortOrder: 30,
    },
  ])
}

/**
 * 拡張列（行の要素が15個以上 = A〜O まで存在する場合）:
 * A id, B title, C target, D industry, E catch_copy, F before_problem, G solution, H result,
 * I numeric_result, J detail_text, K video_url, L thumbnail_url, M tags, N is_featured, O is_published, P sort_order
 *
 * それ未満はレガシー（A〜K）として解釈。スプレッドシートで末尾が空でも列を確保すると安定します。
 *
 * レガシー:
 * A id … H detail, I thumbnail, J video, K status
 */
function parseLegacyRow(row: string[], index: number): CaseData | null {
  const statusRaw = row[10]?.trim() || ''
  let thumbnailUrl = row[8]?.trim() || ''
  let videoUrl = row[9]?.trim() || ''
  let status = 'active'

  if (statusRaw && statusRaw.startsWith('http')) {
    const url = statusRaw
    const isImage =
      /\.(jpg|jpeg|png|gif|svg|webp)$/i.test(url) ||
      url.includes('cdn.') ||
      url.includes('s3.') ||
      url.includes('vercel.app') ||
      url.includes('cloudinary.com') ||
      url.includes('imgix.net')

    const isVideo =
      /\.(mp4|webm|mov|ogg)$/i.test(url) ||
      url.includes('youtube.com') ||
      url.includes('youtu.be') ||
      url.includes('vimeo.com')

    if (isVideo) {
      if (!videoUrl) videoUrl = url
    } else if (isImage) {
      if (!thumbnailUrl) thumbnailUrl = url
    } else if (!videoUrl) {
      videoUrl = url
    }
  } else if (statusRaw && statusRaw.toLowerCase() !== 'active') {
    status = statusRaw.toLowerCase()
  }

  const title = row[1] || ''
  const target = row[2] || ''
  if (!title || !target) return null

  const inactive = status === 'inactive' || status === '非公開' || status === 'false'
  return {
    id: row[0] || `case-${index + 1}`,
    title,
    target,
    industry: '',
    catchCopy: row[3] || '',
    beforeProblem: row[4] || '',
    solution: row[5] || '',
    result: row[6] || '',
    numericResult: '',
    detailText: row[7] || '',
    thumbnailUrl,
    videoUrl,
    tags: [],
    status,
    createdAt: new Date().toISOString(),
    isFeatured: false,
    isPublished: !inactive,
    sortOrder: parseSortOrder(undefined, (index + 1) * 10),
  }
}

function parseExtendedRow(row: string[], index: number): CaseData | null {
  const title = row[1] || ''
  const target = row[2] || ''
  if (!title) return null

  const tags = parseTagsCell(row[12])
  const isPublished = parseBoolCell(row[14], true)
  const isFeatured = parseBoolCell(row[13], false)
  const sortOrder = parseSortOrder(row[15], (index + 1) * 10)

  return {
    id: row[0] || `case-${index + 1}`,
    title,
    target,
    industry: (row[3] || '').trim(),
    catchCopy: row[4] || '',
    beforeProblem: row[5] || '',
    solution: row[6] || '',
    result: row[7] || '',
    numericResult: (row[8] || '').trim(),
    detailText: row[9] || '',
    videoUrl: (row[10] || '').trim(),
    thumbnailUrl: (row[11] || '').trim(),
    tags,
    status: isPublished ? 'active' : 'inactive',
    createdAt: new Date().toISOString(),
    isFeatured,
    isPublished,
    sortOrder,
  }
}

export async function getCasesFromSheet(): Promise<CaseData[]> {
  try {
    const spreadsheetId = process.env.GOOGLE_SPREADSHEET_ID
    const sheetName = process.env.GOOGLE_SHEET_NAME || 'Sheet1'

    if (!spreadsheetId || spreadsheetId.includes('your_spreadsheet_id')) {
      console.warn('GOOGLE_SPREADSHEET_ID not configured, returning sample data')
      return getSampleCases()
    }

    const sheets = getGoogleSheetsClient()

    if (!sheets) {
      console.warn('Google Sheets client not configured, returning sample data')
      return getSampleCases()
    }

    const range = `${sheetName}!A2:P100`
    console.log(`Fetching data from range: ${range}`)

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range,
    })

    const rows = response.data.values

    if (!rows || rows.length === 0) {
      return []
    }

    const cases: CaseData[] = []

    rows.forEach((row, index) => {
      const extended = row.length >= 15
      const parsed = extended ? parseExtendedRow(row, index) : parseLegacyRow(row, index)
      if (parsed) cases.push(parsed)
    })

    return prepareCasesForDisplay(cases)
  } catch (error) {
    console.error('Error fetching cases from Google Sheets:', error)
    console.warn('Returning sample data due to error')
    return getSampleCases()
  }
}
