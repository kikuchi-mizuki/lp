# AIコレクションズ - 業務改善無料相談LP

業務改善向けの無料相談を獲得するための姉妹サイトLP

## 技術スタック

- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend/DB**: Supabase
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage

## プロジェクト構成

```
consultation-lp/
├── app/
│   ├── consultation/          # 無料相談LP
│   ├── admin/
│   │   └── cases/            # 事例管理画面
│   ├── api/                  # API Routes
│   └── layout.tsx
├── components/
│   ├── consultation/         # LP用コンポーネント
│   ├── admin/               # 管理画面用コンポーネント
│   └── shared/              # 共通コンポーネント
├── lib/
│   └── supabase/            # Supabase設定
├── types/                   # TypeScript型定義
└── public/                  # 静的ファイル
```

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. 環境変数の設定

`.env.local`ファイルを作成し、以下を設定：

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Supabaseのセットアップ

`supabase/migrations/001_initial_schema.sql`を実行してテーブルを作成

### 4. 開発サーバーの起動

```bash
npm run dev
```

## ページ構成

- `/consultation` - 無料相談LP
- `/admin/cases` - 事例管理画面（要認証）

## 主要機能

### 無料相談LP
- ファーストビュー
- よくある悩み
- 事例紹介（Supabaseから動的取得）
- よくある質問
- 相談フォーム

### 事例管理画面
- ログイン認証
- 事例のCRUD操作
- 公開/非公開切り替え
- 並び順の設定
- サムネイル画像アップロード

## デザインコンセプト

AIコレクションズのブランドトーンを継承：
- 上品で信頼感のあるデザイン
- プロフェッショナルな印象
- 「無料相談」への心理的ハードルを下げる
- 無理な営業感を出さない
