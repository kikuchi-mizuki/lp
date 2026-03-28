# Google Sheets連携セットアップガイド

このドキュメントでは、導入事例をGoogleスプレッドシートで管理する方法を説明します。

## 目次

1. [Googleスプレッドシートの準備](#1-googleスプレッドシートの準備)
2. [Google Cloud Platform設定](#2-google-cloud-platform設定)
3. [環境変数の設定](#3-環境変数の設定)
4. [スプレッドシートのフォーマット](#4-スプレッドシートのフォーマット)

---

## 1. Googleスプレッドシートの準備

### スプレッドシートの作成

1. [Google Sheets](https://sheets.google.com/)で新しいスプレッドシートを作成
2. シート名は「Sheet1」のまま（またはコード内で変更可能）
3. URLから **スプレッドシートID** をコピー
   ```
   https://docs.google.com/spreadsheets/d/【このIDをコピー】/edit
   ```

---

## 2. Google Cloud Platform設定

### サービスアカウントの作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）
3. 「APIとサービス」→「認証情報」に移動
4. 「認証情報を作成」→「サービスアカウント」を選択
5. サービスアカウント名を入力（例: consultation-lp-sheets）
6. 「作成して続行」をクリック
7. ロールは不要（スキップ）
8. 「完了」をクリック

### サービスアカウントキーの作成

1. 作成したサービスアカウントをクリック
2. 「キー」タブに移動
3. 「鍵を追加」→「新しい鍵を作成」
4. キーのタイプは「JSON」を選択
5. 「作成」をクリック
6. JSONファイルがダウンロードされます（**安全に保管**）

### Google Sheets APIの有効化

1. 「APIとサービス」→「ライブラリ」に移動
2. 「Google Sheets API」を検索
3. 「有効にする」をクリック

### スプレッドシートの共有

1. 作成したスプレッドシートを開く
2. 右上の「共有」をクリック
3. サービスアカウントのメールアドレスを追加
   ```
   your-service-account@your-project.iam.gserviceaccount.com
   ```
4. 権限を「編集者」または「閲覧者」に設定（閲覧者で十分）
5. 「送信」をクリック

---

## 3. 環境変数の設定

`.env.local`ファイルに以下の環境変数を追加します。

```env
# Google Sheets API設定
GOOGLE_SPREADSHEET_ID=15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M
GOOGLE_SHEET_NAME=相談LP事例
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nyour_private_key_here\n-----END PRIVATE KEY-----
```

### 設定値の取得方法

1. **GOOGLE_SPREADSHEET_ID**: スプレッドシートのURLから取得
   - 例：`https://docs.google.com/spreadsheets/d/【このID】/edit`
   - 上記の例では`15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M`

2. **GOOGLE_SHEET_NAME**: スプレッドシート内のシート名（タブ名）
   - 元のLPと同じスプレッドシートを使う場合、別のシート名を指定
   - 例：`相談LP事例`、`ConsultationCases`など
   - 省略した場合は`Sheet1`が使用されます

3. **GOOGLE_SERVICE_ACCOUNT_EMAIL**: ダウンロードしたJSONファイルの`client_email`フィールド

4. **GOOGLE_PRIVATE_KEY**: ダウンロードしたJSONファイルの`private_key`フィールド
   - **注意**: `\n`は改行を表します。そのまま含めてください

### JSONファイルからの取得例

```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...このテキストをコピー...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  ...
}
```

---

## 4. スプレッドシートのフォーマット

### 列構成（Sheet1）

スプレッドシートの1行目（ヘッダー行）に以下の列名を設定してください：

| 列 | 列名 | 説明 | 必須 | 例 |
|----|------|------|------|-----|
| A | id | 一意のID | ✅ | case-001 |
| B | title | 導入事例のタイトル | ✅ | 月次報告書作成を自動化し、3時間削減 |
| C | target | 対象業種・職種 | ✅ | 製造業・経理部門 |
| D | catchCopy | キャッチコピー | ❌ | Excelの手作業から解放されました |
| E | beforeProblem | 導入前の課題 | ❌ | 毎月の報告書作成に3時間かかっていた |
| F | solution | 解決策 | ❌ | RPAツールでExcel作業を自動化 |
| G | result | 導入後の効果 | ✅ | 作業時間を90%削減、3時間→15分に短縮 |
| H | detailText | 詳細説明 | ❌ | より詳しい説明や背景情報 |
| I | thumbnailUrl | サムネイル画像URL | ❌ | https://example.com/image.jpg |
| J | videoUrl | 動画URL | ❌ | https://youtube.com/watch?v=... |
| K | status | ステータス | ❌ | active / inactive |

### データ入力例

```
A列(id)          | B列(title)                      | C列(target)      | D列(catchCopy)
-----------------|---------------------------------|------------------|------------------
case-001         | 月次報告書作成を3時間削減       | 製造業・経理部門 | 手作業から解放
case-002         | 顧客対応を自動化し即レス実現    | 小売業・CS部門   | 24時間対応可能に
```

```
E列(beforeProblem)                        | F列(solution)                   | G列(result)
------------------------------------------|----------------------------------|------------------
毎月3時間かけて手作業でExcel報告書作成   | RPAで自動化                      | 作業時間90%削減
問い合わせ対応が営業時間内のみ          | チャットボット導入               | 顧客満足度30%向上
```

```
H列(detailText)      | I列(thumbnailUrl)              | J列(videoUrl)  | K列(status)
---------------------|--------------------------------|----------------|-------------
詳細な説明テキスト   | https://example.com/thumb.jpg  |                | active
                     |                                |                | active
```

### ステータスについて

- **active**: 公開する事例（デフォルト）
- **inactive**: 非公開の事例（ページに表示されません）
- 空欄の場合は自動的に「active」として扱われます

### 画像・動画URLについて

- **thumbnailUrl**: カード表示用のサムネイル画像
  - 推奨サイズ: 800×450px以上
  - 形式: JPG, PNG, WebP

- **videoUrl**: 詳細モーダルで表示する動画（将来の実装用）
  - YouTube, Vimeoなどの埋め込みURLを想定

---

## トラブルシューティング

### エラー: "Google Sheets API credentials not configured"

- `.env.local`の環境変数が正しく設定されているか確認
- サーバーを再起動（`npm run dev`を再実行）

### エラー: "The caller does not have permission"

- サービスアカウントにスプレッドシートの共有権限が付与されているか確認
- スプレッドシートの「共有」設定を再確認

### データが表示されない

- スプレッドシートのシート名が「Sheet1」か確認（違う場合はコードで変更）
- `status`列が「active」になっているか確認
- 必須項目（id, title, target, result）が入力されているか確認

### private_keyのエラー

- `GOOGLE_PRIVATE_KEY`に`\n`が含まれているか確認
- JSONから直接コピーした値をそのまま使用（余計な改行を追加しない）

---

## 元のLPとの統合

この設定は元のAIコレクションズLPと同じスプレッドシートを使用できます：

### 同じスプレッドシート、別シートを使用する方法（推奨）

1. 元のLPで使用しているスプレッドシートIDを確認
   - 例：`15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M`

2. スプレッドシート内に新しいシート（タブ）を追加
   - スプレッドシートを開く
   - 左下の「+」ボタンで新しいシートを追加
   - シート名を「相談LP事例」などに変更

3. `.env.local`に設定
   ```env
   GOOGLE_SPREADSHEET_ID=15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M
   GOOGLE_SHEET_NAME=相談LP事例
   ```

4. 同じサービスアカウント認証情報を使用

**メリット：**
- 1つのスプレッドシートで両方のLPを管理
- 元のLPのデータと分離して管理
- シート間でデータをコピーしやすい

---

## 次のステップ

1. スプレッドシートにサンプルデータを入力
2. 開発サーバーを起動: `npm run dev`
3. http://localhost:3001/consultation#cases にアクセス
4. 導入事例が正しく表示されるか確認

---

## 参考リンク

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Cloud Console](https://console.cloud.google.com/)
- [googleapis npm package](https://www.npmjs.com/package/googleapis)
