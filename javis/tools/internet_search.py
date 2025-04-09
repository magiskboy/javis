from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import httpx

__all__ = [
    "search",
]

def make_request_as_human(url):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "identity",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = httpx.get(url, headers=headers, verify=False, follow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')
    body_tag = soup.find('body')
    if body_tag:
        text = ' '.join(body_tag.get_text().split())
    else:
        text = None
    return text


def search(query: str, k: int = 3) -> str:
    """Perform a web search using DuckDuckGo and fetch the content of the resulting pages.
    
    Args:
        query (str): The search query to be executed.
        k (int, optional): The maximum number of search results to return. Defaults to 3.
        
    Returns:
        str: A formatted string containing search results with titles, URLs, and content.
             Returns "No results found" if no results are available.
    """
    with DDGS() as ddgs:
        duck_results = ddgs.text(query, max_results=k)
        results = []
        for result in duck_results:
            body = make_request_as_human(result["href"])
            if body is None:
                continue
            results.append({
                **result,
                "body": body
            })

        if len(results) == 0:
            return "No results found"

        formatted_results = []
        for result in results:
            formatted_results.append(
                f"- title: {result['title']}\n"
                f"  url: {result['href']}\n"
                f"  content: {result['body']}"
            )
        return "\n".join(formatted_results)