import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://www.myscheme.gov.in/schemes/fadsp1012e")

        # Print the extracted content
        print(result.html)

# Run the async main function
asyncio.run(main())