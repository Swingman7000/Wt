#!/usr/bin/env python3
"""
Web Crawler - A Python command-line website crawler
"""

import argparse
import sys
import os
from crawler import WebCrawler


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="A respectful web crawler that systematically discovers and visits web pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com --depth 3 --delay 2 --max-pages 50
  %(prog)s https://example.com --output results.csv --no-robots
  %(prog)s https://example.com --domains example.com,blog.example.com
  %(prog)s https://en.wikipedia.org/wiki/Python --search "programming,language,code"
        """
    )
    
    parser.add_argument(
        'url',
        help='The seed URL to start crawling from'
    )
    
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=2,
        help='Maximum crawling depth (default: 2)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '-m', '--max-pages',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output CSV file name (default: crawl_results.csv)'
    )
    
    parser.add_argument(
        '--domains',
        help='Comma-separated list of allowed domains (default: same domain as seed URL)'
    )
    
    parser.add_argument(
        '--no-robots',
        action='store_true',
        help='Ignore robots.txt (not recommended)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Don\'t save results to CSV file'
    )
    
    parser.add_argument(
        '-s', '--search',
        help='Comma-separated list of words/phrases to search for in page content'
    )
    
    return parser.parse_args()


def validate_url(url):
    """Basic URL validation."""
    if not url:
        return False
        
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # Basic validation
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Validate URL
    if not validate_url(args.url):
        print(f"Error: Invalid URL '{args.url}'", file=sys.stderr)
        sys.exit(1)
    
    # Parse domains if provided
    allowed_domains = None
    if args.domains:
        allowed_domains = [domain.strip() for domain in args.domains.split(',')]
    
    # Parse search words if provided
    search_words = None
    if args.search:
        search_words = [word.strip() for word in args.search.split(',')]
    
    # Set up output file
    output_file = args.output or 'crawl_results.csv'
    
    try:
        # Create crawler instance
        crawler = WebCrawler(
            start_url=args.url,
            max_depth=args.depth,
            delay=args.delay,
            max_pages=args.max_pages,
            respect_robots=not args.no_robots,
            allowed_domains=allowed_domains,
            search_words=search_words
        )
        
        if not args.quiet:
            print(f"Starting web crawl...")
            print(f"Seed URL: {args.url}")
            print(f"Max depth: {args.depth}")
            print(f"Max pages: {args.max_pages}")
            print(f"Delay: {args.delay}s")
            print(f"Respect robots.txt: {not args.no_robots}")
            if allowed_domains:
                print(f"Allowed domains: {', '.join(allowed_domains)}")
            if search_words:
                print(f"Searching for words: {', '.join(search_words)}")
            print("-" * 50)
        
        # Start crawling
        results = crawler.crawl()
        
        if not results:
            print("No pages were successfully crawled.")
            sys.exit(1)
        
        # Save results to CSV unless disabled
        if not args.no_save:
            crawler.save_to_csv(output_file)
            if not args.quiet:
                print(f"\nResults saved to: {output_file}")
        
        # Print results unless quiet mode
        if not args.quiet:
            crawler.print_results()
        
        # Summary
        if not args.quiet:
            print(f"\nCrawl Summary:")
            print(f"- Pages successfully crawled: {len(results)}")
            print(f"- Total URLs discovered: {len(crawler.visited_urls)}")
            if not args.no_save:
                print(f"- Results saved to: {output_file}")
                
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
