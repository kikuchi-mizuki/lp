/**
 * 公式LINEアカウントでの利用制限チェッカー
 * 
 * 使用方法：
 * 1. このスクリプトを各公式LINEアカウントのWebページに組み込む
 * 2. LINE_USER_IDを取得して利用制限をチェック
 * 3. 制限されている場合はAIコレクションズの公式LINEに誘導
 */

class LineRestrictionChecker {
    constructor(apiBaseUrl = 'https://ai-collections.herokuapp.com') {
        this.apiBaseUrl = apiBaseUrl;
        this.contentType = this.getContentTypeFromUrl();
    }

    /**
     * URLからコンテンツタイプを取得
     */
    getContentTypeFromUrl() {
        const url = window.location.href;
        if (url.includes('schedule') || url.includes('ai_schedule_secretary')) {
            return 'AI予定秘書';
        } else if (url.includes('accounting') || url.includes('ai_accounting_secretary')) {
            return 'AI経理秘書';
        } else if (url.includes('task') || url.includes('ai_task_concierge')) {
            return 'AIタスクコンシェルジュ';
        }
        return null;
    }

    /**
     * LINEユーザーIDを取得
     */
    async getLineUserId() {
        // LINEログインからユーザーIDを取得
        // 実際の実装ではLINE Login APIを使用
        return new Promise((resolve) => {
            // デモ用：URLパラメータから取得
            const urlParams = new URLSearchParams(window.location.search);
            const lineUserId = urlParams.get('line_user_id');
            resolve(lineUserId);
        });
    }

    /**
     * 利用制限をチェック
     */
    async checkRestriction() {
        try {
            const lineUserId = await this.getLineUserId();
            
            if (!lineUserId) {
                console.log('LINEユーザーIDが見つかりません');
                return { restricted: false };
            }

            const response = await fetch(`${this.apiBaseUrl}/line/check_restriction/${encodeURIComponent(this.contentType)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    line_user_id: lineUserId
                })
            });

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('利用制限チェックエラー:', error);
            return { restricted: false, error: error.message };
        }
    }

    /**
     * 制限メッセージを表示
     */
    async showRestrictionMessage() {
        try {
            const lineUserId = await this.getLineUserId();
            
            if (!lineUserId) {
                console.log('LINEユーザーIDが見つかりません');
                return;
            }

            const response = await fetch(`${this.apiBaseUrl}/line/restriction_message/${encodeURIComponent(this.contentType)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    line_user_id: lineUserId
                })
            });

            const data = await response.json();
            
            if (data.restricted) {
                this.displayRestrictionUI(data.message);
            }

        } catch (error) {
            console.error('制限メッセージ取得エラー:', error);
        }
    }

    /**
     * 制限UIを表示
     */
    displayRestrictionUI(messageData) {
        // 既存のコンテンツを非表示
        const mainContent = document.querySelector('main') || document.body;
        mainContent.style.display = 'none';

        // 制限メッセージを表示
        const restrictionDiv = document.createElement('div');
        restrictionDiv.id = 'line-restriction-message';
        restrictionDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            padding: 20px;
            box-sizing: border-box;
        `;

        const messageContainer = document.createElement('div');
        messageContainer.style.cssText = `
            background: white;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 500px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        `;

        const title = document.createElement('h1');
        title.textContent = messageData.template.title;
        title.style.cssText = `
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
            font-weight: bold;
        `;

        const text = document.createElement('p');
        text.textContent = messageData.template.text;
        text.style.cssText = `
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
            font-size: 16px;
        `;

        const buttonContainer = document.createElement('div');
        buttonContainer.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 15px;
        `;

        // ボタンを作成
        messageData.template.actions.forEach(action => {
            const button = document.createElement('button');
            button.textContent = action.label;
            button.style.cssText = `
                background: #00B900;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.3s;
            `;

            button.addEventListener('mouseenter', () => {
                button.style.background = '#009900';
            });

            button.addEventListener('mouseleave', () => {
                button.style.background = '#00B900';
            });

            if (action.type === 'uri') {
                button.addEventListener('click', () => {
                    window.open(action.uri, '_blank');
                });
            }

            buttonContainer.appendChild(button);
        });

        messageContainer.appendChild(title);
        messageContainer.appendChild(text);
        messageContainer.appendChild(buttonContainer);
        restrictionDiv.appendChild(messageContainer);
        document.body.appendChild(restrictionDiv);
    }

    /**
     * 初期化
     */
    async init() {
        if (!this.contentType) {
            console.log('コンテンツタイプが特定できません');
            return;
        }

        console.log(`利用制限チェック開始: ${this.contentType}`);
        
        const restriction = await this.checkRestriction();
        
        if (restriction.restricted) {
            console.log('利用制限が検出されました');
            await this.showRestrictionMessage();
        } else {
            console.log('利用制限はありません');
        }
    }
}

// 自動初期化
document.addEventListener('DOMContentLoaded', () => {
    const checker = new LineRestrictionChecker();
    checker.init();
});

// グローバル関数として公開（手動初期化用）
window.LineRestrictionChecker = LineRestrictionChecker; 