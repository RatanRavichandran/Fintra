import asyncio
import os
from crawl4ai import AsyncWebCrawler
from openai import OpenAI

async def main():
    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://www.myscheme.gov.in/schemes/fadsp1012e")
        
        # Extract the raw markdown content
        raw_content = result.markdown
        
        # Clean the content using OpenAI
        cleaned_content = clean_content_with_openai(client, raw_content)
        
        # Print the cleaned content
        print(cleaned_content)

def clean_content_with_openai(client, content):
    """
    Use OpenAI to clean the content by removing social media elements and other generic website components.
    """
    try:
        # Create a prompt for OpenAI
        prompt = f"""
        I have the following content extracted from a webpage. Please clean this content by:
        
        1. Removing all social media buttons, share links, and related elements
        2. Removing navigation menus, footers, and headers that aren't part of the main content
        3. Removing any advertisements or promotional elements
        4. Removing any cookie consent notices or popups
        5. Preserving all the main content, including headings, paragraphs, lists, and tables
        6. Maintaining the original structure and formatting of the main content
        7. Ensuring all important information about the scheme is retained
        
        Return only the cleaned content without any explanations.
        
        Here's the content:
        
        {content}
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # You can use "gpt-4" for better results if available
            messages=[
                {"role": "system", "content": "You are a content cleaning assistant that removes generic website elements while preserving the main content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more consistent results
            max_tokens=4000,  # Adjust based on your content length
        )
        
        # Extract and return the cleaned content
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error cleaning content with OpenAI: {e}")
        # Return the original content if there's an error
        return content

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())