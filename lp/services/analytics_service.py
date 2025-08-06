import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.company_service import CompanyService
from lp.services.dashboard_service import dashboard_service

class AnalyticsService:
    """高度な分析サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.company_service = CompanyService()
        
        # 分析設定
        self.analytics_config = {
            'prediction': {
                'enabled': True,
                'forecast_periods': 12,  # 12ヶ月先まで予測
                'confidence_level': 0.95,
                'min_data_points': 6
            },
            'anomaly_detection': {
                'enabled': True,
                'threshold_multiplier': 2.0,
                'window_size': 30,  # 30日間のウィンドウ
                'sensitivity': 'medium'
            },
            'reporting': {
                'enabled': True,
                'auto_generate': True,
                'schedule': 'weekly',
                'format': 'pdf'
            }
        }
    
    def get_prediction_analytics(self, metric_type='revenue', company_id=None):
        """予測分析を実行"""
        try:
            # 過去データを取得
            historical_data = self._get_historical_data(metric_type, company_id)
            
            if len(historical_data) < self.analytics_config['prediction']['min_data_points']:
                return {
                    'success': False,
                    'error': f'予測に必要な最小データポイント数({self.analytics_config["prediction"]["min_data_points"]})に達していません'
                }
            
            # 時系列データをDataFrameに変換
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 予測モデルを構築
            forecast_data = self._build_forecast_model(df, metric_type)
            
            # 信頼区間を計算
            confidence_intervals = self._calculate_confidence_intervals(forecast_data)
            
            return {
                'success': True,
                'predictions': forecast_data,
                'confidence_intervals': confidence_intervals,
                'model_accuracy': self._calculate_model_accuracy(df, forecast_data),
                'trend_analysis': self._analyze_trend(df)
            }
            
        except Exception as e:
            self.logger.error(f"予測分析エラー: {e}")
            return {
                'success': False,
                'error': f'予測分析エラー: {str(e)}'
            }
    
    def get_anomaly_detection(self, metric_type='revenue', company_id=None):
        """異常検知を実行"""
        try:
            # 過去データを取得
            historical_data = self._get_historical_data(metric_type, company_id)
            
            if len(historical_data) < 10:
                return {
                    'success': False,
                    'error': '異常検知に必要なデータが不足しています'
                }
            
            # データをDataFrameに変換
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 異常検知を実行
            anomalies = self._detect_anomalies(df, metric_type)
            
            # 異常の重要度を評価
            severity_analysis = self._analyze_anomaly_severity(anomalies)
            
            return {
                'success': True,
                'anomalies': anomalies,
                'severity_analysis': severity_analysis,
                'detection_summary': self._summarize_anomalies(anomalies)
            }
            
        except Exception as e:
            self.logger.error(f"異常検知エラー: {e}")
            return {
                'success': False,
                'error': f'異常検知エラー: {str(e)}'
            }
    
    def generate_analytics_report(self, report_type='comprehensive', company_id=None):
        """分析レポートを生成"""
        try:
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'report_type': report_type,
                'company_id': company_id,
                'sections': {}
            }
            
            # 1. 概要統計
            report_data['sections']['overview'] = self._generate_overview_section(company_id)
            
            # 2. 予測分析
            if self.analytics_config['prediction']['enabled']:
                report_data['sections']['predictions'] = self._generate_prediction_section(company_id)
            
            # 3. 異常検知
            if self.analytics_config['anomaly_detection']['enabled']:
                report_data['sections']['anomalies'] = self._generate_anomaly_section(company_id)
            
            # 4. トレンド分析
            report_data['sections']['trends'] = self._generate_trend_section(company_id)
            
            # 5. 推奨事項
            report_data['sections']['recommendations'] = self._generate_recommendations_section(report_data)
            
            # レポートを保存
            report_filename = self._save_report(report_data, report_type, company_id)
            
            return {
                'success': True,
                'report_data': report_data,
                'filename': report_filename,
                'download_url': f'/api/v1/analytics/reports/{report_filename}'
            }
            
        except Exception as e:
            self.logger.error(f"レポート生成エラー: {e}")
            return {
                'success': False,
                'error': f'レポート生成エラー: {str(e)}'
            }
    
    def get_customer_segmentation(self, company_id=None):
        """顧客セグメンテーション分析"""
        try:
            # 顧客データを取得
            customers = self._get_customer_data(company_id)
            
            if not customers:
                return {
                    'success': False,
                    'error': '顧客データが見つかりません'
                }
            
            # セグメンテーション分析を実行
            segments = self._perform_customer_segmentation(customers)
            
            # セグメント別の特徴を分析
            segment_characteristics = self._analyze_segment_characteristics(segments)
            
            # セグメント別の推奨事項を生成
            segment_recommendations = self._generate_segment_recommendations(segments)
            
            return {
                'success': True,
                'segments': segments,
                'characteristics': segment_characteristics,
                'recommendations': segment_recommendations,
                'summary': self._summarize_segmentation(segments)
            }
            
        except Exception as e:
            self.logger.error(f"顧客セグメンテーションエラー: {e}")
            return {
                'success': False,
                'error': f'顧客セグメンテーションエラー: {str(e)}'
            }
    
    def get_churn_prediction(self, company_id=None):
        """解約予測分析"""
        try:
            # 顧客データを取得
            customers = self._get_customer_data(company_id)
            
            if not customers:
                return {
                    'success': False,
                    'error': '顧客データが見つかりません'
                }
            
            # 解約リスクを計算
            churn_risks = self._calculate_churn_risks(customers)
            
            # 解約要因を分析
            churn_factors = self._analyze_churn_factors(customers)
            
            # 解約防止策を提案
            prevention_strategies = self._generate_prevention_strategies(churn_risks, churn_factors)
            
            return {
                'success': True,
                'churn_risks': churn_risks,
                'churn_factors': churn_factors,
                'prevention_strategies': prevention_strategies,
                'summary': self._summarize_churn_analysis(churn_risks)
            }
            
        except Exception as e:
            self.logger.error(f"解約予測エラー: {e}")
            return {
                'success': False,
                'error': f'解約予測エラー: {str(e)}'
            }
    
    def _get_historical_data(self, metric_type, company_id=None):
        """過去データを取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if metric_type == 'revenue':
                # 収益データを取得
                if company_id:
                    c.execute('''
                        SELECT DATE(created_at) as date, SUM(amount) as value
                        FROM company_payments 
                        WHERE company_id = %s AND status = 'completed'
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    ''', (company_id,))
                else:
                    c.execute('''
                        SELECT DATE(created_at) as date, SUM(amount) as value
                        FROM company_payments 
                        WHERE status = 'completed'
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    ''')
            
            elif metric_type == 'subscriptions':
                # サブスクリプションデータを取得
                if company_id:
                    c.execute('''
                        SELECT DATE(created_at) as date, COUNT(*) as value
                        FROM company_payments 
                        WHERE company_id = %s AND status = 'active'
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    ''', (company_id,))
                else:
                    c.execute('''
                        SELECT DATE(created_at) as date, COUNT(*) as value
                        FROM company_payments 
                        WHERE status = 'active'
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    ''')
            
            elif metric_type == 'cancellations':
                # 解約データを取得
                if company_id:
                    c.execute('''
                        SELECT DATE(cancelled_at) as date, COUNT(*) as value
                        FROM company_cancellations 
                        WHERE company_id = %s
                        GROUP BY DATE(cancelled_at)
                        ORDER BY date
                    ''', (company_id,))
                else:
                    c.execute('''
                        SELECT DATE(cancelled_at) as date, COUNT(*) as value
                        FROM company_cancellations 
                        GROUP BY DATE(cancelled_at)
                        ORDER BY date
                    ''')
            
            results = c.fetchall()
            conn.close()
            
            # データを辞書のリストに変換
            data = []
            for row in results:
                data.append({
                    'date': row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                    'value': float(row[1])
                })
            
            return data
            
        except Exception as e:
            self.logger.error(f"過去データ取得エラー: {e}")
            return []
    
    def _build_forecast_model(self, df, metric_type):
        """予測モデルを構築"""
        try:
            # 簡単な線形回帰モデルを使用
            # 実際の実装ではより高度なモデル（ARIMA、Prophet等）を使用
            
            # 時系列インデックスを作成
            df = df.set_index('date')
            
            # トレンドを計算
            x = np.arange(len(df))
            y = df['value'].values
            
            # 線形回帰
            coeffs = np.polyfit(x, y, 1)
            
            # 将来の予測値を計算
            forecast_periods = self.analytics_config['prediction']['forecast_periods']
            future_x = np.arange(len(df), len(df) + forecast_periods)
            future_y = np.polyval(coeffs, future_x)
            
            # 予測データを作成
            forecast_data = []
            for i, (x_val, y_val) in enumerate(zip(future_x, future_y)):
                forecast_date = df.index[-1] + timedelta(days=30 * (i + 1))
                forecast_data.append({
                    'date': forecast_date.isoformat(),
                    'predicted_value': max(0, y_val),  # 負の値を防ぐ
                    'confidence': 0.85  # 簡易的な信頼度
                })
            
            return forecast_data
            
        except Exception as e:
            self.logger.error(f"予測モデル構築エラー: {e}")
            return []
    
    def _calculate_confidence_intervals(self, forecast_data):
        """信頼区間を計算"""
        try:
            confidence_level = self.analytics_config['prediction']['confidence_level']
            
            intervals = []
            for forecast in forecast_data:
                # 簡易的な信頼区間計算
                value = forecast['predicted_value']
                margin = value * 0.1  # 10%のマージン
                
                intervals.append({
                    'date': forecast['date'],
                    'lower_bound': max(0, value - margin),
                    'upper_bound': value + margin,
                    'confidence_level': confidence_level
                })
            
            return intervals
            
        except Exception as e:
            self.logger.error(f"信頼区間計算エラー: {e}")
            return []
    
    def _calculate_model_accuracy(self, df, forecast_data):
        """モデル精度を計算"""
        try:
            # 実際の値と予測値を比較
            actual_values = df['value'].values
            predicted_values = [f['predicted_value'] for f in forecast_data[:len(actual_values)]]
            
            if len(predicted_values) < len(actual_values):
                predicted_values.extend([predicted_values[-1]] * (len(actual_values) - len(predicted_values)))
            
            # 平均絶対誤差を計算
            mae = np.mean(np.abs(np.array(actual_values) - np.array(predicted_values)))
            
            # 平均絶対誤差率を計算
            mape = np.mean(np.abs((np.array(actual_values) - np.array(predicted_values)) / np.array(actual_values))) * 100
            
            return {
                'mae': float(mae),
                'mape': float(mape),
                'accuracy': max(0, 100 - mape)
            }
            
        except Exception as e:
            self.logger.error(f"モデル精度計算エラー: {e}")
            return {'mae': 0, 'mape': 0, 'accuracy': 0}
    
    def _analyze_trend(self, df):
        """トレンド分析を実行"""
        try:
            values = df['value'].values
            
            # 線形トレンドを計算
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            slope = coeffs[0]
            
            # トレンドの方向を判定
            if slope > 0:
                trend_direction = 'increasing'
                trend_strength = 'strong' if abs(slope) > np.std(values) else 'weak'
            elif slope < 0:
                trend_direction = 'decreasing'
                trend_strength = 'strong' if abs(slope) > np.std(values) else 'weak'
            else:
                trend_direction = 'stable'
                trend_strength = 'none'
            
            # 季節性を検出
            seasonality = self._detect_seasonality(values)
            
            return {
                'direction': trend_direction,
                'strength': trend_strength,
                'slope': float(slope),
                'seasonality': seasonality,
                'volatility': float(np.std(values))
            }
            
        except Exception as e:
            self.logger.error(f"トレンド分析エラー: {e}")
            return {}
    
    def _detect_seasonality(self, values):
        """季節性を検出"""
        try:
            if len(values) < 12:
                return 'insufficient_data'
            
            # 簡易的な季節性検出
            # 実際の実装ではFFTや自己相関を使用
            
            # 月次データの平均を計算
            monthly_means = []
            for i in range(12):
                month_data = values[i::12]
                if len(month_data) > 0:
                    monthly_means.append(np.mean(month_data))
                else:
                    monthly_means.append(0)
            
            # 季節性の強さを計算
            seasonal_variance = np.var(monthly_means)
            total_variance = np.var(values)
            
            if seasonal_variance / total_variance > 0.1:
                return 'strong'
            elif seasonal_variance / total_variance > 0.05:
                return 'moderate'
            else:
                return 'weak'
                
        except Exception as e:
            self.logger.error(f"季節性検出エラー: {e}")
            return 'unknown'
    
    def _detect_anomalies(self, df, metric_type):
        """異常を検出"""
        try:
            values = df['value'].values
            dates = df['date'].values
            
            # 移動平均と標準偏差を計算
            window_size = self.analytics_config['anomaly_detection']['window_size']
            threshold_multiplier = self.analytics_config['anomaly_detection']['threshold_multiplier']
            
            anomalies = []
            
            for i in range(window_size, len(values)):
                window = values[i-window_size:i]
                mean_val = np.mean(window)
                std_val = np.std(window)
                
                current_val = values[i]
                threshold = threshold_multiplier * std_val
                
                if abs(current_val - mean_val) > threshold:
                    anomalies.append({
                        'date': dates[i].isoformat() if hasattr(dates[i], 'isoformat') else str(dates[i]),
                        'value': float(current_val),
                        'expected_value': float(mean_val),
                        'deviation': float(current_val - mean_val),
                        'severity': 'high' if abs(current_val - mean_val) > 2 * threshold else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"異常検出エラー: {e}")
            return []
    
    def _analyze_anomaly_severity(self, anomalies):
        """異常の重要度を分析"""
        try:
            if not anomalies:
                return {'high': 0, 'medium': 0, 'low': 0}
            
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'medium')
                severity_counts[severity] += 1
            
            return severity_counts
            
        except Exception as e:
            self.logger.error(f"異常重要度分析エラー: {e}")
            return {'high': 0, 'medium': 0, 'low': 0}
    
    def _summarize_anomalies(self, anomalies):
        """異常の要約を作成"""
        try:
            if not anomalies:
                return "異常は検出されませんでした"
            
            total_anomalies = len(anomalies)
            high_severity = len([a for a in anomalies if a.get('severity') == 'high'])
            
            return f"{total_anomalies}件の異常を検出（高重要度: {high_severity}件）"
            
        except Exception as e:
            self.logger.error(f"異常要約エラー: {e}")
            return "異常要約の作成に失敗しました"
    
    def _get_customer_data(self, company_id=None):
        """顧客データを取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if company_id:
                c.execute('''
                    SELECT 
                        cp.company_id,
                        c.name,
                        c.industry,
                        c.employee_count,
                        cp.status,
                        cp.amount,
                        cp.created_at,
                        cp.updated_at
                    FROM company_payments cp
                    JOIN companies c ON cp.company_id = c.id
                    WHERE cp.company_id = %s
                    ORDER BY cp.created_at
                ''', (company_id,))
            else:
                c.execute('''
                    SELECT 
                        cp.company_id,
                        c.name,
                        c.industry,
                        c.employee_count,
                        cp.status,
                        cp.amount,
                        cp.created_at,
                        cp.updated_at
                    FROM company_payments cp
                    JOIN companies c ON cp.company_id = c.id
                    ORDER BY cp.created_at
                ''')
            
            results = c.fetchall()
            conn.close()
            
            customers = []
            for row in results:
                customers.append({
                    'company_id': row[0],
                    'name': row[1],
                    'industry': row[2],
                    'employee_count': row[3],
                    'status': row[4],
                    'amount': float(row[5]) if row[5] else 0,
                    'created_at': row[6].isoformat() if hasattr(row[6], 'isoformat') else str(row[6]),
                    'updated_at': row[7].isoformat() if hasattr(row[7], 'isoformat') else str(row[7])
                })
            
            return customers
            
        except Exception as e:
            self.logger.error(f"顧客データ取得エラー: {e}")
            return []
    
    def _perform_customer_segmentation(self, customers):
        """顧客セグメンテーションを実行"""
        try:
            if not customers:
                return []
            
            # 金額ベースのセグメンテーション
            amounts = [c['amount'] for c in customers]
            mean_amount = np.mean(amounts)
            std_amount = np.std(amounts)
            
            segments = []
            for customer in customers:
                amount = customer['amount']
                
                if amount > mean_amount + std_amount:
                    segment = 'premium'
                elif amount > mean_amount:
                    segment = 'standard'
                else:
                    segment = 'basic'
                
                segments.append({
                    'company_id': customer['company_id'],
                    'name': customer['name'],
                    'segment': segment,
                    'amount': amount,
                    'industry': customer['industry'],
                    'employee_count': customer['employee_count']
                })
            
            return segments
            
        except Exception as e:
            self.logger.error(f"顧客セグメンテーションエラー: {e}")
            return []
    
    def _analyze_segment_characteristics(self, segments):
        """セグメント別の特徴を分析"""
        try:
            if not segments:
                return {}
            
            segment_data = {}
            for segment in segments:
                seg_name = segment['segment']
                if seg_name not in segment_data:
                    segment_data[seg_name] = {
                        'count': 0,
                        'total_amount': 0,
                        'industries': [],
                        'employee_counts': []
                    }
                
                segment_data[seg_name]['count'] += 1
                segment_data[seg_name]['total_amount'] += segment['amount']
                segment_data[seg_name]['industries'].append(segment['industry'])
                segment_data[seg_name]['employee_counts'].append(segment['employee_count'])
            
            # 統計を計算
            characteristics = {}
            for seg_name, data in segment_data.items():
                characteristics[seg_name] = {
                    'count': data['count'],
                    'average_amount': data['total_amount'] / data['count'],
                    'total_amount': data['total_amount'],
                    'top_industries': self._get_top_values(data['industries'], 3),
                    'average_employee_count': np.mean([e for e in data['employee_counts'] if e])
                }
            
            return characteristics
            
        except Exception as e:
            self.logger.error(f"セグメント特徴分析エラー: {e}")
            return {}
    
    def _get_top_values(self, values, top_n):
        """上位の値を取得"""
        try:
            from collections import Counter
            counter = Counter(values)
            return [item[0] for item in counter.most_common(top_n)]
        except Exception as e:
            self.logger.error(f"上位値取得エラー: {e}")
            return []
    
    def _generate_segment_recommendations(self, segments):
        """セグメント別の推奨事項を生成"""
        try:
            recommendations = {
                'premium': [
                    '高価値顧客向けの専用サポートを提供',
                    '早期アクセス機能の提供',
                    'カスタマイズ機能の拡張'
                ],
                'standard': [
                    '標準的なサポートレベルの維持',
                    '機能の段階的な紹介',
                    '定期的なフォローアップ'
                ],
                'basic': [
                    '基本的なサポートの提供',
                    '使いやすい機能の強調',
                    'コスト効率の良いプランの提案'
                ]
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"セグメント推奨事項生成エラー: {e}")
            return {}
    
    def _summarize_segmentation(self, segments):
        """セグメンテーションの要約を作成"""
        try:
            if not segments:
                return "セグメンテーション分析に必要なデータが不足しています"
            
            segment_counts = {}
            for segment in segments:
                seg_name = segment['segment']
                segment_counts[seg_name] = segment_counts.get(seg_name, 0) + 1
            
            summary = f"顧客を{len(segment_counts)}つのセグメントに分類しました: "
            summary += ", ".join([f"{seg}: {count}件" for seg, count in segment_counts.items()])
            
            return summary
            
        except Exception as e:
            self.logger.error(f"セグメンテーション要約エラー: {e}")
            return "セグメンテーション要約の作成に失敗しました"
    
    def _calculate_churn_risks(self, customers):
        """解約リスクを計算"""
        try:
            churn_risks = []
            
            for customer in customers:
                # 簡易的な解約リスク計算
                risk_score = 0
                
                # 金額が低い場合はリスクが高い
                if customer['amount'] < 1000:
                    risk_score += 30
                elif customer['amount'] < 5000:
                    risk_score += 15
                
                # 業界によるリスク調整
                high_risk_industries = ['retail', 'restaurant', 'startup']
                if customer['industry'] in high_risk_industries:
                    risk_score += 20
                
                # 従業員数によるリスク調整
                if customer['employee_count'] and customer['employee_count'] < 10:
                    risk_score += 10
                
                # ステータスによるリスク調整
                if customer['status'] == 'trial':
                    risk_score += 25
                elif customer['status'] == 'past_due':
                    risk_score += 40
                
                churn_risks.append({
                    'company_id': customer['company_id'],
                    'name': customer['name'],
                    'risk_score': min(100, risk_score),
                    'risk_level': 'high' if risk_score > 50 else 'medium' if risk_score > 25 else 'low',
                    'amount': customer['amount'],
                    'status': customer['status']
                })
            
            return churn_risks
            
        except Exception as e:
            self.logger.error(f"解約リスク計算エラー: {e}")
            return []
    
    def _analyze_churn_factors(self, customers):
        """解約要因を分析"""
        try:
            factors = {
                'price_sensitivity': 0,
                'service_quality': 0,
                'competition': 0,
                'business_changes': 0
            }
            
            # 簡易的な要因分析
            total_customers = len(customers)
            
            # 価格感度
            low_amount_customers = len([c for c in customers if c['amount'] < 1000])
            factors['price_sensitivity'] = (low_amount_customers / total_customers) * 100
            
            # サービス品質（ステータスベース）
            problematic_customers = len([c for c in customers if c['status'] in ['past_due', 'cancelled']])
            factors['service_quality'] = (problematic_customers / total_customers) * 100
            
            return factors
            
        except Exception as e:
            self.logger.error(f"解約要因分析エラー: {e}")
            return {}
    
    def _generate_prevention_strategies(self, churn_risks, churn_factors):
        """解約防止策を生成"""
        try:
            strategies = []
            
            # 高リスク顧客向けの戦略
            high_risk_customers = [c for c in churn_risks if c['risk_level'] == 'high']
            if high_risk_customers:
                strategies.append({
                    'target': 'high_risk_customers',
                    'strategy': '個別アプローチによる解約防止',
                    'actions': [
                        '定期的なフォローアップ',
                        'カスタマイズされた提案',
                        '早期警告システムの活用'
                    ]
                })
            
            # 価格感度が高い顧客向けの戦略
            if churn_factors.get('price_sensitivity', 0) > 30:
                strategies.append({
                    'target': 'price_sensitive_customers',
                    'strategy': '価格最適化による解約防止',
                    'actions': [
                        '段階的な価格設定',
                        'バリューパッケージの提供',
                        '長期契約のインセンティブ'
                    ]
                })
            
            return strategies
            
        except Exception as e:
            self.logger.error(f"解約防止策生成エラー: {e}")
            return []
    
    def _summarize_churn_analysis(self, churn_risks):
        """解約分析の要約を作成"""
        try:
            if not churn_risks:
                return "解約分析に必要なデータが不足しています"
            
            total_customers = len(churn_risks)
            high_risk = len([r for r in churn_risks if r['risk_level'] == 'high'])
            medium_risk = len([r for r in churn_risks if r['risk_level'] == 'medium'])
            low_risk = len([r for r in churn_risks if r['risk_level'] == 'low'])
            
            summary = f"解約リスク分析: 高リスク{high_risk}件、中リスク{medium_risk}件、低リスク{low_risk}件"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"解約分析要約エラー: {e}")
            return "解約分析要約の作成に失敗しました"
    
    def _generate_overview_section(self, company_id):
        """概要セクションを生成"""
        try:
            # ダッシュボードサービスから統計を取得
            overview = dashboard_service.get_overview_statistics()
            
            return {
                'title': '概要統計',
                'data': overview.get('statistics', {}),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"概要セクション生成エラー: {e}")
            return {'title': '概要統計', 'error': str(e)}
    
    def _generate_prediction_section(self, company_id):
        """予測セクションを生成"""
        try:
            predictions = self.get_prediction_analytics('revenue', company_id)
            
            return {
                'title': '予測分析',
                'data': predictions,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"予測セクション生成エラー: {e}")
            return {'title': '予測分析', 'error': str(e)}
    
    def _generate_anomaly_section(self, company_id):
        """異常検知セクションを生成"""
        try:
            anomalies = self.get_anomaly_detection('revenue', company_id)
            
            return {
                'title': '異常検知',
                'data': anomalies,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"異常検知セクション生成エラー: {e}")
            return {'title': '異常検知', 'error': str(e)}
    
    def _generate_trend_section(self, company_id):
        """トレンド分析セクションを生成"""
        try:
            historical_data = self._get_historical_data('revenue', company_id)
            
            if historical_data:
                df = pd.DataFrame(historical_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                trend_analysis = self._analyze_trend(df)
                
                return {
                    'title': 'トレンド分析',
                    'data': trend_analysis,
                    'generated_at': datetime.now().isoformat()
                }
            else:
                return {
                    'title': 'トレンド分析',
                    'data': {},
                    'message': 'トレンド分析に必要なデータが不足しています'
                }
                
        except Exception as e:
            self.logger.error(f"トレンドセクション生成エラー: {e}")
            return {'title': 'トレンド分析', 'error': str(e)}
    
    def _generate_recommendations_section(self, report_data):
        """推奨事項セクションを生成"""
        try:
            recommendations = []
            
            # 予測分析からの推奨事項
            if 'predictions' in report_data['sections']:
                pred_data = report_data['sections']['predictions']['data']
                if pred_data.get('success') and pred_data.get('trend_analysis'):
                    trend = pred_data['trend_analysis']
                    if trend.get('direction') == 'decreasing':
                        recommendations.append({
                            'category': 'revenue',
                            'priority': 'high',
                            'title': '収益減少の対策',
                            'description': '収益トレンドが減少傾向にあるため、新規顧客獲得や既存顧客のアップセルを検討してください'
                        })
            
            # 異常検知からの推奨事項
            if 'anomalies' in report_data['sections']:
                anomaly_data = report_data['sections']['anomalies']['data']
                if anomaly_data.get('success') and anomaly_data.get('anomalies'):
                    anomalies = anomaly_data['anomalies']
                    if len(anomalies) > 0:
                        recommendations.append({
                            'category': 'anomaly',
                            'priority': 'medium',
                            'title': '異常値の調査',
                            'description': f'{len(anomalies)}件の異常が検出されました。詳細な調査を推奨します'
                        })
            
            return {
                'title': '推奨事項',
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"推奨事項セクション生成エラー: {e}")
            return {'title': '推奨事項', 'error': str(e)}
    
    def _save_report(self, report_data, report_type, company_id):
        """レポートを保存"""
        try:
            # レポートディレクトリを作成
            reports_dir = 'reports'
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # ファイル名を生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            company_suffix = f"_company_{company_id}" if company_id else ""
            filename = f"analytics_report_{report_type}{company_suffix}_{timestamp}.json"
            filepath = os.path.join(reports_dir, filename)
            
            # レポートを保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            return filename
            
        except Exception as e:
            self.logger.error(f"レポート保存エラー: {e}")
            return None

# インスタンスを作成
analytics_service = AnalyticsService() 