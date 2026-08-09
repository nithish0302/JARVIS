from duckduckgo_search import DDGS
from typing import List, Dict

class WebSearchResult:
  title: str
  url: str
  snippet: str

async def search_web(
  query: str,
  max_results: int = 5
) -> List[Dict]:
  try:
    results = []
    with DDGS() as ddgs:
      for r in ddgs.text(
        query, 
        max_results=max_results
      ):
        results.append({
          "title": r.get("title", ""),
          "url": r.get("href", ""),
          "snippet": r.get("body", "")
        })
    return results
  except Exception as e:
    print(f"Search error: {e}")
    return []

def format_search_results(
  results: List[Dict],
  query: str
) -> str:
  if not results:
    return f"No results found for: {query}"
  
  formatted = f"Web search results for '{query}':\n\n"
  for i, r in enumerate(results, 1):
    formatted += f"{i}. {r['title']}\n"
    formatted += f"   {r['snippet']}\n"
    formatted += f"   Source: {r['url']}\n\n"
  return formatted
