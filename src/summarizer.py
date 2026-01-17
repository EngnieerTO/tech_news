from google import genai
from google.genai import types
import os

class NewsSummarizer:
    # タグがない場合のAI応答のパターン
    NO_TAG_RESPONSES = ["なし", "none", "n/a", "該当なし", "無し"]
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.location = "us-central1"
        
        try:
            if self.api_key:
                # API Keyがある場合はそちらを優先（GitHub Actionsなどで楽）
                self.client = genai.Client(api_key=self.api_key)
                self.model = "gemini-2.5-flash"
            elif self.project_id:
                # ローカルでgcloud auth loginしている場合など
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
                self.model = "gemini-2.5-flash"
            else:
                print("Warning: GOOGLE_API_KEY or GOOGLE_CLOUD_PROJECT is required.")
                self.client = None
                return
        except Exception as e:
            print(f"Error initializing GenAI Client: {e}")
            self.client = None

    def summarize(self, title, original_summary):
        if not self.client:
            return original_summary

        prompt = f"""
以下の技術記事のタイトルと概要を読んで、エンジニア向けに日本語で要約してください。
出力は3点の箇条書きのみにしてください。

Title: {title}
Summary: {original_summary}

出力形式は以下です。これ以外は出力しないでください。
* 箇条書き1
* 箇条書き2
* 箇条書き3
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary for '{title}': {e}")
            return original_summary

    def summarize_grant(self, title, original_summary):
        """助成金情報用の要約を生成"""
        if not self.client:
            return original_summary

        prompt = f"""
以下の助成金・補助金情報のタイトルと概要を読んで、事業者向けに日本語で要約してください。
特に以下の点を含めてください：
- 対象者（中小企業、スタートアップ、特定業界など）
- 支援内容（金額や支援の種類）
- 申請期限や重要な条件


Title: {title}
Summary: {original_summary}

出力は3～5点の箇条書きのみにしてください。これ以外は出力しないでください。
* 箇条書き1
* 箇条書き2
* 箇条書き3
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating grant summary for '{title}': {e}")
            return original_summary

    def generate_overall_summary(self, articles):
        """全記事の情報を元に、食産業・フードテックへの応用視点で注目記事を3つ選定"""
        if not self.client or not articles:
            return None

        # 記事情報をテキストにまとめる（URLも含める）
        articles_text = ""
        for idx, article in enumerate(articles):
            articles_text += f"{idx + 1}. Title: {article['title']}\n"
            articles_text += f"   URL: {article['url']}\n"
            articles_text += f"   Summary: {article.get('summary', 'No summary provided')}\n\n"

        prompt = f"""
以下は本日収集された複数のテックニュース記事のタイトルと要約です。
これらすべての記事の中から、食産業やフードテックの視点で注目の記事を3つピックアップしてください。

条件:
- 記事番号、タイトル、URL、そして食産業での活用事例を挙げながら、各150文字程度で解説してください。
- 直接的に食品に関連しない技術（AI、ロボティクス、センサー技術など）であっても、食品業界への応用可能性を具体的に見出して記述してください。
- 各記事の解説では、具体的な活用事例や応用シーンを含めてください。

出力形式:
===記事1===
番号: [記事番号]
タイトル: [記事のタイトル]
URL: [記事のURL]
解説: [150文字程度の解説。食産業での活用事例を含む]

===記事2===
番号: [記事番号]
タイトル: [記事のタイトル]
URL: [記事のURL]
解説: [150文字程度の解説。食産業での活用事例を含む]

===記事3===
番号: [記事番号]
タイトル: [記事のタイトル]
URL: [記事のURL]
解説: [150文字程度の解説。食産業での活用事例を含む]

Input Articles:
{articles_text}

Output:
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=8192,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating overall summary: {e}")
            return None
    
    def parse_notable_articles(self, summary_text):
        """
        注目記事のサマリーテキストをパースして構造化データに変換
        
        Args:
            summary_text (str): Gemini APIからの構造化された出力テキスト
        
        Returns:
            list[dict]: パースされた注目記事のリスト。各記事は以下のキーを含む:
                - index (str, optional): 記事番号
                - title (str): 記事タイトル
                - url (str): 記事URL
                - description (str): 食産業視点での解説（約150文字）
        
        Note:
            - 日本語と英語のフィールド名の両方に対応
            - 必須フィールド: title, url, description
        """
        if not summary_text:
            return []
        
        # 記事区切りを定数として定義
        ARTICLE_DELIMITER = '===記事'
        
        notable_articles = []
        # 記事ごとにセクションを分割
        sections = summary_text.split(ARTICLE_DELIMITER)
        
        for section in sections[1:]:  # 最初の空セクションをスキップ
            article_info = {}
            lines = section.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                # 番号 (optional field)
                if line.startswith('番号:') or line.startswith('Index:'):
                    article_info['index'] = line.split(':', 1)[1].strip()
                # タイトル (required)
                elif line.startswith('タイトル:') or line.startswith('Title:'):
                    article_info['title'] = line.split(':', 1)[1].strip()
                # URL (required)
                elif line.startswith('URL:'):
                    article_info['url'] = line.split(':', 1)[1].strip()
                # 解説 (required)
                elif line.startswith('解説:') or line.startswith('Description:'):
                    article_info['description'] = line.split(':', 1)[1].strip()
            
            # Validate that all required fields are present
            if article_info.get('title') and article_info.get('url') and article_info.get('description'):
                notable_articles.append(article_info)
        
        return notable_articles

    def generate_tags(self, title, summary, available_tags):
        """記事のタイトルと要約から関連タグを生成"""
        if not self.client or not available_tags:
            return []

        # タグリストを文字列にする
        tags_list = ", ".join(available_tags)

        prompt = f"""
以下の技術記事のタイトルと要約を読んで、関連するタグを選択してください。

Title: {title}
Summary: {summary}

利用可能なタグ: {tags_list}

条件:
- 上記のタグリストから最大3つまで選択してください
- 記事の内容に最も関連性の高いタグを選んでください
- 同じ概念を表す英語と日本語のタグがある場合は、どちらか一方のみを選んでください（例: "AI"と"人工知能"の両方は選ばない）
- より一般的・認知度の高い表現を優先してください
- タグはカンマ区切りで出力してください（例: AI, セキュリティ, Robotics）
- タグが1つも該当しない場合は「なし」と出力してください

出力（タグのみ、他の文言は不要）:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=256,
                )
            )
            tags_text = response.text.strip()
            
            # "なし"の場合は空リストを返す（大文字小文字を区別しない）
            if tags_text.lower() in self.NO_TAG_RESPONSES:
                return []
            
            # カンマ区切りでタグを分割し、前後の空白を削除
            tags = [tag.strip() for tag in tags_text.split(',')]
            # 空文字を除外
            tags = [tag for tag in tags if tag]
            
            # AIが幻覚でタグを作成していないか検証
            # available_tagsリストに含まれるタグのみを返す
            validated_tags = []
            for tag in tags:
                # 大文字小文字を区別せずに検索
                for available_tag in available_tags:
                    if tag.lower() == available_tag.lower():
                        validated_tags.append(available_tag)  # 元のavailable_tagの表記を使用
                        break
            
            return validated_tags
        except Exception as e:
            print(f"Error generating tags for '{title}': {e}")
            return []
