# 強制再デプロイの手順

環境変数を設定したのにサンプルデータが返される場合、強制的に再デプロイを実行してください。

## 🔄 手順

### 方法1: Railwayダッシュボードから再デプロイ

1. Railway Dashboard → プロジェクトを選択
2. **Deployments** タブをクリック
3. 右上の **"..."** (More Options) → **Redeploy** をクリック
4. デプロイが完了するまで待つ（通常2-5分）
5. 完了後、以下のURLにアクセス：
   ```
   https://gracious-happiness-production.up.railway.app/api/cases
   ```

### 方法2: 空のコミットをプッシュして再デプロイ

ローカルで以下を実行：

```bash
cd /Users/kikuchimizuki/Desktop/aicollections_2/lp-main
git commit --allow-empty -m "chore: trigger Railway redeploy"
git push origin main
```

Railwayが自動的に新しいデプロイを開始します。

### 方法3: 環境変数を一時的に変更して再デプロイ

1. Railway Dashboard → **Variables**
2. 適当な環境変数（例：NEXT_PUBLIC_SITE_URL）を一時的に編集
3. 値の末尾にスペースを1つ追加して保存
4. 再デプロイが始まるのを待つ
5. デプロイ完了後、スペースを削除して再度保存

---

## ✅ 再デプロイ後の確認

1. **Deployments** タブで最新のデプロイが **緑色のチェックマーク** になるまで待つ
2. ブラウザで以下のURLにアクセス：
   ```
   https://gracious-happiness-production.up.railway.app/api/cases
   ```
3. レスポンスを確認：
   - **成功:** `"id": "case-001"` のような実際のデータ
   - **失敗:** `"id": "sample-001"` のようなサンプルデータ

---

## 🔍 それでも解決しない場合

### Railwayのログを確認

1. **Deployments** → 最新のデプロイ → **Logs**
2. 以下のメッセージを探す：
   - `GOOGLE_SPREADSHEET_ID not configured`
   - `Google Sheets client not configured`
   - `Error fetching cases from Google Sheets`
   - `Error:` で始まる行

3. エラーメッセージを全文コピーして共有してください

### コンソールログでデバッグ

ブラウザの開発者ツール（F12）を開いて：

1. **Console** タブを開く
2. `/api/cases` にアクセス
3. エラーメッセージがあれば共有
