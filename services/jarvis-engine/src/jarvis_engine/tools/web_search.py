import asyncio
from urllib.parse import urlparse
from tavily import TavilyClient
from duckduckgo_search import DDGS
from typing import List, Dict

async def search_tavily(
  query: str,
  max_results: int = 5,
  api_key: str = ""
) -> List[Dict]:
  try:
    client = TavilyClient(api_key=api_key)
    
    # Run sync client on thread pool
    response = await asyncio.to_thread(
      client.search,
      query=query,
      max_results=max_results,
      search_depth="basic"
    )
    
    results = []
    for r in response.get("results", []):
      url = r.get("url", "")
      domain = urlparse(url).netloc.replace(
        "www.", ""
      )
      results.append({
        "title": r.get("title", ""),
        "url": url,
        "snippet": r.get("content", "")[:300],
        "source": domain
      })
    return results
  except Exception as e:
    print(f"Tavily error: {e}")
    return []

async def search_duckduckgo(
  query: str,
  max_results: int = 5
) -> List[Dict]:
  try:
    def _sync_search(q, n):
      with DDGS() as ddgs:
        return list(ddgs.text(q, max_results=n))
    
    # Run sync DDG on thread pool
    raw_results = await asyncio.to_thread(
      _sync_search, query, max_results
    )
    
    results = []
    for r in raw_results:
      url = r.get("href", "")
      domain = urlparse(url).netloc.replace(
        "www.", ""
      )
      results.append({
        "title": r.get("title", ""),
        "url": url,
        "snippet": r.get("body", "")[:300],
        "source": domain
      })
    return results
  except Exception as e:
    print(f"DuckDuckGo error: {e}")
    return []

async def search_web(
  query: str,
  max_results: int = 5
) -> List[Dict]:
  from ..core.config import settings
  
  if settings.TAVILY_API_KEY and \
     settings.SEARCH_PROVIDER == "tavily":
    results = await search_tavily(
      query, max_results, settings.TAVILY_API_KEY
    )
    if results:
      return results
    print("Tavily failed, falling back to DuckDuckGo")
  
  return await search_duckduckgo(query, max_results)

def format_search_results(
  results: List[Dict],
  query: str
) -> str:
  if not results:
    return f"No results found for: {query}"
  
  formatted = (
    f"Web search results for '{query}':\n\n"
  )
  for i, r in enumerate(results, 1):
    formatted += f"{i}. {r['title']}\n"
    formatted += f"   {r['snippet']}\n"
    formatted += f"   Source: {r['url']}\n\n"
  return formatted
