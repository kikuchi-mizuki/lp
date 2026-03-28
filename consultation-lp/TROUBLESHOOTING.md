# トラブルシューティングガイド

本番環境でスプレッドシートの内容が反映されない場合の確認手順です。

## 📋 チェックリスト

### 1. Railway環境変数の確認

Railwayのダッシュボードで **Variables** タブを開き、以下が正しく設定されているか確認：

- [ ] `GOOGLE_PRIVATE_KEY_BASE64` - Base64エンコードされた秘密鍵（長い文字列）
- [ ] `GOOGLE_SPREADSHEET_ID` - `15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M`
- [ ] `GOOGLE_SHEET_NAME` - `相談LP事例`
- [ ] `GOOGLE_SERVICE_ACCOUNT_EMAIL` - `aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com`

**重要**: 環境変数を変更した後は、必ずRailwayが自動で再デプロイするのを待ってください。

### 2. デプロイログの確認

Railwayで **Deployments** → 最新のデプロイ → **Logs** を確認：

#### 正常な場合のログ例
```
✓ Built successfully
Starting server...
Server listening on port 3001
```

#### エラーがある場合
以下のようなエラーメッセージを探してください：

```
Error: The caller does not have permission
→ スプレッドシートの共有設定を確認

Error: Requested entity was not found
→ スプレッドシートIDまたはシート名を確認

Error: Failed to decode base64 private key
→ GOOGLE_PRIVATE_KEY_BASE64の値を確認
```

### 3. スプレッドシートの共有設定

1. [スプレッドシート](https://docs.google.com/spreadsheets/d/15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M/edit)を開く
2. 右上の **共有** ボタンをクリック
3. 以下のメールアドレスが追加されているか確認：
   ```
   aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com
   ```
4. 権限が **閲覧者** 以上になっているか確認

**追加されていない場合：**
1. 共有ウィンドウで上記のメールアドレスを入力
2. 権限を「閲覧者」または「編集者」に設定
3. 「送信」をクリック

### 4. スプレッドシートのシート名とデータ

1. スプレッドシートを開く
2. 下部のタブに **「相談LP事例」** というシート名があるか確認
3. そのシートを開いて：
   - 1行目にヘッダー（id, title, target, ...）があるか確認
   - 2行目以降にデータが入っているか確認
   - K列（status）が「active」または空欄になっているか確認

**シート名が違う場合：**
- Railwayで `GOOGLE_SHEET_NAME` 環境変数を実際のシート名に変更

### 5. APIエンドポイントのテスト

ブラウザまたはcurlで以下のURLにアクセス：

```
https://your-app.up.railway.app/api/cases
```

#### 正常な場合
```json
{
  "success": true,
  "cases": [
    {
      "id": "case-001",
      "title": "...",
      ...
    }
  ],
  "count": 3
}
```

#### サンプルデータが返ってくる場合
```json
{
  "success": true,
  "cases": [
    {
      "id": "sample-001",
      "title": "月次報告書作成を自動化...",
      ...
    }
  ]
}
```

→ これは環境変数が正しく設定されていないか、スプレッドシートにアクセスできていない証拠です。

#### エラーが返ってくる場合
```json
{
  "success": false,
  "error": "Failed to fetch cases"
}
```

→ Railwayのログを確認して、具体的なエラーメッセージを探してください。

### 6. 環境変数の値を再確認

#### GOOGLE_PRIVATE_KEY_BASE64
- ローカルで再度生成：
  ```bash
  npm run encode-key
  ```
- 出力されたBase64文字列をRailwayの環境変数に設定
- **改行なし**の1行の文字列であることを確認

#### GOOGLE_SPREADSHEET_ID
- スプレッドシートのURLから取得：
  ```
  https://docs.google.com/spreadsheets/d/【このID】/edit
  ```
- 正しいIDは: `15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M`

#### GOOGLE_SHEET_NAME
- スプレッドシートの下部タブに表示されているシート名と完全一致しているか確認
- 正しいシート名: `相談LP事例`

### 7. キャッシュのクリア

Railwayで強制的に再デプロイ：

1. Railwayのダッシュボードを開く
2. **Deployments** タブ
3. 右上の **Deploy** ボタン → **Redeploy**
4. デプロイが完了するまで待つ（通常2-5分）

### 8. ローカルで環境変数をテスト

.env.localに本番と同じ環境変数を設定して、ローカルでテスト：

```bash
npm run check-env
```

問題があれば表示されます。

```bash
npm run dev
```

開発サーバーを起動して、`http://localhost:3001/api/cases` にアクセス。

正常に動作する場合は、Railway側の設定問題です。

---

## 🆘 それでも解決しない場合

### Railwayのログを確認

1. Railway → **Deployments** → 最新のデプロイ
2. **Logs** タブを開く
3. エラーメッセージをすべてコピー
4. 以下の情報と一緒に共有：
   - エラーメッセージ全文
   - `/api/cases` にアクセスしたときのレスポンス
   - 環境変数が4つすべて設定されているか（値は見せない、設定済みかどうかのみ）

### デバッグ用の環境変数を追加

一時的にデバッグログを有効にする：

```
NODE_ENV=production
DEBUG=*
```

これにより、より詳細なログがRailwayに出力されます。

---

## 💡 よくある問題と解決方法

### 問題1: サンプルデータが表示される

**原因**: Google Sheets APIにアクセスできていない

**解決方法**:
1. 環境変数 `GOOGLE_PRIVATE_KEY_BASE64` を確認
2. スプレッドシートの共有設定を確認
3. サービスアカウントのメールアドレスが正しいか確認

### 問題2: 「導入事例がありません」と表示される

**原因**: スプレッドシートからデータを取得できているが、フィルタリングされている

**解決方法**:
1. スプレッドシートの K列（status）が「inactive」になっていないか確認
2. 必須項目（id, title, target）がすべて入力されているか確認
3. シート名が「相談LP事例」と完全一致しているか確認

### 問題3: エラーメッセージ「The caller does not have permission」

**原因**: サービスアカウントがスプレッドシートにアクセスする権限がない

**解決方法**:
1. スプレッドシートの共有設定を開く
2. `aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com` を追加
3. 権限を「閲覧者」以上に設定

### 問題4: 環境変数を変更しても反映されない

**原因**: 環境変数の変更後、再デプロイが必要

**解決方法**:
1. 環境変数を保存
2. Railwayが自動で再デプロイするのを待つ（通常1-3分）
3. または手動で **Redeploy** をクリック
