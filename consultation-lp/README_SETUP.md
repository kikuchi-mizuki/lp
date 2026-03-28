# スプレッドシート自動セットアップガイド

このガイドでは、Google Sheetsに自動でシートを追加してサンプルデータを投入する方法を説明します。

## 🚀 クイックスタート

### 1. 認証情報を設定

`.env.local`ファイルに以下を設定してください：

```env
# スプレッドシート設定
GOOGLE_SPREADSHEET_ID=15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M
GOOGLE_SHEET_NAME=相談LP事例

# 認証情報（元のLPのRailway環境変数から取得）
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
```

### 2. スプレッドシートのセットアップを実行

```bash
npm run setup-sheet
```

このコマンドを実行すると、自動で以下が行われます：

1. ✅ スプレッドシートに「相談LP事例」シートを追加
2. ✅ ヘッダー行を追加（太字・背景色付き）
3. ✅ サンプルデータ3件を追加
4. ✅ 列幅を自動調整

## 📋 実行結果例

```
🚀 スプレッドシートのセットアップを開始します...

📋 スプレッドシートID: 15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M
📄 シート名: 相談LP事例

✨ 新しいシート「相談LP事例」を作成します...

✅ シートを作成しました
✅ ヘッダー行を追加しました
✅ サンプルデータを3件追加しました
✅ ヘッダー行のフォーマットを設定しました

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 セットアップが完了しました！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 スプレッドシートURL:
https://docs.google.com/spreadsheets/d/15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M/edit#gid=123456789

次のステップ:
1. スプレッドシートを開いて確認
2. 必要に応じてデータを編集
3. http://localhost:3001/consultation#cases で表示確認
```

## 🔄 既存シートがある場合

既に「相談LP事例」シートが存在する場合、スクリプトは以下の動作をします：

```
⚠️  シート「相談LP事例」は既に存在します
既存のシートをクリアしてデータを再投入します...

✅ ヘッダー行を追加しました
✅ サンプルデータを3件追加しました
```

既存データは上書きされるので注意してください。

## 📊 追加されるサンプルデータ

以下の3件のサンプルデータが自動で追加されます：

### 1. 月次報告書作成の自動化
- 対象: 製造業・経理部門
- 結果: 作業時間を90%削減（3時間→15分）

### 2. 顧客問い合わせ対応の自動化
- 対象: 小売業・カスタマーサポート
- 結果: 顧客満足度30%向上

### 3. 在庫管理の効率化
- 対象: 卸売業・在庫管理部門
- 結果: 発注業務の時間を70%削減

---

## 🎬 画像・動画URLの設定方法（元のLPと同じ）

### 方法1: K列（status）にURLを入れる（元のLPと同じ）

**元のLPと全く同じ使い方です。**

K列（status）に画像や動画のURLを入れると、自動的に検出されます：

```
case-001 | タイトル | ... | https://www.youtube.com/watch?v=VIDEO_ID
```

#### 自動検出される形式

**画像URL（サムネイルとして表示）:**
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`で終わるURL
- `cdn.`, `s3.`, `vercel.app`, `cloudinary.com`などを含むURL

**動画URL（詳細モーダルで再生）:**
- YouTube URL: `youtube.com`, `youtu.be`
- Vimeo URL: `vimeo.com`
- 動画ファイル: `.mp4`, `.webm`, `.mov`, `.ogg`

### 方法2: I列・J列に直接入れる（推奨）

より明示的に設定したい場合：

- **I列（thumbnailUrl）**: 画像URL
- **J列（videoUrl）**: 動画URL
- **K列（status）**: `active` または `inactive`

```
case-001 | タイトル | ... | https://example.com/thumb.jpg | https://youtube.com/... | active
```

### 対応している動画形式

#### 1. YouTube動画

以下のいずれの形式でもOK：

```
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://www.youtube.com/embed/VIDEO_ID
```

**例:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/dQw4w9WgXcQ
```

#### 2. Vimeo動画

```
https://vimeo.com/VIDEO_ID
```

**例:**
```
https://vimeo.com/123456789
```

#### 3. MP4などの動画ファイル

直接動画ファイルのURLを指定：

```
https://example.com/video.mp4
https://example.com/video.webm
https://example.com/video.ogg
```

#### 4. その他のURL

上記以外のURLは外部リンクとして表示されます。

### スプレッドシートでの設定例

| 列 | 値 |
|----|-----|
| J列 | https://www.youtube.com/watch?v=dQw4w9WgXcQ |

設定後、詳細モーダルを開くと動画が埋め込まれて表示されます。

---

## ⚠️ トラブルシューティング

### エラー: 認証情報が設定されていません

```
❌ エラー: Google Sheets APIの認証情報が設定されていません
```

**解決方法:**
`.env.local`ファイルに`GOOGLE_SERVICE_ACCOUNT_EMAIL`と`GOOGLE_PRIVATE_KEY`を設定してください。

---

### エラー: 権限エラー (403)

```
❌ エラーが発生しました: The caller does not have permission
```

**解決方法:**
1. スプレッドシートをサービスアカウントと共有しているか確認
2. サービスアカウントのメールアドレスで共有設定を確認
3. 権限は「閲覧者」または「編集者」に設定

---

### エラー: スプレッドシートが見つかりません (404)

```
❌ エラーが発生しました: Requested entity was not found
```

**解決方法:**
1. `GOOGLE_SPREADSHEET_ID`が正しいか確認
2. スプレッドシートのURLからIDを再度コピー

---

## 🔧 カスタマイズ

### シート名を変更する

`.env.local`で`GOOGLE_SHEET_NAME`を変更：

```env
GOOGLE_SHEET_NAME=カスタムシート名
```

### サンプルデータを変更する

`scripts/setup-spreadsheet.ts`の`sampleData`配列を編集してください。

---

## 📝 次のステップ

1. スプレッドシートを開いて確認
   ```
   https://docs.google.com/spreadsheets/d/15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M/edit
   ```

2. データを追加・編集
   - 新しい行を追加してケーススタディを増やす
   - 既存データを実際の事例に置き換える

3. ページで表示確認
   ```
   http://localhost:3001/consultation#cases
   ```

---

## 🆘 サポート

詳細なセットアップ手順は`GOOGLE_SHEETS_SETUP.md`を参照してください。
