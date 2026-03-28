#!/usr/bin/env node
/**
 * 環境変数の設定状況を確認するスクリプト
 * 本番環境（Railway）で環境変数が正しく設定されているか確認するために使用
 *
 * 使い方:
 * node scripts/check-env.js
 */

const requiredVars = [
  {
    name: 'GOOGLE_SPREADSHEET_ID',
    description: 'スプレッドシートID',
    example: '15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M',
    required: true
  },
  {
    name: 'GOOGLE_SHEET_NAME',
    description: 'シート名',
    example: '相談LP事例',
    required: false,
    default: 'Sheet1'
  },
  {
    name: 'GOOGLE_SERVICE_ACCOUNT_EMAIL',
    description: 'サービスアカウントメール',
    example: 'your-service-account@your-project.iam.gserviceaccount.com',
    required: true
  },
  {
    name: 'GOOGLE_PRIVATE_KEY',
    description: '秘密鍵（従来の方式）',
    example: '-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----',
    required: false
  },
  {
    name: 'GOOGLE_PRIVATE_KEY_BASE64',
    description: '秘密鍵（Base64エンコード - 推奨）',
    example: 'LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t...',
    required: false
  },
  {
    name: 'NEXT_PUBLIC_SITE_URL',
    description: 'サイトURL',
    example: 'https://your-app.up.railway.app',
    required: false
  }
]

console.log('🔍 環境変数の設定状況を確認中...\n')
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

let hasError = false
let hasWarning = false

requiredVars.forEach((varInfo) => {
  const value = process.env[varInfo.name]
  const hasValue = value && value.trim() !== ''

  // ダミー値のチェック
  const isDummy = hasValue && (
    value.includes('your_') ||
    value.includes('your-') ||
    value.includes('example') ||
    value.includes('dummy')
  )

  let status = '❌'
  let message = '未設定'

  if (hasValue && !isDummy) {
    status = '✅'
    // 値の一部を表示（セキュリティのため）
    if (varInfo.name.includes('PRIVATE_KEY')) {
      message = `設定済み (${value.length}文字)`
    } else if (varInfo.name.includes('EMAIL') && value.includes('@')) {
      message = `設定済み (${value})`
    } else if (value.length > 50) {
      message = `設定済み (${value.substring(0, 20)}...)`
    } else {
      message = `設定済み (${value})`
    }
  } else if (isDummy) {
    status = '⚠️'
    message = 'ダミー値が設定されています'
    hasWarning = true
  } else if (!varInfo.required && varInfo.default) {
    status = '⚪️'
    message = `未設定 (デフォルト: ${varInfo.default})`
  } else if (!varInfo.required) {
    status = '⚪️'
    message = '未設定（任意）'
  } else {
    hasError = true
  }

  console.log(`${status} ${varInfo.description} (${varInfo.name})`)
  console.log(`   ${message}`)
  console.log()
})

// 秘密鍵の設定チェック
const hasPrivateKey = process.env.GOOGLE_PRIVATE_KEY && !process.env.GOOGLE_PRIVATE_KEY.includes('your_')
const hasPrivateKeyBase64 = process.env.GOOGLE_PRIVATE_KEY_BASE64 && !process.env.GOOGLE_PRIVATE_KEY_BASE64.includes('your_')

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
console.log('\n🔐 秘密鍵の設定状況:')

if (hasPrivateKeyBase64) {
  console.log('✅ GOOGLE_PRIVATE_KEY_BASE64が設定されています（推奨方式）')
  if (hasPrivateKey) {
    console.log('ℹ️  GOOGLE_PRIVATE_KEYも設定されていますが、Base64方式が優先されます')
  }
} else if (hasPrivateKey) {
  console.log('⚠️  GOOGLE_PRIVATE_KEYが設定されています（従来の方式）')
  console.log('   推奨: Base64エンコード方式に変更してください')
  console.log('   実行: node scripts/encode-private-key.js')
  hasWarning = true
} else {
  console.log('❌ 秘密鍵が設定されていません')
  console.log('   GOOGLE_PRIVATE_KEYまたはGOOGLE_PRIVATE_KEY_BASE64を設定してください')
  hasError = true
}

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

// 結果サマリー
if (hasError) {
  console.log('❌ エラー: 必須の環境変数が設定されていません')
  console.log('\n📝 設定手順:')
  console.log('1. Railwayダッシュボードを開く')
  console.log('2. プロジェクト → Variables')
  console.log('3. 必要な環境変数を追加')
  console.log('\n詳細は DEPLOYMENT.md を参照してください')
  process.exit(1)
} else if (hasWarning) {
  console.log('⚠️  警告: 一部の設定に問題があります')
  console.log('動作する可能性はありますが、推奨設定を確認してください')
  console.log('\n詳細は DEPLOYMENT.md を参照してください')
} else {
  console.log('✅ すべての環境変数が正しく設定されています')
  console.log('\nGoogle Sheets APIとの接続テストを実行してください:')
  console.log('curl http://localhost:3001/api/cases')
}

console.log()
