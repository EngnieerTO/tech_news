import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html

class EmailNotifier:
    # タグのスタイル定義
    TAG_STYLE = "background-color: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 3px; margin-right: 5px; font-size: 0.85em;"
    # 食産業タグのスタイル定義（緑色）
    FOOD_INDUSTRY_TAG_STYLE = "background-color: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 3px; margin-right: 5px; font-size: 0.85em;"
    # 食産業タグのリスト
    FOOD_INDUSTRY_TAGS = {"飲食", "農業", "漁業", "食品工場", "フードテック"}
    # カテゴリーの表示順序
    CATEGORY_ORDER = ["News", "Blog", "Events", "Uncategorized"]
    
    def __init__(self, config):
        self.config = config
        # 環境変数からGmail設定を取得
        self.gmail_user = os.environ.get('GMAIL_USER')
        self.gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not self.gmail_user or not self.gmail_password:
            print("Warning: GMAIL_USER or GMAIL_APP_PASSWORD environment variable is not set.")

    def send_daily_summary(self, articles, notable_articles=None):
        """収集した記事リストをメールで送信する"""
        if not articles:
            print("No articles to send.")
            return

        if not self.gmail_user or not self.gmail_password:
            print("Skipping email send (No Credentials). Printing content instead.")
            print(self._generate_email_body(articles, notable_articles))
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
        text_body = self._generate_email_body(articles, notable_articles)
        html_body = self._generate_html_body(articles, notable_articles)

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        try:
            # GmailのSMTPサーバーに接続
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully to {self.config['email']['to_email']}!")
        except smtplib.SMTPAuthenticationError as e:
            print(f"Error sending email: Authentication failed. Please regenerate the Gmail App Password and update the GMAIL_APP_PASSWORD secret. Details: {e}")
            raise
        except Exception as e:
            print(f"Error sending email: {e}")
            raise

    def _generate_email_body(self, articles, notable_articles=None):
        """テキスト形式のメール本文（デバッグ用）"""
        lines = ["Here is your daily tech news summary:\n"]
        
        if notable_articles:
            lines.append("=== 本日の注目記事 (Today's Notable Articles) ===")
            for i, article in enumerate(notable_articles, 1):
                lines.append(f"\n{i}. {article.get('title', 'N/A')}")
                lines.append(f"   {article.get('url', 'N/A')}")
                lines.append(f"   {article.get('description', 'N/A')}")
            lines.append("====================================\n")

        for article in articles:
            lines.append(f"- {article['title']}")
            lines.append(f"  {article['url']}")
            if article.get('tags'):
                lines.append(f"  Tags: {', '.join(article['tags'])}")
            lines.append("")
        return "\n".join(lines)

    def _generate_html_body(self, articles, notable_articles=None):
        """HTML形式のメール本文（カテゴリー分け対応）"""
        # カテゴリーごとにグループ化
        grouped_articles = {}
        for article in articles:
            cat = article.get('category', 'Uncategorized')
            if cat not in grouped_articles:
                grouped_articles[cat] = []
            grouped_articles[cat].append(article)

        html_content = "<h2>Daily Summary</h2>"
        
        # 注目記事セクション
        if notable_articles:
            html_content += """
            <div style="background-color: #fff3e0; padding: 20px; margin-bottom: 25px; border-left: 5px solid #ff9800; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #e65100;">📌 本日の注目記事 (Today's Notable Articles)</h3>
                <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">食産業・フードテックの視点で選出</p>
            """
            
            for i, article in enumerate(notable_articles, 1):
                title_escaped = html.escape(article.get('title', 'N/A'))
                url_escaped = html.escape(article.get('url', 'N/A'))
                description_escaped = html.escape(article.get('description', 'N/A'))
                
                html_content += f"""
                <div style="margin-bottom: 20px; padding: 15px; background-color: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 10px 0; color: #ff9800;">
                        <span style="background-color: #ff9800; color: white; padding: 3px 8px; border-radius: 3px; margin-right: 8px; font-size: 0.9em;">{i}</span>
                        <a href='{url_escaped}' style="color: #e65100; text-decoration: none;">{title_escaped}</a>
                    </h4>
                    <p style="margin: 0; color: #333; line-height: 1.6;">{description_escaped}</p>
                </div>
                """
            
            html_content += "</div>"
        
        # カテゴリー順に表示（固定順序）
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
                    # 食産業タグは緑色、その他は青色で表示
                    tags_html = " ".join([
                        f"<span style='{self.FOOD_INDUSTRY_TAG_STYLE if tag in self.FOOD_INDUSTRY_TAGS else self.TAG_STYLE}'>{html.escape(tag)}</span>" 
                        for tag in article['tags']
                    ])
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
