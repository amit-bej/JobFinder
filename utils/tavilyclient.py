import sys
import os
from tavily import TavilyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

def tavily_search_jobs(prompt,domains,max_results=20, days=3):
    """
    Searches Python developer jobs using Tavily.
    Returns a list of search results.
    """

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not found in environment")

    client = TavilyClient(api_key=api_key)

    query = prompt

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_domains= domains,
        days=days
    )

    return response.get("results", [])


# Example usage
if __name__ == "__main__":
    prompt = """
            Python Developer jobs Hyderabad Secunderabad 3 years experience Python AND (Flask OR FastAPI) REST APIs (PostgreSQL OR MySQL) (Pandas OR NumPy) (Docker OR Git)
"""
    domains = [
            "linkedin.com",
            "naukri.com",
            "indeed.com",
            "glassdoor.com"
        ]
    results = tavily_search_jobs(prompt,domains)
    print(results)
    # for idx, result in enumerate(results, start=1):
    #     print(f"{idx}. {result.get('title')}")
    #     print(f"URL: {result.get('url')}")
    #     print(f"Summary: {result.get('content')}")
    #     print("-" * 80)
