from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import requests
import re
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import logging

class WebScraper:
    def __init__(self, base_url: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the WebScraper with configuration parameters.
        
        Args:
            base_url (str): The main URL to scrape
            chunk_size (int): Size of text chunks for splitting
            chunk_overlap (int): Overlap between chunks
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for the scraper"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and belongs to the same domain.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain
        except:
            return False

    def clean_text(self, text: str) -> str:
        """
        Clean scraped text by removing extra whitespace and special characters.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()

    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract meaningful text from HTML content.
        
        Args:
            html_content (str): Raw HTML content
            
        Returns:
            str: Extracted text
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'header', 'footer', 'nav']):
            element.decompose()
        
        # Get text
        text = soup.get_text()
        return self.clean_text(text)

    def get_links_from_html(self, html_content: str, current_url: str) -> List[str]:
        """
        Extract all valid links from HTML content.
        
        Args:
            html_content (str): Raw HTML content
            current_url (str): Current page URL
            
        Returns:
            List[str]: List of valid URLs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(current_url, href)
            
            if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                links.append(absolute_url)
        
        return links

    def scrape_url(self, url: str) -> Dict[str, str]:
        """
        Scrape content from a single URL.
        
        Args:
            url (str): URL to scrape
            
        Returns:
            Dict[str, str]: Dictionary containing URL and its content
        """
        try:
            self.logger.info(f"Scraping URL: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            text_content = self.extract_text_from_html(response.text)
            return {"url": url, "content": text_content}
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None

    def scrape_website(self, max_pages: int = 10) -> List[Dict[str, str]]:
        """
        Scrape the website starting from base_url.
        
        Args:
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[Dict[str, str]]: List of dictionaries containing URLs and their content
        """
        pages_to_visit = [self.base_url]
        scraped_content = []
        
        while pages_to_visit and len(self.visited_urls) < max_pages:
            current_url = pages_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            content = self.scrape_url(current_url)
            
            if content:
                scraped_content.append(content)
                
                # Get new links from the page
                response = requests.get(current_url)
                new_links = self.get_links_from_html(response.text, current_url)
                pages_to_visit.extend(new_links)
        
        return scraped_content

    def process_content(self, scraped_content: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Process scraped content and split into chunks.
        
        Args:
            scraped_content (List[Dict[str, str]]): List of scraped content
            
        Returns:
            List[Dict[str, str]]: List of processed chunks with metadata
        """
        processed_chunks = []
        
        for item in scraped_content:
            chunks = self.text_splitter.split_text(item['content'])
            
            for i, chunk in enumerate(chunks):
                processed_chunks.append({
                    'chunk_id': f"{item['url']}_chunk_{i}",
                    'url': item['url'],
                    'content': chunk
                })
        
        return processed_chunks

def main():
    # Example usage
    base_url = "https://apidog.com/vi/blog/rag-deepseek-r1-ollama-vi/"  # Replace with your target website
    scraper = WebScraper(base_url)
    
    # Scrape the website
    scraped_content = scraper.scrape_website(max_pages=5)
    
    # Process and split the content
    processed_chunks = scraper.process_content(scraped_content)
    
    # Print results
    print(f"Total pages scraped: {len(scraped_content)}")
    print(f"Total chunks created: {len(processed_chunks)}")
    
    # Example of accessing the first chunk
    if processed_chunks:
        print("\nExample chunk:")
        print(f"Chunk ID: {processed_chunks[0]['chunk_id']}")
        print(f"URL: {processed_chunks[0]['url']}")
        print(f"Content preview: {processed_chunks[0]['content'][:200]}...")

if __name__ == "__main__":
    main() 