import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html

class EmailNotifier:
    # タグのスタイル定義
    TAG_STYLE = "background-color: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 3px; margin-right: 5px; font-size: 0.85em;"
    # カテゴリーの表示順序
    CATEGORY_ORDER = ["News", "Blog", "Events", "Uncategorized"]
    
    def __init__(self, config):
        self.config = config
        # 環境変数からGmail設定を取得
        self.gmail_user = os.environ.get('GMAIL_USER')
        self.gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not self.gmail_user or not self.gmail_password:
            print("Warning: GMAIL_USER or GMAIL_APP_PASSWORD environment variable is not set.")

    def send_daily_summary(self, articles, overall_summary=None):
        """収集した記事リストをメールで送信する"""
        if not articles:
            print("No articles to send.")
            return

        if not self.gmail_user or not self.gmail_password:
            print("Skipping email send (No Credentials). Printing content instead.")
            print(self._generate_email_body(articles, overall_summary))
            return

        # メールの作成
        msg = MIMEMultipart("alternative")
        msg['Subject'] = f"{self.config['email']['subject_prefix']} Daily Summary - {len(articles)} articles"
        msg['From'] = self.gmail_user
        
        # 宛先がリストならカンマ区切りにする、文字列ならそのまま
        to_emails = self.config['email']['to_email']
        if isinstance(to_emails, list):
            msg['To'] = ", ".join(to_emails)
        else:
            msg['To'] = to_emails

        # 本文の作成（テキスト版とHTML版）
        text_body = self._generate_email_body(articles, overall_summary)
        html_body = self._generate_html_body(articles, overall_summary)

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        try:
            # GmailのSMTPサーバーに接続
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully to {self.config['email']['to_email']}!")
        except Exception as e:
            print(f"Error sending email: {e}")

    def _generate_email_body(self, articles, overall_summary=None):
        """テキスト形式のメール本文（デバッグ用）"""
        lines = ["Here is your daily tech news summary:\n"]
        
        if overall_summary:
            lines.append("=== FoodTech Perspective Summary ===")
            lines.append(overall_summary)
            lines.append("====================================\n")

        for article in articles:
            lines.append(f"- {article['title']}")
            lines.append(f"  {article['url']}")
            if article.get('tags'):
                lines.append(f"  Tags: {', '.join(article['tags'])}")
            lines.append("")
        return "\n".join(lines)

    def _generate_html_body(self, articles, overall_summary=None):
        """HTML形式のメール本文（カテゴリー分け対応）"""
        # カテゴリーごとにグループ化
        grouped_articles = {}
        for article in articles:
            cat = article.get('category', 'Uncategorized')
            if cat not in grouped_articles:
                grouped_articles[cat] = []
            grouped_articles[cat].append(article)

        html_content = "<h2>Daily Summary</h2>"
        
        if overall_summary:
            overall_summary_escaped = html.escape(overall_summary)
            html_content += f"""
            <div style="background-color: #e8daef; padding: 15px; margin-bottom: 20px; border-left: 5px solid #8e44ad; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #8e44ad;">Today's FoodTech Perspective</h3>
                <p style="white-space: pre-wrap;">{overall_summary_escaped}</p>
            </div>
            """
        
        # カテゴリー順に表示（固定順序またはアルファベット順）
        # ここでは固定順序を定義してみる
        category_order = self.CATEGORY_ORDER
        
        # 存在するカテゴリーだけを抽出してソート
        sorted_categories = [c for c in category_order if c in grouped_articles]
        # 定義にないカテゴリーがあれば末尾に追加
        for cat in grouped_articles.keys():
            if cat not in sorted_categories:
                sorted_categories.append(cat)

        for category in sorted_categories:
            articles_in_cat = grouped_articles[category]
            category_escaped = html.escape(category)
            html_content += f"<h3 style='background-color: #f0f0f0; padding: 5px;'>{category_escaped} ({len(articles_in_cat)})</h3><ul>"
            
            for article in articles_in_cat:
                html_escaped_title = html.escape(article['title'])
                html_escaped_url = html.escape(article['url'])
                html_escaped_source = html.escape(article['source'])
                html_escaped_keyword = html.escape(article.get('matched_keyword', 'N/A'))
                
                html_content += f"<li style='margin-bottom: 15px;'>"
                html_content += f"<strong><a href='{html_escaped_url}'>{html_escaped_title}</a></strong>"
                html_content += f"<br/><small style='color: #666;'>Source: {html_escaped_source} | Keyword: {html_escaped_keyword}</small>"
                
                # タグを表示（HTML エスケープして XSS を防止）
                if article.get('tags'):
                    tags_html = " ".join([f"<span style='{self.TAG_STYLE}'>{html.escape(tag)}</span>" for tag in article['tags']])
                    html_output = f"<br/><div style='margin-top: 5px;'>{tags_html}</div>"
                    html_content += html_output
                
                if article.get('summary'):
                    # HTMLエスケープしてから改行を<br>に変換
                    summary_escaped = html.escape(article['summary'])
                    summary_html = summary_escaped.replace('\n', '<br/>')
                    html_output = f"<p style='margin-top: 5px;'>{summary_html}</p>"
                    html_content += html_output
                html_content += "</li>"
            html_content += "</ul>"
            
        return html_content
