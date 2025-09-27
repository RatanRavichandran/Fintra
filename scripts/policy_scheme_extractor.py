import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from urllib.parse import urljoin

class SchemeExtractor:
    def __init__(self, base_url="https://myscheme.in"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
    
    def get_scheme_details(self, scheme_url):
        """Extract all details for a specific scheme"""
        try:
            # Get the page content
            full_url = urljoin(self.base_url, scheme_url)
            print(f"Fetching scheme from: {full_url}")
            
            response = self.session.get(full_url)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract scheme title and basic info
            scheme_data = {
                "url": full_url,
                "title": self._extract_title(soup),
                "summary": self._extract_summary(soup),
                "sections": {}
            }
            
            # Extract data from each section
            sections = ['details', 'benefits', 'eligibility', 'application-process', 
                        'documents-required', 'faqs', 'sources']
            
            for section_id in sections:
                section_content = self._extract_section(soup, section_id)
                if section_content:
                    scheme_data["sections"][section_id] = section_content
            
            return scheme_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching scheme: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extract the scheme title"""
        title_elem = soup.find('h1', class_='font-bold')
        return title_elem.text.strip() if title_elem else "Unknown Scheme"
    
    def _extract_summary(self, soup):
        """Extract the scheme summary"""
        summary_elem = soup.find('div', class_='scheme-summary')
        return summary_elem.text.strip() if summary_elem else ""
    
    def _extract_section(self, soup, section_id):
        """Extract content from a specific section"""
        section = soup.find(id=section_id)
        if not section:
            return None
        
        heading_elem = section.find(['h2', 'h3'])
        heading = heading_elem.text.strip() if heading_elem else section_id.replace('-', ' ').title()
        
        content_elem = section.find(class_='markdown-options')
        if not content_elem:
            return {"heading": heading, "content": ""}
        
        # Process different content types
        content = self._process_content(content_elem)
        
        return {
            "heading": heading,
            "content": content
        }
    
    def _process_content(self, content_elem):
        """Process different types of content (text, lists, tables)"""
        result = []
        
        # Process paragraphs
        for p in content_elem.find_all('p'):
            if p.text.strip():
                result.append({"type": "paragraph", "text": p.text.strip()})
        
        # Process lists
        for ul in content_elem.find_all(['ul', 'ol']):
            list_items = []
            for li in ul.find_all('li'):
                list_items.append(li.text.strip())
            list_type = "unordered" if ul.name == 'ul' else "ordered"
            result.append({"type": "list", "list_type": list_type, "items": list_items})
        
        # Process tables
        for table in content_elem.find_all('table'):
            table_data = []
            headers = []
            
            # Extract headers
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]
            
            # Extract rows
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    row = [td.text.strip() for td in tr.find_all(['td', 'th'])]
                    if row:
                        table_data.append(row)
            
            result.append({
                "type": "table", 
                "headers": headers, 
                "data": table_data
            })
        
        # If no structured content was found, extract all text
        if not result:
            result.append({"type": "text", "text": content_elem.get_text(strip=True, separator="\n")})
        
        return result
    
    def search_schemes(self, query, max_results=10):
        """Search for schemes matching the query"""
        try:
            search_url = f"{self.base_url}/search"
            params = {"q": query}
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find scheme cards or results
            scheme_cards = soup.find_all('div', class_='scheme-card')
            
            for card in scheme_cards[:max_results]:
                link = card.find('a')
                title = card.find('h3')
                description = card.find('p')
                
                if link and title:
                    results.append({
                        "title": title.text.strip(),
                        "description": description.text.strip() if description else "",
                        "url": link.get('href')
                    })
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching schemes: {e}")
            return []
    
    def save_to_file(self, data, filename):
        """Save extracted data to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def extract_multiple_schemes(self, scheme_urls, output_dir="scheme_data"):
        """Extract data from multiple schemes and save to files"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for url in scheme_urls:
            scheme_data = self.get_scheme_details(url)
            if scheme_data:
                # Create a filename from the scheme title
                safe_title = re.sub(r'[^\w\s-]', '', scheme_data["title"]).strip().replace(' ', '_')
                filename = os.path.join(output_dir, f"{safe_title}.json")
                self.save_to_file(scheme_data, filename)
                results.append({
                    "title": scheme_data["title"],
                    "url": scheme_data["url"],
                    "file": filename
                })
            
            # Be nice to the server
            time.sleep(2)
        
        return results


def main():
    # Example usage
    extractor = SchemeExtractor()
    
    # Option 1: Extract a specific scheme
    scheme_url = "https://www.myscheme.gov.in/schemes/js-esdcv"
    scheme_data = extractor.get_scheme_details(scheme_url)
    if scheme_data:
        extractor.save_to_file(scheme_data, "scheme_details.json")
        
        # Print a summary of what we extracted
        print(f"\nExtracted: {scheme_data['title']}")
        print(f"Summary: {scheme_data['summary'][:100]}...")
        print("\nSections extracted:")
        for section_id, section in scheme_data["sections"].items():
            print(f"- {section['heading']}")

if __name__ == "__main__":
    main()