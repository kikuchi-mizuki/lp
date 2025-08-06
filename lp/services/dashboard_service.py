import json
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.company_service import CompanyService
from lp.services.cancellation_service import cancellation_service
from lp.services.notification_service import notification_service
from lp.services.backup_service import backup_service

class DashboardService:
    """管理ダッシュボードサービス"""
    
    def __init__(self):
        self.company_service = CompanyService()
    
    def get_overview_statistics(self):
        """概要統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業統計
            c.execute('SELECT COUNT(*) FROM companies')
            total_companies = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM companies WHERE created_at >= CURRENT_DATE - INTERVAL \'30 days\'')
            new_companies_30d = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM companies WHERE created_at >= CURRENT_DATE - INTERVAL \'7 days\'')
            new_companies_7d = c.fetchone()[0]
            
            # 支払い統計
            c.execute('''
                SELECT 
                    COUNT(*) as total_payments,
                    COUNT(CASE WHEN subscription_status = 'active' THEN 1 END) as active_payments,
                    COUNT(CASE WHEN subscription_status = 'trialing' THEN 1 END) as trialing_payments,
                    COUNT(CASE WHEN subscription_status = 'canceled' THEN 1 END) as canceled_payments
                FROM company_payments
            ''')
            payment_stats = c.fetchone()
            total_payments, active_payments, trialing_payments, canceled_payments = payment_stats
            
            # 解約統計
            c.execute('SELECT COUNT(*) FROM company_cancellations')
            total_cancellations = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM company_cancellations WHERE cancelled_at >= CURRENT_DATE - INTERVAL \'30 days\'')
            cancellations_30d = c.fetchone()[0]
            
            # 通知統計
            c.execute('SELECT COUNT(*) FROM company_notifications')
            total_notifications = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM company_notifications WHERE sent_at >= CURRENT_DATE')
            notifications_today = c.fetchone()[0]
            
            # コンテンツ統計
            c.execute('SELECT COUNT(*) FROM company_contents WHERE is_active = true')
            active_contents = c.fetchone()[0]
            
            c.execute('SELECT content_type, COUNT(*) FROM company_contents WHERE is_active = true GROUP BY content_type')
            content_type_stats = dict(c.fetchall())
            
            conn.close()
            
            return {
                'success': True,
                'overview': {
                    'companies': {
                        'total': total_companies,
                        'new_30d': new_companies_30d,
                        'new_7d': new_companies_7d
                    },
                    'payments': {
                        'total': total_payments,
                        'active': active_payments,
                        'trialing': trialing_payments,
                        'canceled': canceled_payments
                    },
                    'cancellations': {
                        'total': total_cancellations,
                        'last_30d': cancellations_30d
                    },
                    'notifications': {
                        'total': total_notifications,
                        'today': notifications_today
                    },
                    'contents': {
                        'active': active_contents,
                        'by_type': content_type_stats
                    }
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'概要統計取得エラー: {str(e)}'
            }
    
    def get_cancellation_statistics(self):
        """解約統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 解約理由別統計
            c.execute('''
                SELECT cancellation_reason, COUNT(*) as count
                FROM company_cancellations
                GROUP BY cancellation_reason
                ORDER BY count DESC
            ''')
            reason_stats = []
            for row in c.fetchall():
                reason_stats.append({
                    'reason': row[0],
                    'count': row[1]
                })
            
            # 月別解約統計（過去12ヶ月）
            c.execute('''
                SELECT 
                    DATE_TRUNC('month', cancelled_at) as month,
                    COUNT(*) as count
                FROM company_cancellations
                WHERE cancelled_at >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY DATE_TRUNC('month', cancelled_at)
                ORDER BY month
            ''')
            monthly_stats = []
            for row in c.fetchall():
                monthly_stats.append({
                    'month': row[0].strftime('%Y-%m'),
                    'count': row[1]
                })
            
            # 解約率計算
            c.execute('SELECT COUNT(*) FROM companies')
            total_companies = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM company_cancellations')
            total_cancellations = c.fetchone()[0]
            
            cancellation_rate = (total_cancellations / total_companies * 100) if total_companies > 0 else 0
            
            # 平均利用期間
            c.execute('''
                SELECT AVG(EXTRACT(EPOCH FROM (cancelled_at - cc.created_at)) / 86400) as avg_days
                FROM company_cancellations cc
                JOIN companies c ON cc.company_id = c.id
                WHERE cc.cancelled_at IS NOT NULL AND c.created_at IS NOT NULL
            ''')
            avg_usage_days = c.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'success': True,
                'cancellation_stats': {
                    'total_cancellations': total_cancellations,
                    'cancellation_rate': round(cancellation_rate, 2),
                    'avg_usage_days': round(avg_usage_days, 1),
                    'reason_stats': reason_stats,
                    'monthly_stats': monthly_stats
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'解約統計取得エラー: {str(e)}'
            }
    
    def get_notification_statistics(self):
        """通知統計を取得"""
        try:
            # 通知サービスから統計を取得
            notification_stats = notification_service.get_notification_statistics()
            
            if not notification_stats['success']:
                return notification_stats
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 通知タイプ別統計（詳細）
            c.execute('''
                SELECT 
                    notification_type,
                    COUNT(*) as count,
                    DATE_TRUNC('day', sent_at) as date
                FROM company_notifications
                WHERE sent_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY notification_type, DATE_TRUNC('day', sent_at)
                ORDER BY date DESC, count DESC
            ''')
            
            daily_notifications = {}
            for row in c.fetchall():
                notification_type, count, date = row
                date_str = date.strftime('%Y-%m-%d')
                if date_str not in daily_notifications:
                    daily_notifications[date_str] = {}
                daily_notifications[date_str][notification_type] = count
            
            # 企業別通知統計（上位10社）
            c.execute('''
                SELECT 
                    c.company_name,
                    COUNT(cn.id) as notification_count
                FROM companies c
                LEFT JOIN company_notifications cn ON c.id = cn.company_id
                GROUP BY c.id, c.company_name
                ORDER BY notification_count DESC
                LIMIT 10
            ''')
            
            company_notifications = []
            for row in c.fetchall():
                company_notifications.append({
                    'company_name': row[0],
                    'notification_count': row[1]
                })
            
            conn.close()
            
            return {
                'success': True,
                'notification_stats': {
                    **notification_stats['statistics'],
                    'daily_notifications': daily_notifications,
                    'company_notifications': company_notifications
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'通知統計取得エラー: {str(e)}'
            }
    
    def get_backup_statistics(self):
        """バックアップ統計を取得"""
        try:
            # バックアップサービスから統計を取得
            backup_stats = backup_service.get_backup_statistics()
            
            if not backup_stats['success']:
                return backup_stats
            
            return {
                'success': True,
                'backup_stats': backup_stats['statistics']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'バックアップ統計取得エラー: {str(e)}'
            }
    
    def get_company_analytics(self, company_id=None):
        """企業分析データを取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if company_id:
                # 特定企業の分析
                c.execute('''
                    SELECT 
                        c.*,
                        cp.subscription_status,
                        cp.current_period_start,
                        cp.current_period_end,
                        cp.trial_end,
                        COUNT(cc.id) as content_count,
                        COUNT(cn.id) as notification_count
                    FROM companies c
                    LEFT JOIN company_payments cp ON c.id = cp.company_id
                    LEFT JOIN company_contents cc ON c.id = cc.company_id AND cc.is_active = true
                    LEFT JOIN company_notifications cn ON c.id = cn.company_id
                    WHERE c.id = %s
                    GROUP BY c.id, cp.subscription_status, cp.current_period_start, cp.current_period_end, cp.trial_end
                ''', (company_id,))
                
                company_data = c.fetchone()
                if not company_data:
                    return {
                        'success': False,
                        'error': '企業が見つかりません'
                    }
                
                # 企業の詳細分析
                company_analytics = {
                    'company_info': {
                        'id': company_data[0],
                        'company_name': company_data[1],
                        'industry': company_data[2],
                        'employee_count': company_data[3],
                        'created_at': company_data[7].isoformat() if company_data[7] else None
                    },
                    'subscription_info': {
                        'status': company_data[9],
                        'current_period_start': company_data[10].isoformat() if company_data[10] else None,
                        'current_period_end': company_data[11].isoformat() if company_data[11] else None,
                        'trial_end': company_data[12].isoformat() if company_data[12] else None
                    },
                    'usage_stats': {
                        'content_count': company_data[13],
                        'notification_count': company_data[14]
                    }
                }
                
                # コンテンツ使用履歴
                c.execute('''
                    SELECT content_type, created_at, updated_at
                    FROM company_contents
                    WHERE company_id = %s
                    ORDER BY created_at DESC
                ''', (company_id,))
                
                content_history = []
                for row in c.fetchall():
                    content_history.append({
                        'content_type': row[0],
                        'created_at': row[1].isoformat() if row[1] else None,
                        'updated_at': row[2].isoformat() if row[2] else None
                    })
                
                company_analytics['content_history'] = content_history
                
                # 通知履歴
                c.execute('''
                    SELECT notification_type, sent_at
                    FROM company_notifications
                    WHERE company_id = %s
                    ORDER BY sent_at DESC
                    LIMIT 20
                ''', (company_id,))
                
                notification_history = []
                for row in c.fetchall():
                    notification_history.append({
                        'notification_type': row[0],
                        'sent_at': row[1].isoformat() if row[1] else None
                    })
                
                company_analytics['notification_history'] = notification_history
                
                conn.close()
                
                return {
                    'success': True,
                    'company_analytics': company_analytics
                }
            
            else:
                # 全企業の分析
                c.execute('''
                    SELECT 
                        c.id,
                        c.company_name,
                        c.industry,
                        c.employee_count,
                        c.created_at,
                        cp.subscription_status,
                        COUNT(cc.id) as content_count,
                        COUNT(cn.id) as notification_count
                    FROM companies c
                    LEFT JOIN company_payments cp ON c.id = cp.company_id
                    LEFT JOIN company_contents cc ON c.id = cc.company_id AND cc.is_active = true
                    LEFT JOIN company_notifications cn ON c.id = cn.company_id
                    GROUP BY c.id, c.company_name, c.industry, c.employee_count, c.created_at, cp.subscription_status
                    ORDER BY c.created_at DESC
                ''')
                
                companies_analytics = []
                for row in c.fetchall():
                    companies_analytics.append({
                        'id': row[0],
                        'company_name': row[1],
                        'industry': row[2],
                        'employee_count': row[3],
                        'created_at': row[4].isoformat() if row[4] else None,
                        'subscription_status': row[5],
                        'content_count': row[6],
                        'notification_count': row[7]
                    })
                
                conn.close()
                
                return {
                    'success': True,
                    'companies_analytics': companies_analytics
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'企業分析取得エラー: {str(e)}'
            }
    
    def get_revenue_analytics(self):
        """収益分析データを取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 月別収益統計（過去12ヶ月）
            c.execute('''
                SELECT 
                    DATE_TRUNC('month', cp.created_at) as month,
                    COUNT(*) as subscription_count,
                    COUNT(*) * 3900 as revenue
                FROM company_payments cp
                WHERE cp.created_at >= CURRENT_DATE - INTERVAL '12 months'
                AND cp.subscription_status IN ('active', 'trialing')
                GROUP BY DATE_TRUNC('month', cp.created_at)
                ORDER BY month
            ''')
            
            monthly_revenue = []
            for row in c.fetchall():
                monthly_revenue.append({
                    'month': row[0].strftime('%Y-%m'),
                    'subscription_count': row[1],
                    'revenue': row[2]
                })
            
            # 業界別統計
            c.execute('''
                SELECT 
                    c.industry,
                    COUNT(*) as company_count,
                    COUNT(*) * 3900 as total_revenue
                FROM companies c
                JOIN company_payments cp ON c.id = cp.company_id
                WHERE cp.subscription_status IN ('active', 'trialing')
                GROUP BY c.industry
                ORDER BY total_revenue DESC
            ''')
            
            industry_stats = []
            for row in c.fetchall():
                industry_stats.append({
                    'industry': row[0] or '未設定',
                    'company_count': row[1],
                    'total_revenue': row[2]
                })
            
            # 従業員数別統計
            c.execute('''
                SELECT 
                    CASE 
                        WHEN c.employee_count < 10 THEN '1-9人'
                        WHEN c.employee_count < 50 THEN '10-49人'
                        WHEN c.employee_count < 100 THEN '50-99人'
                        WHEN c.employee_count < 500 THEN '100-499人'
                        ELSE '500人以上'
                    END as employee_range,
                    COUNT(*) as company_count,
                    COUNT(*) * 3900 as total_revenue
                FROM companies c
                JOIN company_payments cp ON c.id = cp.company_id
                WHERE cp.subscription_status IN ('active', 'trialing')
                GROUP BY 
                    CASE 
                        WHEN c.employee_count < 10 THEN '1-9人'
                        WHEN c.employee_count < 50 THEN '10-49人'
                        WHEN c.employee_count < 100 THEN '50-99人'
                        WHEN c.employee_count < 500 THEN '100-499人'
                        ELSE '500人以上'
                    END
                ORDER BY total_revenue DESC
            ''')
            
            employee_stats = []
            for row in c.fetchall():
                employee_stats.append({
                    'employee_range': row[0],
                    'company_count': row[1],
                    'total_revenue': row[2]
                })
            
            conn.close()
            
            return {
                'success': True,
                'revenue_analytics': {
                    'monthly_revenue': monthly_revenue,
                    'industry_stats': industry_stats,
                    'employee_stats': employee_stats
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'収益分析取得エラー: {str(e)}'
            }
    
    def get_dashboard_summary(self):
        """ダッシュボード全体のサマリーを取得"""
        try:
            # 各統計を取得
            overview = self.get_overview_statistics()
            cancellation = self.get_cancellation_statistics()
            notification = self.get_notification_statistics()
            backup = self.get_backup_statistics()
            revenue = self.get_revenue_analytics()
            
            # 成功した統計のみをまとめる
            summary = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'overview': overview.get('overview') if overview['success'] else None,
                'cancellation': cancellation.get('cancellation_stats') if cancellation['success'] else None,
                'notification': notification.get('notification_stats') if notification['success'] else None,
                'backup': backup.get('backup_stats') if backup['success'] else None,
                'revenue': revenue.get('revenue_analytics') if revenue['success'] else None
            }
            
            return summary
            
        except Exception as e:
            return {
                'success': False,
                'error': f'ダッシュボードサマリー取得エラー: {str(e)}'
            }

# インスタンスを作成
dashboard_service = DashboardService() 