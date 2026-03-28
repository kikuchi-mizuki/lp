#!/usr/bin/env node
/**
 * Google秘密鍵をBase64エンコードするスクリプト
 * Railway用の環境変数設定を簡単にします
 *
 * 使い方:
 * 1. .env.localにGOOGLE_PRIVATE_KEYを設定
 * 2. このスクリプトを実行: node scripts/encode-private-key.js
 * 3. 出力されたBase64文字列をRailwayのGOOGLE_PRIVATE_KEY_BASE64に設定
 */

const fs = require('fs')
const path = require('path')
require('dotenv').config({ path: '.env.local' })

const privateKey = process.env.GOOGLE_PRIVATE_KEY

if (!privateKey) {
  console.error('❌ エラー: GOOGLE_PRIVATE_KEYが.env.localに設定されていません')
  console.log('\n.env.localに以下を設定してください:')
  console.log('GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----')
  process.exit(1)
}

if (privateKey.includes('your_private_key_here')) {
  console.error('❌ エラー: GOOGLE_PRIVATE_KEYがダミー値のままです')
  process.exit(1)
}

try {
  // Base64エンコード
  const base64 = Buffer.from(privateKey).toString('base64')

  // ファイルに保存
  const outputFile = path.join(__dirname, '.base64-key.txt')
  fs.writeFileSync(outputFile, base64, 'utf8')

  console.log('✅ Base64エンコードが完了しました\n')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('📋 Railwayの環境変数に以下を設定してください:')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
  console.log('環境変数名: GOOGLE_PRIVATE_KEY_BASE64')
  console.log('\n📄 値は以下のファイルに保存されました（改行なし・コピーしやすい形式）:')
  console.log(`   ${outputFile}`)
  console.log('\n💡 ファイルの内容を表示:')
  console.log(`   cat ${outputFile}`)
  console.log('\n💡 macOSでクリップボードにコピー:')
  console.log(`   cat ${outputFile} | pbcopy`)
  console.log('\n💡 Linuxでクリップボードにコピー:')
  console.log(`   cat ${outputFile} | xclip -selection clipboard`)
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('\n📝 設定手順:')
  console.log('1. Railwayのダッシュボードを開く')
  console.log('2. プロジェクト → Variables')
  console.log('3. New Variable をクリック')
  console.log('4. Variable Name: GOOGLE_PRIVATE_KEY_BASE64')
  console.log('5. Value: 上記のBase64文字列を貼り付け')
  console.log('6. Add をクリック')
  console.log('\n⚠️  注意: GOOGLE_PRIVATE_KEYとGOOGLE_PRIVATE_KEY_BASE64の両方を設定した場合、')
  console.log('   GOOGLE_PRIVATE_KEY_BASE64が優先されます（推奨）')
  console.log('\n🔧 他に必要な環境変数:')
  console.log('- GOOGLE_SPREADSHEET_ID')
  console.log('- GOOGLE_SHEET_NAME')
  console.log('- GOOGLE_SERVICE_ACCOUNT_EMAIL')

  // サービスアカウントメールも表示
  const serviceAccountEmail = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL
  if (serviceAccountEmail && !serviceAccountEmail.includes('your-service-account')) {
    console.log(`\n✅ サービスアカウントメール: ${serviceAccountEmail}`)
  }

  const spreadsheetId = process.env.GOOGLE_SPREADSHEET_ID
  if (spreadsheetId && !spreadsheetId.includes('your_spreadsheet_id')) {
    console.log(`✅ スプレッドシートID: ${spreadsheetId}`)
  }

  const sheetName = process.env.GOOGLE_SHEET_NAME
  if (sheetName) {
    console.log(`✅ シート名: ${sheetName}`)
  }

} catch (error) {
  console.error('❌ エラーが発生しました:', error.message)
  process.exit(1)
}
