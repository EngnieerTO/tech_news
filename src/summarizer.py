from google import genai
from google.genai import types
import os

class NewsSummarizer:
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
        """全記事の情報を元に、食産業・フードテックへの応用視点で全体サマリーを生成"""
        if not self.client or not articles:
            return None

        # 記事情報をテキストにまとめる
        articles_text = ""
        for article in articles:
            articles_text += f"- Title: {article['title']}\n"
            articles_text += f"  Summary: {article.get('summary', 'No summary provided')}\n\n"

        prompt = f"""
以下は本日収集された複数のテックニュース記事のタイトルと要約です。
これらすべての情報を踏まえて、**食産業やフードテック（食品関連技術、外食、農業など）に応用できそうな視点**で、全体を俯瞰した要約を作成してください。

条件:
- 文字数は日本語で800〜1000文字程度。
- 単なる記事の羅列ではなく、どのようなトレンドがあり、それがどう食産業に活かせるか、あるいは影響を与えるかを考察してください。
- 直接的に食品に関連しない技術（AI、ロボティクスなど）であっても、食品業界への応用可能性を見出して記述してください。
- 洞察を深め、具体例や将来予測も交えて詳しく記述してください。

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
                    max_output_tokens=4096,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating overall summary: {e}")
            return None
