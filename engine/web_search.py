from tavily import TavilyClient
import json
import asyncio
import requests

class WebSearch:
    def __init__(self):
        self.client = None
        self.scraper_key = None

    def make_client(self, config):
        web_search_config = config.get('tools', {}).get('web_search', {})

        tavily_key = web_search_config.get('tavily_api_key')
        self.client = TavilyClient(tavily_key) if tavily_key else None

        scraper_key = web_search_config.get('scraper_api_key')
        self.scraper_key = scraper_key if scraper_key else None

    async def web_search(self, query, max_results=4):
        search_res = await asyncio.to_thread(self.client.search, query=query, search_depth="advanced", include_answer='advanced', max_results=max_results)

        res = {
            'event_name': 'Web Search Results',
            'content': json.dumps({
                'ai_summary': search_res['answer'],
                'results': search_res['results']
            }, indent=2)
        }

        return res

    def scrape(self, url):
        payload = {
            'api_key': self.scraper_key,
            'url': url,
            'render': 'false',
            'output_format': 'text'
        }
        res = requests.get('https://api.scraperapi.com/', params=payload)

        res = {
            'event_name': 'Scraped Page Data',
            'content': res.text
        }

        return res
