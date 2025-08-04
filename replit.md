# Web Tools Platform

## Overview

This is a comprehensive web tools platform featuring three powerful utilities: a web crawler, HTML text encryptor, and web proxy. Built with Flask and designed for ease of use, each tool serves different purposes for web development, security, and accessibility needs.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The platform is built as a Flask web application with three distinct tools:

- **Web Application Framework**: Flask-based web interface with Bootstrap styling
- **Web Crawler**: Systematic website analysis with word search and link extraction
- **HTML Text Encryptor**: Secure text encryption/decryption with Base64 and AES options
- **Web Proxy**: Anonymous browsing tool with content filtering and security features

## Key Components

### 1. Web Crawler (`crawler.html`, `crawler.py`)
**Blue-themed interface** for systematic website analysis:
- URL normalization and validation
- Robots.txt compliance checking
- Breadth-first crawling with depth control
- Word search functionality across pages
- Link extraction and counting
- CSV export of results
- Real-time progress tracking

### 2. HTML Text Encryptor (`encryptor.html`)
**Green-themed interface** for secure text processing:
- Single input/output box design with encrypt/decrypt buttons
- Base64 encoding for basic obfuscation
- AES encryption with password protection
- Password visibility toggle
- Smart detection of encryption type
- Auto-save functionality

### 3. Web Proxy (`proxy.html`)
**Purple-themed interface** for anonymous browsing:
- Anonymous web browsing through proxy server
- JavaScript filtering for security
- Cookie blocking capabilities
- URL rewriting for relative links
- Navigation controls (back/forward/refresh)
- Content filtering options

## Color Theming

Each tool has distinct visual theming for better user experience:
- **Web Crawler**: Blue theme (#007bff) - Professional analysis tool
- **HTML Encryptor**: Green theme (#28a745) - Security and encryption
- **Web Proxy**: Purple theme (#6f42c1) - Anonymity and privacy

## External Dependencies

### Core Libraries:
- **Flask**: Web framework for the application
- **requests**: HTTP client for proxy and crawling
- **BeautifulSoup4**: HTML parsing and link extraction
- **trafilatura**: Content extraction from web pages

### Frontend Libraries:
- **Bootstrap 5**: UI framework and styling
- **FontAwesome 6**: Icons and visual elements
- **CryptoJS**: Client-side encryption for the encryptor tool

### Python Standard Library:
- **threading**: Background crawling operations
- **csv**: Data export functionality
- **urllib**: URL parsing and validation
- **re**: Regular expressions for content filtering

## Recent Changes

**July 21, 2025:**
- Added PostgreSQL database integration with comprehensive data models
- Created usage statistics tracking for all tools and activities
- Built statistics dashboard with charts and analytics
- Added database logging for crawl jobs, encryption activities, and proxy requests
- Implemented real-time activity monitoring and historical data storage
- Added third tool: Web Proxy with purple theming and anonymous browsing capabilities
- Removed "About these tools" section from homepage as requested  
- Implemented color theming for each tool page (blue/green/purple)
- Updated homepage layout to 3-column grid for all three tools
- Added proxy API endpoint with content filtering and URL rewriting

**Previous:**
- Created Flask web application with Bootstrap interface
- Implemented web crawler with real-time progress tracking
- Built HTML encryptor with single input/output design and password toggle
- Added CSV export functionality and results display

## Database Architecture

The platform now uses PostgreSQL for persistent data storage:

### Data Models:
- **CrawlJob**: Stores crawling configurations and status
- **CrawledPage**: Individual page results from crawl jobs
- **EncryptionHistory**: Logs all encryption/decryption activities
- **ProxyRequest**: Tracks proxy usage and performance
- **ToolUsageStats**: Daily usage statistics for each tool

### Features:
- Real-time activity logging
- Historical data retention
- Usage analytics and reporting
- Performance monitoring

## Deployment Strategy

This is a Flask web application designed to run on Replit:

- **Web Interface**: Accessible through browser on port 5000
- **Database**: PostgreSQL for persistent data storage
- **File-based Exports**: Results can be downloaded as CSV files
- **Responsive Design**: Works on desktop and mobile devices
- **Statistics Dashboard**: Real-time analytics and usage tracking

### Usage Pattern:
1. Navigate to the homepage to choose a tool
2. Each tool has its own dedicated page with themed interface
3. Results are displayed in real-time with export options

The platform provides three distinct utilities while maintaining consistent navigation and professional design throughout.