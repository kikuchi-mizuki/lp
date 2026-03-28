/**
 * スプレッドシートの画像URLを更新するスクリプト
 *
 * 使用方法:
 * 1. .env.localに認証情報を設定
 * 2. npm run update-images
 */

import { config } from 'dotenv'
import { google } from 'googleapis'

config({ path: '.env.local' })

const SPREADSHEET_ID = process.env.GOOGLE_SPREADSHEET_ID || '15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M'
const SHEET_NAME = process.env.GOOGLE_SHEET_NAME || '相談LP事例'

// 更新する画像URL（実際に表示したい画像URLに変更してください）
const IMAGE_UPDATES = {
  'case-001': {
    thumbnailUrl: 'https://www.mmms-11.com/aicollections_image/secretary.jpg', // 製造業の画像
    videoUrl: 'https://www.mmms-11.com/aicollections_image/task.mp4'
  },
  'case-002': {
    thumbnailUrl: 'https://www.mmms-11.com/aicollections_image/cs_support.jpg', // カスタマーサポートの画像
    videoUrl: ''
  },
  'case-003': {
    thumbnailUrl: 'https://www.mmms-11.com/aicollections_image/inventory.jpg', // 在庫管理の画像
    videoUrl: ''
  }
}

async function updateCaseImages() {
  console.log('🚀 スプレッドシートの画像URLを更新します...\n')

  const privateKey = process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n')
  const clientEmail = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL

  if (!privateKey || !clientEmail || privateKey.includes('your_private_key_here')) {
    console.error('❌ エラー: Google Sheets APIの認証情報が設定されていません')
    process.exit(1)
  }

  try {
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

    // 現在のデータを取得
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_NAME}!A2:P100`,
    })

    const rows = response.data.values
    if (!rows || rows.length === 0) {
      console.log('⚠️  データが見つかりません')
      return
    }

    console.log(`📊 ${rows.length}件のデータを確認しました\n`)

    // 更新するセルの情報を収集
    const updates: any[] = []

    rows.forEach((row, index) => {
      const id = row[0]
      const rowNumber = index + 2 // ヘッダー行をスキップ

      if (IMAGE_UPDATES[id as keyof typeof IMAGE_UPDATES]) {
        const imageData = IMAGE_UPDATES[id as keyof typeof IMAGE_UPDATES]

        // K列: videoUrl
        if (imageData.videoUrl !== undefined) {
          updates.push({
            range: `${SHEET_NAME}!K${rowNumber}`,
            values: [[imageData.videoUrl]]
          })
          console.log(`✏️  ${id}: videoUrl を更新`)
        }

        // L列: thumbnailUrl
        if (imageData.thumbnailUrl !== undefined) {
          updates.push({
            range: `${SHEET_NAME}!L${rowNumber}`,
            values: [[imageData.thumbnailUrl]]
          })
          console.log(`✏️  ${id}: thumbnailUrl を更新`)
        }
      }
    })

    if (updates.length === 0) {
      console.log('⚠️  更新するデータがありません')
      return
    }

    // バッチ更新を実行
    await sheets.spreadsheets.values.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      requestBody: {
        valueInputOption: 'RAW',
        data: updates
      }
    })

    console.log(`\n✅ ${updates.length}個のセルを更新しました`)
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('🎉 画像URLの更新が完了しました！')
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
    console.log('📍 スプレッドシートURL:')
    console.log(`https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit\n`)
    console.log('次のステップ:')
    console.log('1. ブラウザをリロード（Cmd+R または F5）')
    console.log('2. カードの画像が更新されているか確認\n')

  } catch (error: any) {
    console.error('❌ エラーが発生しました:', error.message)
    process.exit(1)
  }
}

updateCaseImages()
