# Railway デプロイガイド

## デプロイ手順

### 1. Railway プロジェクトを作成

1. [Railway.app](https://railway.app/) にログイン
2. 「New Project」をクリック
3. 「Deploy from GitHub repo」を選択
4. リポジトリ `kikuchi-mizuki/lp` を選択

### 2. サービスの設定

1. **Root Directory** を設定:
   - Settings → Root Directory → `consultation-lp` と入力

2. **環境変数** を設定:
   ```
   GOOGLE_SPREADSHEET_ID=15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M
   GOOGLE_SHEET_NAME=相談LP事例
   GOOGLE_SERVICE_ACCOUNT_EMAIL=(サービスアカウントのメールアドレス)
   GOOGLE_PRIVATE_KEY=(プライベートキー - 改行は\nで表記)
   NEXT_PUBLIC_SITE_URL=(デプロイ後のURL - 例: https://your-app.up.railway.app)
   ```

   **Supabase設定（オプション - 将来的に使用する場合）:**
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   ```

3. **Build設定** (自動検出されるため通常不要):
   - Build Command: `npm run build`
   - Start Command: `npm start`

### 3. デプロイ

- GitHubにプッシュすると自動的にデプロイが開始されます
- デプロイ完了後、Railwayが提供するURLでアクセス可能になります

## 環境変数の注意点

### GOOGLE_PRIVATE_KEY の設定方法

プライベートキーは改行を `\n` で表記する必要があります：

```
-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0...\n-----END PRIVATE KEY-----
```

または、Railwayのダッシュボードで直接ペーストする場合は、そのままコピー&ペーストでOKです。

## トラブルシューティング

### ビルドエラーが発生する場合

1. Root Directoryが `consultation-lp` に設定されているか確認
2. 環境変数が正しく設定されているか確認
3. Railway のビルドログを確認

### Google Sheets APIエラー

1. サービスアカウントがスプレッドシートに共有されているか確認
2. `GOOGLE_PRIVATE_KEY` の改行文字が正しいか確認
3. 権限が「閲覧者」または「編集者」に設定されているか確認

## カスタムドメインの設定

1. Railway ダッシュボードで Settings → Domains
2. 「Add Domain」をクリック
3. カスタムドメインを入力
4. DNSレコードを設定（Railway が指示を表示します）

## デプロイ後のURL

デプロイ後、以下のようなURLが発行されます：

```
https://consultation-lp-production-xxxx.up.railway.app
```

このURLを環境変数 `NEXT_PUBLIC_SITE_URL` に設定してください。

## 参考リンク

- [Railway Documentation](https://docs.railway.app/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Google Sheets API](https://developers.google.com/sheets/api)
