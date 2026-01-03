import yaml
import feedparser
from datetime import datetime, timedelta
from dateutil import parser
import os
import pytz

class GrantCollector:
    def __init__(self, config_path='grant_config.yaml'):
        self.config = self._load_config(config_path)
        self.keywords = self.config.get('keywords', [])
        self.sources = self.config.get('sources', [])
        self.days_limit = self.config.get('days_limit', 7)

    def _load_config(self, path):
        """YAML設定ファイルを読み込む"""
        # 実行ディレクトリからの相対パスを考慮
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Config file not found at {full_path}")
            return {}

    def collect_grants(self):
        """設定されたソースから助成金情報を収集し、キーワードでフィルタリングする"""
        all_articles = []

        for source in self.sources:
            source_name = source.get('name')
            source_url = source.get('url')
            source_type = source.get('type')
            source_category = source.get('category', 'Uncategorized')

            print(f"Fetching from: {source_name} ({source_category})...")

            if source_type == 'rss':
                articles = self._fetch_rss(source_url, source_name, source_category)
                all_articles.extend(articles)
            else:
                print(f"Unknown source type: {source_type}")

        # キーワードでフィルタリング
        filtered_articles = self._filter_by_keywords(all_articles)
        return filtered_articles

    def _fetch_rss(self, url, source_name, source_category):
        """RSSフィードから記事を取得"""
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"Error fetching RSS from {url}: {e}")
            return []
        
        articles = []
        
        # 基準日時を計算（現在時刻 - days_limit）
        now = datetime.now(pytz.utc)
        limit_date = now - timedelta(days=self.days_limit) if self.days_limit > 0 else None

        for entry in feed.entries:
            # 公開日時を取得・パース
            published_str = entry.get('published', '') or entry.get('updated', '')
            published_dt = None
            
            if published_str:
                try:
                    published_dt = parser.parse(published_str)
                    # タイムゾーンがない場合はUTC扱いにする
                    if published_dt.tzinfo is None:
                        published_dt = published_dt.replace(tzinfo=pytz.utc)
                except Exception:
                    pass # パース失敗時は日付チェックをスキップ（または除外）

            # 日付フィルタリング
            if limit_date and published_dt:
                if published_dt < limit_date:
                    continue # 古い記事はスキップ

            article = {
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'summary': entry.get('summary', '') or entry.get('description', ''),
                'published': published_str,
                'source': source_name,
                'category': source_category,
                'collected_at': datetime.now().isoformat()
            }
            articles.append(article)
        
        return articles

    def _filter_by_keywords(self, articles):
        """キーワードが含まれる記事のみを抽出"""
        if not self.keywords:
            return articles # キーワード設定がなければ全件返す

        filtered = []
        for article in articles:
            # タイトルと要約を検索対象にする
            text_to_search = (article['title'] + " " + article['summary']).lower()
            
            # いずれかのキーワードが含まれていれば採用
            for keyword in self.keywords:
                if keyword.lower() in text_to_search:
                    article['matched_keyword'] = keyword
                    filtered.append(article)
                    break
        
        return filtered
