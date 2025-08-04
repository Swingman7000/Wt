"""
Database models for the Web Tools Platform
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class CrawlJob(db.Model):
    """Model for storing web crawling jobs and their configurations."""
    __tablename__ = 'crawl_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.Text, nullable=False)
    search_type = db.Column(db.String(20), nullable=False)  # 'text', 'links', 'both'
    search_words = db.Column(db.Text)  # JSON string of search words
    depth = db.Column(db.Integer, default=2)
    max_pages = db.Column(db.Integer, default=10)
    delay = db.Column(db.Float, default=1.0)
    domains = db.Column(db.Text)  # JSON string of allowed domains
    respect_robots = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'running', 'completed', 'error'
    progress = db.Column(db.Integer, default=0)
    total_pages = db.Column(db.Integer, default=0)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship to crawled pages
    pages = db.relationship('CrawledPage', backref='crawl_job', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'url': self.url,
            'search_type': self.search_type,
            'search_words': json.loads(self.search_words) if self.search_words else [],
            'depth': self.depth,
            'max_pages': self.max_pages,
            'delay': self.delay,
            'domains': json.loads(self.domains) if self.domains else [],
            'respect_robots': self.respect_robots,
            'status': self.status,
            'progress': self.progress,
            'total_pages': self.total_pages,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class CrawledPage(db.Model):
    """Model for storing individual crawled page results."""
    __tablename__ = 'crawled_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    crawl_job_id = db.Column(db.Integer, db.ForeignKey('crawl_jobs.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    content_length = db.Column(db.Integer)
    links_found = db.Column(db.Integer, default=0)
    word_matches = db.Column(db.Text)  # JSON string of word match counts
    total_word_matches = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'status_code': self.status_code,
            'content_length': self.content_length,
            'links_found': self.links_found,
            'word_matches': json.loads(self.word_matches) if self.word_matches else {},
            'total_word_matches': self.total_word_matches,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class EncryptionHistory(db.Model):
    """Model for storing encryption/decryption history (optional feature)."""
    __tablename__ = 'encryption_history'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(20), nullable=False)  # 'encrypt', 'decrypt'
    encryption_method = db.Column(db.String(20), nullable=False)  # 'base64', 'aes'
    has_password = db.Column(db.Boolean, default=False)
    input_length = db.Column(db.Integer)
    output_length = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    
    def to_dict(self):
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'encryption_method': self.encryption_method,
            'has_password': self.has_password,
            'input_length': self.input_length,
            'output_length': self.output_length,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address
        }

class ProxyRequest(db.Model):
    """Model for storing proxy request logs."""
    __tablename__ = 'proxy_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    target_url = db.Column(db.Text, nullable=False)
    remove_scripts = db.Column(db.Boolean, default=True)
    remove_cookies = db.Column(db.Boolean, default=True)
    status_code = db.Column(db.Integer)
    response_size = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'target_url': self.target_url,
            'remove_scripts': self.remove_scripts,
            'remove_cookies': self.remove_cookies,
            'status_code': self.status_code,
            'response_size': self.response_size,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

class ToolUsageStats(db.Model):
    """Model for tracking general usage statistics."""
    __tablename__ = 'tool_usage_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    tool_name = db.Column(db.String(50), nullable=False)  # 'crawler', 'encryptor', 'proxy'
    page_views = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=datetime.utcnow().date())
    
    __table_args__ = (db.UniqueConstraint('tool_name', 'date', name='unique_tool_date'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tool_name': self.tool_name,
            'page_views': self.page_views,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'date': self.date.isoformat() if self.date else None
        }