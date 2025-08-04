import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import time
import logging
from collections import deque
import csv
from typing import Set, Dict, List, Optional, Tuple
import re


class WebCrawler:
    """A respectful web crawler that systematically discovers and visits web pages."""
    
    def __init__(self, 
                 start_url: str,
                 max_depth: int = 2,
                 delay: float = 1.0,
                 max_pages: int = 100,
                 respect_robots: bool = True,
                 allowed_domains: Optional[List[str]] = None,
                 search_words: Optional[List[str]] = None):
        """
        Initialize the web crawler.
        
        Args:
            start_url: The seed URL to start crawling from
            max_depth: Maximum depth to crawl (0 means only seed URL)
            delay: Delay between requests in seconds
            max_pages: Maximum number of pages to crawl
            respect_robots: Whether to respect robots.txt
            allowed_domains: List of allowed domains (None means same domain as seed)
            search_words: List of words/phrases to search for in page content
        """
        self.start_url = self._normalize_url(start_url)
        self.max_depth = max_depth
        self.delay = delay
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self.search_words = [word.lower() for word in search_words] if search_words else []
        
        # Parse the start URL to get domain info
        parsed_start = urlparse(self.start_url)
        self.start_domain = parsed_start.netloc
        
        # Set allowed domains
        if allowed_domains is None:
            self.allowed_domains = {self.start_domain}
        else:
            self.allowed_domains = set(allowed_domains)
            
        # Initialize crawler state
        self.visited_urls: Set[str] = set()
        self.crawled_data: List[Dict] = []
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WebCrawler/1.0 (+https://example.com/crawler)'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and ensuring proper format."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        # Remove fragment and normalize
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        
        return normalized
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be crawled."""
        try:
            parsed = urlparse(url)
            
            # Check if it's a valid HTTP/HTTPS URL
            if parsed.scheme not in ['http', 'https']:
                return False
                
            # Check if domain is allowed
            if parsed.netloc not in self.allowed_domains:
                return False
                
            # Skip common non-HTML file extensions
            path = parsed.path.lower()
            skip_extensions = {
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.tar', '.gz', '.rar', '.exe', '.dmg',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
                '.mp3', '.mp4', '.avi', '.mov', '.wmv',
                '.css', '.js', '.xml', '.rss', '.json'
            }
            
            for ext in skip_extensions:
                if path.endswith(ext):
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.warning(f"Invalid URL format: {url} - {e}")
            return False
    
    def _can_fetch(self, url: str) -> bool:
        """Check if we can fetch the URL according to robots.txt."""
        if not self.respect_robots:
            return True
            
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            if domain not in self.robots_cache:
                robots_url = f"{parsed.scheme}://{domain}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_cache[domain] = rp
                except Exception as e:
                    self.logger.warning(f"Could not fetch robots.txt for {domain}: {e}")
                    # If we can't fetch robots.txt, assume we can crawl
                    return True
            
            rp = self.robots_cache[domain]
            user_agent = self.session.headers.get('User-Agent', '*')
            if isinstance(user_agent, bytes):
                user_agent = user_agent.decode('utf-8')
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True
    
    def _extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract all valid links from HTML content."""
        links = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all anchor tags with href attributes
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and isinstance(href, str):
                    # Convert relative URLs to absolute URLs
                    absolute_url = urljoin(base_url, href)
                    normalized_url = self._normalize_url(absolute_url)
                    
                    if self._is_valid_url(normalized_url):
                        links.add(normalized_url)
                        
        except Exception as e:
            self.logger.error(f"Error extracting links from {base_url}: {e}")
            
        return links
    
    def _search_content(self, text_content: str) -> Dict[str, int]:
        """Search for specified words in page content and return counts."""
        if not self.search_words:
            return {}
            
        text_lower = text_content.lower()
        word_counts = {}
        
        for word in self.search_words:
            # Count occurrences of the word/phrase
            count = text_lower.count(word)
            word_counts[word] = count
            
        return word_counts
    
    def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page and extract metadata."""
        try:
            self.logger.info(f"Fetching: {url}")
            
            # Check robots.txt
            if not self._can_fetch(url):
                self.logger.info(f"Robots.txt disallows crawling: {url}")
                return None
            
            # Make the request
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if it's HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                self.logger.info(f"Skipping non-HTML content: {url}")
                return None
            
            # Parse HTML and extract metadata
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = ''
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract meta description
            description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                       soup.find('meta', attrs={'property': 'og:description'})
            if meta_desc:
                content = meta_desc.get('content')
                if content and isinstance(content, str):
                    description = content.strip()
            
            # Extract text content for word searching
            page_text = soup.get_text()
            word_counts = self._search_content(page_text)
            
            # Extract links for further crawling
            links = self._extract_links(response.text, url)
            
            page_data = {
                'url': url,
                'title': title,
                'description': description,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'links_found': len(links),
                'word_matches': word_counts,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return {
                'data': page_data,
                'links': links
            }
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout while fetching: {url}")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error while fetching: {url}")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error {e.response.status_code} while fetching: {url}")
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching {url}: {e}")
            
        return None
    
    def crawl(self) -> List[Dict]:
        """
        Start crawling from the seed URL.
        
        Returns:
            List of dictionaries containing page data
        """
        self.logger.info(f"Starting crawl from: {self.start_url}")
        self.logger.info(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        self.logger.info(f"Delay between requests: {self.delay}s")
        
        # Initialize crawling queue: (url, depth)
        crawl_queue: deque[Tuple[str, int]] = deque([(self.start_url, 0)])
        pages_crawled = 0
        
        while crawl_queue and pages_crawled < self.max_pages:
            current_url, depth = crawl_queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
                
            # Skip if depth exceeds limit
            if depth > self.max_depth:
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            # Fetch the page
            result = self._fetch_page(current_url)
            
            if result:
                # Store the page data
                self.crawled_data.append(result['data'])
                pages_crawled += 1
                
                self.logger.info(f"Successfully crawled: {current_url} "
                               f"(Title: {result['data']['title'][:50]}...)")
                
                # Add new links to queue if we haven't reached max depth
                if depth < self.max_depth:
                    for link in result['links']:
                        if link not in self.visited_urls:
                            crawl_queue.append((link, depth + 1))
            
            # Rate limiting - be respectful
            if crawl_queue:  # Don't delay after the last request
                time.sleep(self.delay)
        
        self.logger.info(f"Crawling completed. Total pages crawled: {len(self.crawled_data)}")
        return self.crawled_data
    
    def save_to_csv(self, filename: str = 'crawl_results.csv'):
        """Save crawled data to CSV file."""
        if not self.crawled_data:
            self.logger.warning("No data to save")
            return
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'title', 'description', 'status_code', 
                         'content_length', 'links_found', 'word_matches', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in self.crawled_data:
                # Convert word_matches dict to string for CSV
                row_copy = row.copy()
                if 'word_matches' in row_copy:
                    word_matches_str = ', '.join([f"{word}:{count}" for word, count in row_copy['word_matches'].items()])
                    row_copy['word_matches'] = word_matches_str
                writer.writerow(row_copy)
                
        self.logger.info(f"Results saved to {filename}")
    
    def print_results(self):
        """Print crawling results to console."""
        if not self.crawled_data:
            print("No pages were crawled.")
            return
            
        print(f"\n{'='*80}")
        print(f"CRAWL RESULTS - {len(self.crawled_data)} pages crawled")
        print(f"{'='*80}")
        
        for i, page in enumerate(self.crawled_data, 1):
            print(f"\n{i}. {page['url']}")
            print(f"   Title: {page['title']}")
            if page['description']:
                print(f"   Description: {page['description'][:100]}...")
            print(f"   Status: {page['status_code']} | "
                  f"Size: {page['content_length']:,} bytes | "
                  f"Links: {page['links_found']}")
            
            # Show word search results if any
            if page.get('word_matches') and any(count > 0 for count in page['word_matches'].values()):
                matches = [f"{word}({count})" for word, count in page['word_matches'].items() if count > 0]
                print(f"   Word matches: {', '.join(matches)}")
            
            print(f"   Crawled: {page['timestamp']}")
