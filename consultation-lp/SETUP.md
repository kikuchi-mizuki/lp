# セットアップ手順

## 1. Supabaseプロジェクトの作成

1. [Supabase](https://supabase.com)でアカウントを作成
2. 新規プロジェクトを作成
3. Project Settings → API から以下を取得:
   - Project URL
   - Anon/Public Key

## 2. 環境変数の設定

`.env.local`ファイルを作成:

```bash
cp .env.local.example .env.local
```

`.env.local`に以下を設定:

```
NEXT_PUBLIC_SUPABASE_URL=あなたのSupabaseプロジェクトURL
NEXT_PUBLIC_SUPABASE_ANON_KEY=あなたのSupabaseAnonKey
NEXT_PUBLIC_SITE_URL=http://localhost:3001
```

## 3. Supabaseデータベースのセットアップ

Supabase管理画面の「SQL Editor」で以下を実行:

```sql
-- supabase/migrations/001_initial_schema.sql の内容をコピー&実行
```

## 4. 管理者ユーザーの作成

Supabase管理画面の「Authentication」→「Users」から:

1. 「Add User」をクリック
2. メールアドレスとパスワードを設定
3. 「Create User」をクリック

このメールアドレスとパスワードで管理画面にログインできます。

## 5. 依存関係のインストール

```bash
npm install
```

## 6. 開発サーバーの起動

```bash
npm run dev
```

ブラウザで以下にアクセス:

- 無料相談LP: http://localhost:3001/consultation
- 管理画面: http://localhost:3001/admin/cases

## 7. サムネイル画像の設定（オプション）

Supabase Storageを使用する場合:

1. Supabase管理画面の「Storage」→「Create Bucket」
2. Bucket名: `case-thumbnails`
3. Public access: `ON`
4. ファイルサイズ制限: 5MB
5. 許可MIMEタイプ: `image/jpeg, image/png, image/webp`

画像をアップロードしたら、公開URLを事例のサムネイルURLに設定します。

## トラブルシューティング

### データベース接続エラー

- `.env.local`の設定を確認
- SupabaseプロジェクトのURLとKeyが正しいか確認

### ログインできない

- Supabaseの「Authentication」でユーザーが作成されているか確認
- メールアドレスとパスワードが正しいか確認

### 事例が表示されない

- 事例の「公開する」チェックが入っているか確認
- SQLマイグレーションが正常に実行されたか確認

## デプロイ

### Vercelにデプロイ

1. GitHubリポジトリにプッシュ
2. [Vercel](https://vercel.com)でプロジェクトをインポート
3. 環境変数を設定:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_SITE_URL` (本番URL)

### Netlifyにデプロイ

1. GitHubリポジトリにプッシュ
2. [Netlify](https://netlify.com)でプロジェクトをインポート
3. Build command: `npm run build`
4. Publish directory: `.next`
5. 環境変数を設定（Vercelと同じ）

## 本番環境での注意事項

1. **SEO対策**
   - `next.config.js`で画像ドメインを追加
   - OGP画像を設定
   - Google Analytics等の設定

2. **セキュリティ**
   - Supabase RLSポリシーの確認
   - 管理画面のアクセス制限
   - HTTPS必須

3. **パフォーマンス**
   - 画像の最適化
   - キャッシュ設定
   - CDN使用の検討
