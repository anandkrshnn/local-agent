"""Web-related tools: search, HTTP, scraping"""

import requests
import re
from typing import Dict, Any, Optional
from ..core.sandbox import SandboxPath

class WebTools:
    def __init__(self, agent):
        self.agent = agent
        self.sandbox = SandboxPath()
    
    def web_search(self, query: str, token: str) -> str:
        """Search the web using DuckDuckGo"""
        if not self.agent.broker.validate_and_consume(token, "web_search", query):
            return "Permission denied"
        
        try:
            # Use DuckDuckGo HTML API (no API key)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Extract results
            results = re.findall(r'<a[^>]*href="//([^"]+)"[^>]*>([^<]+)</a>', response.text)
            
            formatted = f"🔍 Search results for '{query}':\n\n"
            for i, (link, title) in enumerate(results[:5]):
                title = re.sub(r'<[^>]+>', '', title)
                formatted += f"{i+1}. **{title[:60]}**\n   {link}\n\n"
            
            if not results:
                formatted = f"No results found for '{query}'"
            
            # Store in memory
            self.agent.memory.store("web_search", {"query": query, "results_count": len(results[:5])})
            
            return formatted
        except Exception as e:
            return f"Search failed: {e}"
    
    def http_request(self, method: str, url: str, token: str, body: str = None, headers: Dict = None) -> str:
        """Make HTTP request to external API"""
        if not self.agent.broker.validate_and_consume(token, "http_request", url):
            return "Permission denied"
        
        # Security: Block internal IPs
        dangerous = ['localhost', '127.0.0.1', '192.168.', '10.', '172.16.', '172.17.']
        for d in dangerous:
            if d in url:
                return f"❌ Blocked: Internal IP addresses not allowed for security"
        
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                data=body,
                timeout=30
            )
            
            result = f"✅ {method.upper()} {url}\n"
            result += f"Status: {response.status_code}\n"
            result += f"Response: {response.text[:1000]}"
            
            self.agent.memory.store("http_request", {"method": method, "url": url, "status": response.status_code})
            
            return result
        except Exception as e:
            return f"Request failed: {e}"
