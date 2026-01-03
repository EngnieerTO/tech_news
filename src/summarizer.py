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

出力は3～5点の箇条書きのみにしてください。

Title: {title}
Summary: {original_summary}
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
