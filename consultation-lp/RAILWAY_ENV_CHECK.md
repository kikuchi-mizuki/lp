# Railway環境変数の再確認手順

サンプルデータが返されている場合、環境変数の値が間違っている可能性があります。

## 📋 確認手順

### 1. Railwayで環境変数を開く

1. Railway Dashboard → プロジェクト選択
2. **Variables** タブをクリック
3. 以下の4つの環境変数が存在するか確認

### 2. 各環境変数の値を確認

#### ✅ GOOGLE_SPREADSHEET_ID

**期待される値:**
```
15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M
```

**確認方法:**
- 先頭と末尾の数文字が一致するか確認
- スペースや改行が入っていないか確認
- 余分な引用符（`"` や `'`）が付いていないか確認

#### ✅ GOOGLE_SHEET_NAME

**期待される値:**
```
相談LP事例
```

**確認方法:**
- **完全一致**しているか確認（スペースや全角半角に注意）
- スプレッドシートの下部タブの名前と完全に同じか
- 余分なスペースがないか

#### ✅ GOOGLE_SERVICE_ACCOUNT_EMAIL

**期待される値:**
```
aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com
```

**確認方法:**
- スペルミスがないか
- スペースや改行が入っていないか
- `@` や `.` が正しく入っているか

#### ✅ GOOGLE_PRIVATE_KEY_BASE64

**期待される値の特徴:**
- **非常に長い文字列**（800文字以上）
- 先頭が `LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t` で始まる
- 末尾が `0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0=` で終わる
- **改行が含まれていない**（1行の文字列）

**よくある間違い:**
- ❌ 改行が含まれている（複数行になっている）
- ❌ `-----BEGIN PRIVATE KEY-----` をそのまま貼り付けている（Base64エンコードしていない）
- ❌ コピー時に一部が欠けている

**正しい値の例（先頭と末尾）:**
```
LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t...（中略）...0tLS0tRU5EIFBSSVWQVRFIEtFWS0tLS0t=
```

### 3. 環境変数が間違っている場合の修正手順

#### GOOGLE_PRIVATE_KEY_BASE64を修正する場合

1. **ローカルで再生成:**
   ```bash
   cd consultation-lp
   npm run encode-key
   ```

2. **出力されたBase64文字列をコピー:**
   ```bash
   cat scripts/.base64-key.txt | pbcopy
   ```
   または手動でファイルを開いてコピー

3. **Railwayで更新:**
   - Variables → GOOGLE_PRIVATE_KEY_BASE64 の **Edit** をクリック
   - 古い値を全て削除
   - 新しいBase64文字列を貼り付け（**1行で**）
   - **Save** をクリック

4. **自動再デプロイを待つ:**
   - 環境変数を保存すると、Railwayが自動的に再デプロイします
   - Deployments タブで進行状況を確認
   - 通常2-5分で完了

#### その他の環境変数を修正する場合

1. Variables → 該当の環境変数の **Edit** をクリック
2. 正しい値に修正
3. **Save** をクリック
4. 自動再デプロイを待つ

### 4. 再デプロイ後の確認

デプロイ完了後（緑色のチェックマーク）、以下のURLにアクセス：

```
https://gracious-happiness-production.up.railway.app/api/cases
```

**成功した場合:**
- `"id": "case-001"` のような実際のデータが返される
- `"id": "sample-001"` ではなくなる

**まだサンプルデータが返される場合:**
- Railwayのログを確認（次のステップ）

### 5. Railwayのログを確認

1. Railway Dashboard → **Deployments** タブ
2. 最新のデプロイをクリック
3. **Logs** タブを開く
4. 以下のようなエラーメッセージを探す：

#### エラーメッセージの例と対処法

**エラー1: 認証情報が設定されていない**
```
GOOGLE_SPREADSHEET_ID not configured, returning sample data
```
→ `GOOGLE_SPREADSHEET_ID` が設定されていないか、ダミー値のまま

**エラー2: Google Sheets APIクライアントが初期化できない**
```
Google Sheets client not configured, returning sample data
```
→ `GOOGLE_PRIVATE_KEY_BASE64` または `GOOGLE_SERVICE_ACCOUNT_EMAIL` が正しくない

**エラー3: 権限エラー**
```
Error: The caller does not have permission
```
→ スプレッドシートの共有設定を再確認

**エラー4: スプレッドシートが見つからない**
```
Error: Requested entity was not found
```
→ `GOOGLE_SPREADSHEET_ID` が間違っている

**エラー5: シートが見つからない**
```
Error: Unable to parse range: Sheet1!A2:K100
```
→ `GOOGLE_SHEET_NAME` が間違っている

### 6. 環境変数をすべて削除して再設定

それでも解決しない場合、環境変数を一度すべて削除して再設定：

1. **Variables** タブで以下を削除:
   - GOOGLE_PRIVATE_KEY_BASE64
   - GOOGLE_SPREADSHEET_ID
   - GOOGLE_SHEET_NAME
   - GOOGLE_SERVICE_ACCOUNT_EMAIL

2. **新規追加:**
   - **New Variable** をクリック
   - 以下を1つずつ追加:

```
GOOGLE_SPREADSHEET_ID
15yjq73FUIiNKtZGmNQgOorTthaEpd0-NYZ-XChJ0r5M

GOOGLE_SHEET_NAME
相談LP事例

GOOGLE_SERVICE_ACCOUNT_EMAIL
aicollections@numeric-scope-456509-t3.iam.gserviceaccount.com

GOOGLE_PRIVATE_KEY_BASE64
（npm run encode-keyで生成したBase64文字列を貼り付け）
```

3. すべて追加したら、自動再デプロイを待つ

### 7. 最終確認のチェックリスト

- [ ] 4つの環境変数がすべて存在する
- [ ] GOOGLE_PRIVATE_KEY_BASE64が1行の長い文字列（改行なし）
- [ ] GOOGLE_SPREADSHEET_IDに余分なスペースや引用符がない
- [ ] GOOGLE_SHEET_NAMEがスプレッドシートのタブ名と完全一致
- [ ] デプロイが成功している（緑色）
- [ ] `/api/cases` でサンプルデータではなく実データが返される

---

## 🆘 それでも解決しない場合

Railwayのログ（Deployments → 最新のデプロイ → Logs）をスクリーンショットまたはテキストで共有してください。エラーメッセージから具体的な問題を特定できます。
