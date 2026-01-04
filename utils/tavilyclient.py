import sys
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")


def tavily_search_jobs(prompt, domains, max_results=20, days=3):
    """
    Searches jobs using Tavily with advanced features.
    Returns a list of search results with raw content for better extraction.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not found in environment")

    client = TavilyClient(api_key=api_key)

    response = client.search(
        query=prompt,
        search_depth="advanced",
        max_results=max_results,
        include_domains=domains,
        days=days,
        include_raw_content=True,
        topic="general"
    )

    return response.get("results", [])
