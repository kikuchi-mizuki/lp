# AI Collections LP デザインシステム

## 1. ブランドアイデンティティ

### ロゴ分析
- **メインロゴ**: グラデーションの「a」文字 + 上部のドット
- **カラーパレット**: ブルーからパープルへのグラデーション
- **タイポグラフィ**: モダンなサンセリフ（AI Collections）
- **デザインスタイル**: クリーン、モダン、デジタル感

## 2. カラーパレット

### プライマリカラー
```css
/* メイングラデーション */
--primary-gradient: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
--primary-blue: #4F46E5;
--primary-purple: #7C3AED;

/* グラデーション変形 */
--gradient-light: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
--gradient-dark: linear-gradient(135deg, #3730A3 0%, #5B21B6 100%);
```

### セカンダリカラー
```css
--accent-blue: #3B82F6;
--accent-purple: #8B5CF6;
--accent-indigo: #6366F1;
```

### ニュートラルカラー
```css
--text-primary: #1F2937;
--text-secondary: #6B7280;
--text-muted: #9CA3AF;
--background-white: #FFFFFF;
--background-gray: #F9FAFB;
--border-light: #E5E7EB;
--border-medium: #D1D5DB;
```

## 3. タイポグラフィ

### フォントファミリー
```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### フォントサイズ
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */
```

## 4. デザイントーン

### 全体的なスタイル
- **モダン**: クリーンで洗練されたデザイン
- **デジタル**: テクノロジー感のある要素
- **親しみやすい**: アクセシブルで使いやすいUI
- **プロフェッショナル**: 信頼性を感じさせるデザイン

### 視覚的要素
- **グラデーション**: ロゴと統一感のあるグラデーション使用
- **角丸**: 8px〜16pxの適度な角丸
- **シャドウ**: ソフトで自然な影効果
- **アニメーション**: スムーズで控えめな動き

## 5. コンポーネントデザイン

### ボタン
```css
/* プライマリボタン */
.btn-primary {
  background: var(--primary-gradient);
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
  transition: all 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 70, 229, 0.35);
}

/* セカンダリボタン */
.btn-secondary {
  background: var(--background-white);
  border: 2px solid var(--border-medium);
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.2s ease;
}
```

### カード
```css
.card {
  background: var(--background-white);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}
```

### フォーム
```css
.form-input {
  border: 2px solid var(--border-light);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: var(--text-base);
  transition: all 0.2s ease;
}

.form-input:focus {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  outline: none;
}
```

## 6. LPレイアウト構成

### ヘッダー
- ロゴ配置（左上）
- ナビゲーション（右側）
- 背景: グラデーションまたはホワイト

### ヒーローセクション
- 大きな見出し（グラデーションテキスト）
- サブタイトル
- CTAボタン（プライマリグラデーション）
- 背景: ソフトなグラデーション

### 機能紹介セクション
- カード形式での機能説明
- アイコン使用（グラデーション）
- 3カラムレイアウト

### 料金セクション
- 料金カード（ホバーエフェクト付き）
- グラデーションボーダー
- 目立つCTAボタン

### フッター
- ロゴ
- リンク集
- 法的情報

## 7. アニメーション・インタラクション

### ホバーエフェクト
```css
/* カードホバー */
.card-hover {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-hover:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

/* ボタンホバー */
.btn-hover {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 70, 229, 0.3);
}
```

### スクロールアニメーション
```css
/* フェードイン */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.6s ease-out;
}
```

## 8. レスポンシブデザイン

### ブレークポイント
```css
--mobile: 640px;
--tablet: 768px;
--desktop: 1024px;
--large: 1280px;
```

### モバイル対応
- タッチフレンドリーなボタンサイズ
- 適切なタッチターゲット（44px以上）
- スワイプ可能なセクション

## 9. アクセシビリティ

### カラーコントラスト
- WCAG AA準拠（4.5:1以上）
- フォーカスインジケーター
- カラーのみに依存しない情報伝達

### キーボードナビゲーション
- タブ順序の最適化
- フォーカス可能な要素の明確な表示
- スキップリンクの提供

## 10. 実装ガイドライン

### CSS変数の使用
```css
:root {
  /* カラーパレット */
  --primary-gradient: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  --primary-blue: #4F46E5;
  --primary-purple: #7C3AED;
  
  /* タイポグラフィ */
  --font-primary: 'Inter', sans-serif;
  
  /* スペーシング */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
}
```

### コンポーネント優先設計
- 再利用可能なコンポーネント
- 一貫性のあるデザインシステム
- メンテナンスしやすい構造

---

**作成日**: 2024年12月19日  
**バージョン**: 1.0  
**ブランド**: AI Collections 