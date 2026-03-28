/**
 * Google Sheetsにシートを追加してサンプルデータを投入するスクリプト
 *
 * 使用方法:
 * 1. .env.localに認証情報を設定
 * 2. npm run setup-sheet
 */

import { config } from 'dotenv'
import { google } from 'googleapis'

// .env.localファイルを読み込む
config({ path: '.env.local' })

const SPREADSHEET_ID = process.env.GOOGLE_SPREADSHEET_ID || '15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M'
const SHEET_NAME = process.env.GOOGLE_SHEET_NAME || '相談LP事例'

async function setupSpreadsheet() {
  console.log('🚀 スプレッドシートのセットアップを開始します...\n')

  // 認証情報の確認
  const privateKey = process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n')
  const clientEmail = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL

  if (!privateKey || !clientEmail ||
      privateKey.includes('your_private_key_here') ||
      clientEmail.includes('your-service-account')) {
    console.error('❌ エラー: Google Sheets APIの認証情報が設定されていません')
    console.error('\n.env.localファイルに以下を設定してください:')
    console.error('- GOOGLE_SERVICE_ACCOUNT_EMAIL')
    console.error('- GOOGLE_PRIVATE_KEY')
    console.error('\n詳細はGOOGLE_SHEETS_SETUP.mdを参照してください')
    process.exit(1)
  }

  try {
    // Google Sheets APIクライアントの初期化
    const auth = new google.auth.GoogleAuth({
      credentials: {
        client_email: clientEmail,
        private_key: privateKey,
      },
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    })

    const sheets = google.sheets({ version: 'v4', auth })

    console.log(`📋 スプレッドシートID: ${SPREADSHEET_ID}`)
    console.log(`📄 シート名: ${SHEET_NAME}\n`)

    // 既存のシート一覧を取得
    const spreadsheet = await sheets.spreadsheets.get({
      spreadsheetId: SPREADSHEET_ID,
    })

    const existingSheet = spreadsheet.data.sheets?.find(
      (sheet) => sheet.properties?.title === SHEET_NAME
    )

    let sheetId: number

    if (existingSheet) {
      console.log(`⚠️  シート「${SHEET_NAME}」は既に存在します`)
      console.log('既存のシートをクリアしてデータを再投入します...\n')
      sheetId = existingSheet.properties?.sheetId || 0

      // 既存データをクリア
      await sheets.spreadsheets.values.clear({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!A1:K1000`,
      })
    } else {
      console.log(`✨ 新しいシート「${SHEET_NAME}」を作成します...\n`)

      // 新しいシートを追加
      const addSheetResponse = await sheets.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: {
          requests: [
            {
              addSheet: {
                properties: {
                  title: SHEET_NAME,
                  gridProperties: {
                    rowCount: 100,
                    columnCount: 11,
                  },
                },
              },
            },
          ],
        },
      })

      sheetId = addSheetResponse.data.replies?.[0]?.addSheet?.properties?.sheetId || 0
      console.log('✅ シートを作成しました')
    }

    // ヘッダー行
    const headers = [
      'id',
      'title',
      'target',
      'catchCopy',
      'beforeProblem',
      'solution',
      'result',
      'detailText',
      'thumbnailUrl',
      'videoUrl',
      'status',
    ]

    // サンプルデータ
    const sampleData = [
      [
        'case-001',
        '月次報告書作成を自動化し、3時間を15分に短縮',
        '製造業・経理部門',
        'Excel手作業から解放され、本来の業務に集中できるようになりました',
        '毎月末に3時間かけて手作業でExcelの報告書を作成していた。データの転記ミスも多く、確認作業にも時間がかかっていた。',
        'RPAツールを導入し、複数システムからのデータ取得とExcel作成を自動化。人の手を介さずに正確なレポートを生成できるようになった。',
        '作業時間を90%削減（3時間→15分）。転記ミスがゼロになり、データの信頼性が向上。',
        '初期設定に1週間、運用開始後は毎月15分の確認作業のみで完了。年間で約34時間の工数削減を実現。',
        '',
        '',
        'active',
      ],
      [
        'case-002',
        '顧客問い合わせ対応を自動化し、24時間対応を実現',
        '小売業・カスタマーサポート',
        '深夜や休日の問い合わせにも即座に対応できるようになりました',
        '営業時間外の問い合わせに対応できず、翌営業日まで顧客を待たせていた。よくある質問への対応で人的リソースを圧迫。',
        'AIチャットボットを導入し、よくある質問の80%を自動対応。複雑な問い合わせのみ人が対応する体制に変更。',
        '顧客満足度30%向上。サポート担当者の負担を50%削減し、より複雑な案件に注力できるように。',
        'FAQデータベース構築に2週間。月間約200件の問い合わせのうち160件を自動対応。',
        '',
        '',
        'active',
      ],
      [
        'case-003',
        '在庫管理を効率化し、発注業務の時間を70%削減',
        '卸売業・在庫管理部門',
        '手動チェックから解放され、在庫切れリスクも大幅に低減',
        '毎日1時間かけて在庫データを確認し、発注が必要な商品をリストアップ。見落としによる在庫切れも発生していた。',
        '在庫管理システムとAIを連携し、需要予測に基づいた自動発注アラートを実装。発注業務の大部分を自動化。',
        '発注業務の時間を70%削減（1時間→20分）。在庫切れ発生率を80%削減し、販売機会損失を防止。',
        'システム連携に3週間。過去2年分の販売データを学習し、精度の高い需要予測を実現。',
        '',
        '',
        'active',
      ],
    ]

    // データをスプレッドシートに書き込み
    const values = [headers, ...sampleData]

    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_NAME}!A1:K${values.length}`,
      valueInputOption: 'RAW',
      requestBody: {
        values,
      },
    })

    console.log('✅ ヘッダー行を追加しました')
    console.log(`✅ サンプルデータを${sampleData.length}件追加しました\n`)

    // ヘッダー行のフォーマット設定
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      requestBody: {
        requests: [
          // ヘッダー行を太字に
          {
            repeatCell: {
              range: {
                sheetId,
                startRowIndex: 0,
                endRowIndex: 1,
              },
              cell: {
                userEnteredFormat: {
                  textFormat: {
                    bold: true,
                  },
                  backgroundColor: {
                    red: 0.85,
                    green: 0.92,
                    blue: 0.97,
                  },
                },
              },
              fields: 'userEnteredFormat(textFormat,backgroundColor)',
            },
          },
          // 列幅を自動調整
          {
            autoResizeDimensions: {
              dimensions: {
                sheetId,
                dimension: 'COLUMNS',
                startIndex: 0,
                endIndex: 11,
              },
            },
          },
        ],
      },
    })

    console.log('✅ ヘッダー行のフォーマットを設定しました')
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('🎉 セットアップが完了しました！')
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
    console.log(`📍 スプレッドシートURL:`)
    console.log(`https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit#gid=${sheetId}\n`)
    console.log('次のステップ:')
    console.log('1. スプレッドシートを開いて確認')
    console.log('2. 必要に応じてデータを編集')
    console.log('3. http://localhost:3001/consultation#cases で表示確認\n')
  } catch (error: any) {
    console.error('❌ エラーが発生しました:', error.message)

    if (error.code === 403) {
      console.error('\n権限エラー:')
      console.error('- スプレッドシートがサービスアカウントと共有されているか確認してください')
      console.error(`- サービスアカウント: ${clientEmail}`)
    } else if (error.code === 404) {
      console.error('\nスプレッドシートが見つかりません:')
      console.error(`- スプレッドシートID: ${SPREADSHEET_ID}`)
      console.error('- IDが正しいか確認してください')
    }

    process.exit(1)
  }
}

setupSpreadsheet()
