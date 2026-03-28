-- ================================================================
-- AIコレクションズ - 業務改善無料相談LP
-- 初期スキーマ
-- ================================================================

-- ================================================================
-- 1. 事例テーブル (cases)
-- ================================================================
CREATE TABLE IF NOT EXISTS cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  target TEXT NOT NULL,
  catch_copy TEXT NOT NULL,
  before_problem TEXT NOT NULL,
  solution TEXT NOT NULL,
  result TEXT NOT NULL,
  detail_text TEXT,
  thumbnail_url TEXT,
  video_url TEXT,
  tags TEXT[] DEFAULT '{}',
  sort_order INTEGER DEFAULT 0,
  is_published BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_cases_published ON cases(is_published, sort_order, created_at);
CREATE INDEX IF NOT EXISTS idx_cases_sort_order ON cases(sort_order);

-- updated_at 自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cases_updated_at
  BEFORE UPDATE ON cases
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- 2. 相談リードテーブル (consultation_leads)
-- ================================================================
CREATE TABLE IF NOT EXISTS consultation_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  inquiry TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_consultation_leads_created_at ON consultation_leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consultation_leads_email ON consultation_leads(email);

-- ================================================================
-- 3. Row Level Security (RLS) の設定
-- ================================================================

-- casesテーブルのRLS有効化
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

-- 公開事例は誰でも閲覧可能
CREATE POLICY "Public cases are viewable by everyone"
  ON cases
  FOR SELECT
  USING (is_published = true);

-- 認証済みユーザーは全ての事例を閲覧可能（管理画面用）
CREATE POLICY "Authenticated users can view all cases"
  ON cases
  FOR SELECT
  TO authenticated
  USING (true);

-- 認証済みユーザーは事例を挿入可能
CREATE POLICY "Authenticated users can insert cases"
  ON cases
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- 認証済みユーザーは事例を更新可能
CREATE POLICY "Authenticated users can update cases"
  ON cases
  FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- 認証済みユーザーは事例を削除可能
CREATE POLICY "Authenticated users can delete cases"
  ON cases
  FOR DELETE
  TO authenticated
  USING (true);

-- consultation_leadsテーブルのRLS有効化
ALTER TABLE consultation_leads ENABLE ROW LEVEL SECURITY;

-- 誰でも相談リードを挿入可能（フォーム送信用）
CREATE POLICY "Anyone can insert consultation leads"
  ON consultation_leads
  FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

-- 認証済みユーザーのみ相談リードを閲覧可能（管理画面用）
CREATE POLICY "Authenticated users can view consultation leads"
  ON consultation_leads
  FOR SELECT
  TO authenticated
  USING (true);

-- ================================================================
-- 4. サンプルデータ（開発用）
-- ================================================================

INSERT INTO cases (
  title,
  target,
  catch_copy,
  before_problem,
  solution,
  result,
  detail_text,
  thumbnail_url,
  tags,
  sort_order,
  is_published
) VALUES
(
  '請求書作成を90%自動化',
  '経理部門2名の小規模EC事業者',
  '月100時間かかっていた請求書作成が、わずか10時間に',
  '毎月の請求書作成に100時間以上を費やし、本来の業務に集中できない状態でした。手作業でのミスも多発し、取引先からの問い合わせ対応にも追われていました。',
  'AI-OCRとRPAを組み合わせた自動請求書生成システムを導入。取引データを自動抽出し、テンプレートに沿って請求書を生成。承認フローも電子化しました。',
  '請求書作成時間を90%削減（100時間→10時間）。ミス率も95%減少し、取引先からのクレームがゼロに。浮いた時間で新規取引先開拓に注力できるようになりました。',
  'システム導入前は、ExcelとWordで1件ずつ請求書を作成していました。導入後は、売上データをアップロードするだけで自動生成されるため、経理担当者は確認作業のみに専念できます。初期費用は3ヶ月で回収できました。',
  '/images/cases/case-invoice.jpg',
  ARRAY['自動化', 'RPA', 'AI-OCR', '経理業務'],
  1,
  true
),
(
  '顧客対応の効率化で残業時間70%削減',
  'カスタマーサポート5名の小売業',
  'AIチャットボット導入で、深夜対応から解放',
  '問い合わせ対応に追われ、月平均50時間の残業が発生。夜間の問い合わせにも対応するため、交代制のシフトを組んでいましたが、スタッフの負担が大きい状況でした。',
  'よくある質問を学習したAIチャットボットを導入。24時間自動対応を実現し、複雑な問い合わせのみ人間が対応する仕組みに変更しました。',
  '問い合わせ対応時間を60%削減。残業時間も70%減少し、スタッフの満足度が大幅に向上。顧客満足度も、即座に回答が得られることで15%向上しました。',
  'チャットボットは簡単な質問（営業時間、配送状況など）の80%に自動対応。残り20%の複雑な質問のみ、翌営業日にスタッフが対応します。導入から6ヶ月でROI300%を達成しました。',
  '/images/cases/case-chatbot.jpg',
  ARRAY['AIチャットボット', 'カスタマーサポート', '残業削減'],
  2,
  true
),
(
  'スケジュール調整を自動化し、月20時間を創出',
  '営業チーム10名のBtoB企業',
  '営業の商談設定が自動化され、成約率も20%向上',
  '顧客とのアポイント調整に、1件あたり平均30分を要していました。メールのやり取りが往復し、スケジュール確定までに数日かかることも。営業担当者の本来の業務時間が圧迫されていました。',
  '自動スケジュール調整ツール（Calendly連携）を導入。顧客が空き時間を選んで予約できる仕組みを構築。リマインダー機能も追加しました。',
  'アポイント調整時間を90%削減（月20時間創出）。キャンセル率も40%減少し、成約率が20%向上。営業担当者は商談準備により多くの時間を割けるようになりました。',
  '顧客には専用リンクを送るだけで、自動的にカレンダーの空き時間が表示されます。予約確定後は自動でZoomリンクが発行され、前日にリマインドメールも送信されます。営業チーム全体で月200時間以上を創出しました。',
  '/images/cases/case-scheduling.jpg',
  ARRAY['スケジュール自動化', '営業効率化', 'Calendly'],
  3,
  true
);

-- ================================================================
-- 5. ストレージバケット作成（Supabase管理画面で実行）
-- ================================================================
-- 以下はSupabase管理画面のStorageセクションで作成してください
-- Bucket名: case-thumbnails
-- Public: true
-- File size limit: 5MB
-- Allowed MIME types: image/jpeg, image/png, image/webp

COMMENT ON TABLE cases IS '事例マスタ - 業務改善事例を管理';
COMMENT ON TABLE consultation_leads IS '相談リード - 無料相談フォームからの問い合わせを管理';
