# Railway 環境変数設定ガイド（クイックスタート）

本番環境（Railway）でスプレッドシートを連携させるための手順です。

## ⚡️ 問題の症状

- 開発環境では動作する
- 本番環境（Railway）で「スプレッドシートの内容が反映されない」

## 🔧 原因

Railwayに環境変数が設定されていないか、秘密鍵の改行処理に問題があります。

## ✅ 解決手順

### ステップ1: Base64エンコードされた秘密鍵を生成

ローカルで以下のコマンドを実行:

```bash
cd consultation-lp
npm run encode-key
```

出力されたBase64文字列（長い文字列）をコピーしてください。

### ステップ2: Railwayで環境変数を設定

1. [Railway Dashboard](https://railway.app/) を開く
2. プロジェクトを選択
3. **Variables** タブをクリック
4. 以下の環境変数を **すべて** 設定:

#### 必須の環境変数

| 環境変数名 | 値 |
|-----------|-----|
| `GOOGLE_SPREADSHEET_ID` | `15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M` |
| `GOOGLE_SHEET_NAME` | `相談LP事例` |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | `aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com` |
| `GOOGLE_PRIVATE_KEY_BASE64` | （ステップ1で生成したBase64文字列を貼り付け） |

#### 各変数の設定方法

1. **New Variable** をクリック
2. **Variable Name** に上記の名前を入力
3. **Value** に対応する値を入力
4. **Add** をクリック
5. すべての変数について繰り返す

### ステップ3: デプロイ

環境変数を保存すると、Railwayが自動的に再デプロイします。

### ステップ4: 確認

デプロイ完了後、以下のURLにアクセスして動作確認:

```
https://your-app.up.railway.app/api/cases
```

正常に動作している場合、JSONでスプレッドシートのデータが返されます。

## 🔍 トラブルシューティング

### 環境変数が正しく設定されているか確認

Railwayのダッシュボードで **Variables** タブを開き、以下が設定されているか確認:

- ✅ GOOGLE_SPREADSHEET_ID
- ✅ GOOGLE_SHEET_NAME
- ✅ GOOGLE_SERVICE_ACCOUNT_EMAIL
- ✅ GOOGLE_PRIVATE_KEY_BASE64

### それでも動作しない場合

1. Railwayのログを確認:
   - **Deployments** タブ → 最新のデプロイをクリック → **Logs** を確認
   - エラーメッセージがあれば、それをもとに対処

2. サービスアカウントの権限を確認:
   - [スプレッドシート](https://docs.google.com/spreadsheets/d/15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M/edit)を開く
   - 右上の **共有** をクリック
   - `aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com` が追加されているか確認
   - 権限が「閲覧者」以上になっているか確認

3. スプレッドシートにデータが入っているか確認:
   - シート名が「相談LP事例」になっているか
   - データが2行目以降に入力されているか（1行目はヘッダー）
   - K列（status）が「active」または空欄になっているか

## 📋 チェックリスト

設定完了後、以下を確認:

- [ ] Railwayに4つの環境変数が設定されている
- [ ] デプロイが完了している（緑色のチェックマーク）
- [ ] `/api/cases` エンドポイントがJSONを返す
- [ ] スプレッドシートのデータがページに表示される

## 🆘 それでも解決しない場合

詳細な設定手順は以下のドキュメントを参照:

- [DEPLOYMENT.md](./DEPLOYMENT.md) - 詳細なデプロイ手順
- [GOOGLE_SHEETS_SETUP.md](./GOOGLE_SHEETS_SETUP.md) - Google Sheets設定の詳細

---

## 💡 補足情報

### なぜBase64エンコードが必要？

Google秘密鍵には改行が含まれており、環境変数として設定する際に改行処理が正しく行われないことがあります。Base64エンコードすることで、改行を含まない1つの文字列として扱えるため、確実に動作します。

### 従来の方法（非推奨）

以下の方法も可能ですが、改行処理の問題が発生しやすいため推奨しません:

```
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG...\n-----END PRIVATE KEY-----
```

Base64方式を使用してください。
