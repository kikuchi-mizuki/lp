import { google } from 'googleapis'

export interface CaseData {
  id: string
  title: string
  target: string
  catchCopy: string
  beforeProblem: string
  solution: string
  result: string
  detailText?: string
  thumbnailUrl?: string
  videoUrl?: string
  tags?: string[]
  status: string
  createdAt: string
}

/**
 * Google Sheets APIクライアントを初期化
 */
function getGoogleSheetsClient() {
  // 環境変数から取得
  let privateKey = process.env.GOOGLE_PRIVATE_KEY || ''
  const privateKeyBase64 = process.env.GOOGLE_PRIVATE_KEY_BASE64
  const clientEmail = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL

  // Base64エンコードされている場合はデコード (Railwayでの推奨方法)
  if (privateKeyBase64) {
    try {
      privateKey = Buffer.from(privateKeyBase64, 'base64').toString('utf-8')
      // デコード後も改行文字列が残っている場合は変換
      privateKey = privateKey.replace(/\\\\n/g, '\n').replace(/\\n/g, '\n')
    } catch (error) {
      console.error('Failed to decode base64 private key:', error)
      return null
    }
  } else {
    // 通常の環境変数の場合、改行を変換
    privateKey = privateKey.replace(/\\\\n/g, '\n').replace(/\\n/g, '\n')
  }

  if (!privateKey || !clientEmail ||
      privateKey.includes('your_private_key_here') ||
      clientEmail.includes('your-service-account')) {
    // 認証情報が未設定またはダミー値の場合はnullを返す
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

/**
 * フォールバック用のサンプルデータ
 */
function getSampleCases(): CaseData[] {
  return [
    {
      id: 'sample-001',
      title: '月次報告書作成を自動化し、3時間を15分に短縮',
      target: '製造業・経理部門',
      catchCopy: 'Excel手作業から解放され、本来の業務に集中できるようになりました',
      beforeProblem: '毎月末に3時間かけて手作業でExcelの報告書を作成していた。データの転記ミスも多く、確認作業にも時間がかかっていた。',
      solution: 'RPAツールを導入し、複数システムからのデータ取得とExcel作成を自動化。人の手を介さずに正確なレポートを生成できるようになった。',
      result: '作業時間を90%削減（3時間→15分）。転記ミスがゼロになり、データの信頼性が向上。',
      detailText: '初期設定に1週間、運用開始後は毎月15分の確認作業のみで完了。年間で約34時間の工数削減を実現。',
      thumbnailUrl: '/images/secretary_optimized.jpg',
      videoUrl: '',
      tags: ['RPA', '業務自動化', '経理'],
      status: 'active',
      createdAt: new Date().toISOString(),
    },
    {
      id: 'sample-002',
      title: '顧客問い合わせ対応を自動化し、24時間対応を実現',
      target: '小売業・カスタマーサポート',
      catchCopy: '深夜や休日の問い合わせにも即座に対応できるようになりました',
      beforeProblem: '営業時間外の問い合わせに対応できず、翌営業日まで顧客を待たせていた。よくある質問への対応で人的リソースを圧迫。',
      solution: 'AIチャットボットを導入し、よくある質問の80%を自動対応。複雑な問い合わせのみ人が対応する体制に変更。',
      result: '顧客満足度30%向上。サポート担当者の負担を50%削減し、より複雑な案件に注力できるように。',
      detailText: 'FAQデータベース構築に2週間。月間約200件の問い合わせのうち160件を自動対応。',
      thumbnailUrl: '/images/task_icon_optimized.jpg',
      videoUrl: '',
      tags: ['AI', 'チャットボット', 'CS'],
      status: 'active',
      createdAt: new Date().toISOString(),
    },
    {
      id: 'sample-003',
      title: '在庫管理を効率化し、発注業務の時間を70%削減',
      target: '卸売業・在庫管理部門',
      catchCopy: '手動チェックから解放され、在庫切れリスクも大幅に低減',
      beforeProblem: '毎日1時間かけて在庫データを確認し、発注が必要な商品をリストアップ。見落としによる在庫切れも発生していた。',
      solution: '在庫管理システムとAIを連携し、需要予測に基づいた自動発注アラートを実装。発注業務の大部分を自動化。',
      result: '発注業務の時間を70%削減（1時間→20分）。在庫切れ発生率を80%削減し、販売機会損失を防止。',
      detailText: 'システム連携に3週間。過去2年分の販売データを学習し、精度の高い需要予測を実現。',
      thumbnailUrl: '',
      videoUrl: '',
      tags: ['AI', '在庫管理', '需要予測'],
      status: 'active',
      createdAt: new Date().toISOString(),
    },
  ]
}

/**
 * スプレッドシートから導入事例データを取得
 */
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

    // シート名を環境変数から取得（デフォルトはSheet1）
    // A1:K100 の範囲でデータを取得（必要に応じて調整）
    const range = `${sheetName}!A2:K100` // ヘッダー行を除く
    console.log(`Fetching data from range: ${range}`)

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range,
    })

    const rows = response.data.values

    if (!rows || rows.length === 0) {
      return []
    }

    // スプレッドシートの列構造:
    // A: id
    // B: title (タイトル)
    // C: target (対象)
    // D: catchCopy (キャッチコピー)
    // E: beforeProblem (導入前の課題)
    // F: solution (解決策)
    // G: result (結果)
    // H: detailText (詳細テキスト)
    // I: thumbnailUrl (サムネイル画像URL)
    // J: videoUrl (動画URL)
    // K: status (ステータス: active/inactive)

    const cases: CaseData[] = rows
      .filter((row) => {
        // statusがactiveのもののみ、または空の場合はactiveとみなす
        const statusRaw = row[10]?.trim() || ''
        const status = statusRaw.toLowerCase()

        // URLの場合はactiveとして扱う（元のLPと同じ動作）
        if (statusRaw.startsWith('http')) {
          return true
        }

        return status === 'active' || status === ''
      })
      .map((row, index) => {
        // tagsはスプレッドシートには列がないため、空の配列とする
        const tags: string[] = []

        // K列（status）からURLを自動検出（元のLPと同じ動作）
        const statusRaw = row[10]?.trim() || ''
        let thumbnailUrl = row[8]?.trim() || ''
        let videoUrl = row[9]?.trim() || ''
        let status = 'active'

        // K列にURLが入っている場合、自動検出
        if (statusRaw && statusRaw.startsWith('http')) {
          const url = statusRaw
          const isImage = /\.(jpg|jpeg|png|gif|svg|webp)$/i.test(url) ||
                         url.includes('cdn.') ||
                         url.includes('s3.') ||
                         url.includes('vercel.app') ||
                         url.includes('cloudinary.com') ||
                         url.includes('imgix.net')

          const isVideo = /\.(mp4|webm|mov|ogg)$/i.test(url) ||
                         url.includes('youtube.com') ||
                         url.includes('youtu.be') ||
                         url.includes('vimeo.com')

          if (isVideo) {
            // 動画URLとして優先的に扱う
            if (!videoUrl) {
              videoUrl = url
            }
          } else if (isImage) {
            // 画像URLとして扱う
            if (!thumbnailUrl) {
              thumbnailUrl = url
            }
          } else {
            // その他のURLは動画URLとして扱う
            if (!videoUrl) {
              videoUrl = url
            }
          }
        } else if (statusRaw && statusRaw.toLowerCase() !== 'active') {
          status = statusRaw.toLowerCase()
        }

        return {
          id: row[0] || `case-${index + 1}`,
          title: row[1] || '',
          target: row[2] || '',
          catchCopy: row[3] || '',
          beforeProblem: row[4] || '',
          solution: row[5] || '',
          result: row[6] || '',
          detailText: row[7] || '',
          thumbnailUrl,
          videoUrl,
          tags,
          status,
          createdAt: new Date().toISOString(),
        }
      })
      .filter((caseData) => caseData.title && caseData.target) // タイトルと対象が必須

    return cases
  } catch (error) {
    console.error('Error fetching cases from Google Sheets:', error)
    // エラー時はサンプルデータを返す
    console.warn('Returning sample data due to error')
    return getSampleCases()
  }
}
