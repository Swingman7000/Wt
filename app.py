#!/usr/bin/env python3
"""
Web Crawler & Tools - Flask Web Application
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import json
import os
import threading
import time
from datetime import datetime, date
from crawler import WebCrawler
import csv
import io
import requests
from urllib.parse import urljoin, urlparse
import re
from models import db, CrawlJob, CrawledPage, EncryptionHistory, ProxyRequest, ToolUsageStats

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    # Initialize database
    db.init_app(app)
else:
    # Fallback configuration for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webtools.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

# Store crawling results temporarily (for backwards compatibility)
crawl_results = {}
crawl_status = {}

@app.route('/')
def index():
    """Main page with tool selection."""
    # Track page view
    track_tool_usage('home')
    return render_template('index.html')

@app.route('/web-crawler')
def web_crawler():
    """Web crawler tool page."""
    track_tool_usage('crawler')
    return render_template('crawler.html')

@app.route('/html-encryptor')
def html_encryptor():
    """HTML text encryptor tool page."""
    track_tool_usage('encryptor')
    return render_template('encryptor.html')

@app.route('/web-proxy')
def web_proxy():
    """Web proxy tool page."""
    track_tool_usage('proxy')
    return render_template('proxy.html')

@app.route('/stats')
def stats():
    """Statistics dashboard page."""
    track_tool_usage('stats')
    return render_template('stats.html')

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """Start a web crawling job."""
    try:
        data = request.get_json()
        
        # Generate unique job ID
        job_id = f"crawl_{int(time.time())}"
        
        # Extract parameters
        url = data.get('url', '').strip()
        search_type = data.get('searchType', 'both')  # 'text', 'links', 'both'
        search_words = data.get('searchWords', '').strip()
        depth = int(data.get('depth', 2))
        max_pages = int(data.get('maxPages', 10))
        delay = float(data.get('delay', 1.0))
        domains = data.get('domains', '').strip()
        respect_robots = data.get('respectRobots', True)
        
        # Validate URL
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Parse domains and search words
        allowed_domains = None
        if domains:
            allowed_domains = [d.strip() for d in domains.split(',')]
            
        search_word_list = None
        if search_words and search_type in ['text', 'both']:
            search_word_list = [w.strip() for w in search_words.split(',')]
        
        # Create database record
        crawl_job = CrawlJob(
            job_id=job_id,
            url=url,
            search_type=search_type,
            search_words=json.dumps(search_word_list) if search_word_list else None,
            depth=depth,
            max_pages=max_pages,
            delay=delay,
            domains=json.dumps(allowed_domains) if allowed_domains else None,
            respect_robots=respect_robots,
            status='starting',
            message='Initializing crawler...'
        )
        db.session.add(crawl_job)
        db.session.commit()

        # Initialize status (for backwards compatibility)
        crawl_status[job_id] = {
            'status': 'starting',
            'progress': 0,
            'total_pages': 0,
            'current_url': '',
            'message': 'Initializing crawler...'
        }
        
        # Start crawling in background thread
        thread = threading.Thread(
            target=run_crawler,
            args=(crawl_job.id, job_id, url, depth, max_pages, delay, respect_robots, allowed_domains, search_word_list, search_type)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id, 'status': 'started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_crawler(db_job_id, job_id, url, depth, max_pages, delay, respect_robots, allowed_domains, search_words, search_type):
    """Run the crawler in a background thread."""
    try:
        # Update database status
        with app.app_context():
            crawl_job = db.session.get(CrawlJob, db_job_id)
            if crawl_job:
                crawl_job.status = 'running'
                crawl_job.message = 'Starting crawler...'
                db.session.commit()
        
        # Update in-memory status (for backwards compatibility)
        crawl_status[job_id]['status'] = 'running'
        crawl_status[job_id]['message'] = 'Starting crawler...'
        
        # Create crawler instance
        crawler = WebCrawler(
            start_url=url,
            max_depth=depth,
            delay=delay,
            max_pages=max_pages,
            respect_robots=respect_robots,
            allowed_domains=allowed_domains,
            search_words=search_words
        )
        
        # Start crawling
        results = crawler.crawl()
        
        # Process results based on search type
        processed_results = []
        for page in results:
            page_result = {
                'url': page['url'],
                'title': page['title'],
                'description': page['description'],
                'status_code': page['status_code'],
                'content_length': page['content_length'],
                'timestamp': page['timestamp']
            }
            
            # Add links information if requested
            if search_type in ['links', 'both']:
                page_result['links_found'] = page.get('links_found', 0)
            
            # Add word search results if requested
            if search_type in ['text', 'both'] and page.get('word_matches'):
                page_result['word_matches'] = page['word_matches']
                page_result['total_word_matches'] = sum(page['word_matches'].values())
            
            processed_results.append(page_result)
        
        # Store results in database
        with app.app_context():
            crawl_job = db.session.get(CrawlJob, db_job_id)
            if crawl_job:
                # Save crawled pages to database
                for page_data in processed_results:
                    crawled_page = CrawledPage(
                        crawl_job_id=db_job_id,
                        url=page_data['url'],
                        title=page_data['title'],
                        description=page_data['description'],
                        status_code=page_data['status_code'],
                        content_length=page_data['content_length'],
                        links_found=page_data.get('links_found', 0),
                        word_matches=json.dumps(page_data.get('word_matches', {})),
                        total_word_matches=page_data.get('total_word_matches', 0)
                    )
                    db.session.add(crawled_page)
                
                # Update job status
                crawl_job.status = 'completed'
                crawl_job.progress = 100
                crawl_job.total_pages = len(processed_results)
                crawl_job.message = f'Crawling completed! Found {len(processed_results)} pages.'
                crawl_job.completed_at = datetime.utcnow()
                db.session.commit()
        
        # Store results in memory (for backwards compatibility)
        crawl_results[job_id] = {
            'results': processed_results,
            'summary': {
                'total_pages': len(processed_results),
                'total_urls_discovered': len(crawler.visited_urls),
                'search_type': search_type,
                'search_words': search_words or [],
                'completed_at': datetime.now().isoformat()
            }
        }
        
        # Update final status
        crawl_status[job_id] = {
            'status': 'completed',
            'progress': 100,
            'total_pages': len(processed_results),
            'message': f'Crawling completed! Found {len(processed_results)} pages.'
        }
        
    except Exception as e:
        # Update database status
        with app.app_context():
            crawl_job = db.session.get(CrawlJob, db_job_id)
            if crawl_job:
                crawl_job.status = 'error'
                crawl_job.message = f'Error: {str(e)}'
                db.session.commit()
        
        # Update in-memory status
        crawl_status[job_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }

@app.route('/api/crawl/status/<job_id>')
def get_crawl_status(job_id):
    """Get the status of a crawling job."""
    if job_id not in crawl_status:
        return jsonify({'error': 'Job not found'}), 404
        
    return jsonify(crawl_status[job_id])

@app.route('/api/crawl/results/<job_id>')
def get_crawl_results(job_id):
    """Get the results of a completed crawling job."""
    if job_id not in crawl_results:
        return jsonify({'error': 'Results not found'}), 404
        
    return jsonify(crawl_results[job_id])

@app.route('/api/crawl/download/<job_id>')
def download_results(job_id):
    """Download crawl results as CSV."""
    if job_id not in crawl_results:
        return jsonify({'error': 'Results not found'}), 404
    
    try:
        results = crawl_results[job_id]['results']
        summary = crawl_results[job_id]['summary']
        
        # Create CSV content
        output = io.StringIO()
        
        # Determine fieldnames based on search type
        fieldnames = ['url', 'title', 'description', 'status_code', 'content_length', 'timestamp']
        
        if summary['search_type'] in ['links', 'both']:
            fieldnames.append('links_found')
            
        if summary['search_type'] in ['text', 'both']:
            fieldnames.extend(['word_matches', 'total_word_matches'])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in results:
            csv_row = {k: v for k, v in row.items() if k in fieldnames}
            
            # Convert word_matches dict to string for CSV
            if 'word_matches' in csv_row and isinstance(csv_row['word_matches'], dict):
                csv_row['word_matches'] = ', '.join([f"{word}:{count}" for word, count in csv_row['word_matches'].items()])
            
            writer.writerow(csv_row)
        
        # Create file-like object
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"crawl_results_{timestamp}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy')
def proxy():
    """Proxy web requests to bypass CORS and provide anonymity."""
    target_url = request.args.get('url')
    remove_scripts = request.args.get('removeScripts', 'true').lower() == 'true'
    remove_cookies = request.args.get('removeCookies', 'true').lower() == 'true'
    
    if not target_url:
        return "No URL provided", 400
    
    try:
        # Make request to target URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(target_url, headers=headers, timeout=10)
        content = response.text
        
        # Basic content filtering for security
        if remove_scripts:
            # Remove script tags and inline JavaScript
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
        
        # Remove cookie-related headers if requested
        if remove_cookies:
            content = re.sub(r'document\.cookie\s*=', '// document.cookie =', content, flags=re.IGNORECASE)
        
        # Fix relative URLs to absolute
        parsed_url = urlparse(target_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Fix href attributes
        content = re.sub(r'href\s*=\s*["\'](?!//)([^"\']+)["\']', 
                        lambda m: f'href="/api/proxy?url={urljoin(base_url, m.group(1))}"', content)
        
        # Fix src attributes
        content = re.sub(r'src\s*=\s*["\'](?!//)([^"\']+)["\']', 
                        lambda m: f'src="{urljoin(base_url, m.group(1))}"', content)
        
        # Create response with appropriate headers
        proxy_response = Response(content)
        proxy_response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html')
        
        # Add security headers
        proxy_response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        proxy_response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Log proxy request to database
        log_proxy_request(target_url, remove_scripts, remove_cookies, response.status_code, len(content), request.remote_addr, request.headers.get('User-Agent'))
        
        return proxy_response
        
    except requests.exceptions.RequestException as e:
        log_proxy_request(target_url, remove_scripts, remove_cookies, 0, 0, request.remote_addr, request.headers.get('User-Agent'))
        return f"Error fetching URL: {str(e)}", 500
    except Exception as e:
        return f"Proxy error: {str(e)}", 500

def track_tool_usage(tool_name):
    """Track tool usage statistics."""
    try:
        with app.app_context():
            today = date.today()
            stats = ToolUsageStats.query.filter_by(tool_name=tool_name, date=today).first()
            
            if stats:
                stats.page_views += 1
                stats.last_accessed = datetime.utcnow()
            else:
                stats = ToolUsageStats(
                    tool_name=tool_name,
                    page_views=1,
                    date=today
                )
                db.session.add(stats)
            
            db.session.commit()
    except Exception as e:
        print(f"Error tracking usage: {e}")

def log_encryption_activity(operation_type, encryption_method, has_password, input_length, output_length, ip_address):
    """Log encryption/decryption activity."""
    try:
        with app.app_context():
            history = EncryptionHistory(
                operation_type=operation_type,
                encryption_method=encryption_method,
                has_password=has_password,
                input_length=input_length,
                output_length=output_length,
                ip_address=ip_address
            )
            db.session.add(history)
            db.session.commit()
    except Exception as e:
        print(f"Error logging encryption activity: {e}")

def log_proxy_request(target_url, remove_scripts, remove_cookies, status_code, response_size, ip_address, user_agent):
    """Log proxy request."""
    try:
        with app.app_context():
            proxy_req = ProxyRequest(
                target_url=target_url,
                remove_scripts=remove_scripts,
                remove_cookies=remove_cookies,
                status_code=status_code,
                response_size=response_size,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(proxy_req)
            db.session.commit()
    except Exception as e:
        print(f"Error logging proxy request: {e}")

@app.route('/api/stats')
def get_stats():
    """Get usage statistics."""
    try:
        stats = {}
        
        # Tool usage stats
        tool_stats = db.session.query(ToolUsageStats).all()
        stats['tool_usage'] = [stat.to_dict() for stat in tool_stats]
        
        # Crawl job stats
        crawl_count = db.session.query(CrawlJob).count()
        stats['total_crawl_jobs'] = crawl_count
        
        # Recent crawl jobs
        recent_crawls = db.session.query(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(5).all()
        stats['recent_crawls'] = [job.to_dict() for job in recent_crawls]
        
        # Encryption activity count
        encryption_count = db.session.query(EncryptionHistory).count()
        stats['total_encryption_operations'] = encryption_count
        
        # Proxy request count
        proxy_count = db.session.query(ProxyRequest).count()
        stats['total_proxy_requests'] = proxy_count
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/log-encryption', methods=['POST'])
def log_encryption():
    """Log encryption activity."""
    try:
        data = request.get_json()
        log_encryption_activity(
            operation_type=data.get('operation_type'),
            encryption_method=data.get('encryption_method'),
            has_password=data.get('has_password', False),
            input_length=data.get('input_length', 0),
            output_length=data.get('output_length', 0),
            ip_address=request.remote_addr
        )
        return jsonify({'status': 'logged'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=True)