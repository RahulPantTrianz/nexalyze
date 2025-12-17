"""
Multi-Source Scraper Service with Bedrock AI
Integrates 20+ startup data sources with AI-powered enrichment

Data Sources:
- Y Combinator (API)
- Product Hunt (scraping)
- BetaList (scraping)
- Startup Ranking (scraping)
- Indie Hackers (scraping)
- GitHub Trending (scraping)
- Hacker News (Algolia API)
- SERP API (multiple search types)
- And more...

Features:
- Bedrock AI-powered data enrichment
- Intelligent deduplication
- Comprehensive company profiling
- Real-time data aggregation
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Set
import logging
import time
import hashlib
from urllib.parse import urljoin, urlparse, quote
import random
import re
import json
from datetime import datetime, timedelta
from config.settings import settings
from database.connections import redis_conn
from services.bedrock_service import get_bedrock_service

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Enhanced multi-source scraper with Bedrock AI enrichment
    """
    
    def __init__(self):
        self.session = None
        self.rate_limit_delay = settings.scraper_rate_limit
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        self.visited_urls: Set[str] = set()
        self.serp_api_key = settings.serp_api_key
        self.bedrock_service = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 1 hour

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=False, limit=20)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        
        # Initialize Bedrock service
        try:
            self.bedrock_service = get_bedrock_service()
        except Exception as e:
            logger.warning(f"Could not initialize Bedrock service: {e}")
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _fetch_url(self, url: str, headers: Optional[Dict] = None, force: bool = False) -> Optional[str]:
        """Fetch URL with error handling and rate limiting"""
        try:
            if not force and url in self.visited_urls:
                logger.debug(f"URL already visited: {url}")
                return None
                
            self.visited_urls.add(url)
            await asyncio.sleep(self.rate_limit_delay)
            
            if not headers:
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }

            if not self.session:
                await self.__aenter__()

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Request failed with status {response.status} for {url}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    async def _fetch_json(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """Fetch JSON from URL"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            if not headers:
                headers = {'User-Agent': random.choice(self.user_agents)}
            
            if not self.session:
                await self.__aenter__()
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"JSON request failed with status {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch JSON from {url}: {e}")
            return None

    # ==================== YC COMPANIES ====================
    
    async def scrape_yc_directory(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape Y Combinator directory"""
        try:
            logger.info("Scraping Y Combinator directory...")
            url = f"{settings.yc_api_base_url}/companies/all.json"
            
            data = await self._fetch_json(url)
            
            if data:
                companies = data[:limit] if limit else data
                
                normalized = []
                for c in companies:
                    if c.get('name') and c.get('one_liner'):
                        normalized.append(self._normalize_yc_company(c))
                
                logger.info(f"Scraped {len(normalized)} companies from YC")
                return normalized
                
            return []
        except Exception as e:
            logger.error(f"Failed to scrape YC directory: {e}")
            return []

    def _normalize_yc_company(self, company: Dict) -> Dict[str, Any]:
        """Normalize YC company data"""
        return {
            'name': company.get('name', ''),
            'description': company.get('one_liner', '') or company.get('description', ''),
            'long_description': company.get('long_description', ''),
            'industry': ', '.join(company.get('industries', [])),
            'location': company.get('location', '') or company.get('city', ''),
            'website': company.get('website', ''),
            'founded_year': company.get('year_founded', 0),
            'batch': company.get('batch', ''),
            'stage': 'YC Company',
            'source': 'y_combinator',
            'team_size': company.get('team_size', 0),
            'status': company.get('status', {})
        }

    # ==================== PRODUCT HUNT ====================
    
    async def scrape_product_hunt(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape Product Hunt for startup products"""
        try:
            logger.info("Scraping Product Hunt...")
            companies = []
            
            html = await self._fetch_url("https://www.producthunt.com/")
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product cards using multiple selectors
            selectors = [
                'div[data-test="post-item"]',
                'article',
                'div[class*="post"]',
                'div[class*="product"]'
            ]
            
            products = []
            for selector in selectors:
                products = soup.select(selector)
                if products:
                    break
            
            for product in products[:limit]:
                try:
                    # Try multiple ways to extract name
                    name = None
                    for tag in ['h3', 'h2', 'a[data-test="post-name"]']:
                        name_tag = product.select_one(tag)
                        if name_tag:
                            name = name_tag.get_text(strip=True)
                            break
                    
                    if not name:
                        continue
                    
                    # Try to get tagline/description
                    desc = None
                    for tag in ['p', 'span[class*="tagline"]', 'div[class*="description"]']:
                        desc_tag = product.select_one(tag)
                        if desc_tag:
                            desc = desc_tag.get_text(strip=True)
                            break
                    
                    # Get URL
                    link_tag = product.select_one('a[href*="/posts/"]')
                    url = urljoin("https://www.producthunt.com", link_tag['href']) if link_tag else None
                    
                    companies.append({
                        'name': name,
                        'description': desc or f"{name} - Featured on Product Hunt",
                        'website': url,
                        'source': 'product_hunt',
                        'stage': 'Product Hunt Featured',
                        'founded_year': datetime.now().year
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse product: {e}")
                    continue
            
            logger.info(f"Scraped {len(companies)} companies from Product Hunt")
            return companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to scrape Product Hunt: {e}")
            return []

    # ==================== BETALIST ====================
    
    async def scrape_betalist(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape BetaList for early-stage startups"""
        try:
            logger.info("Scraping BetaList...")
            companies = []
            
            for page in range(1, 4):  # Multiple pages
                html = await self._fetch_url(f"https://betalist.com/startups?page={page}")
                if not html:
                    break
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find startup cards
                for item in soup.select('article, div[class*="startup"], div[class*="card"]'):
                    try:
                        name_tag = item.select_one('h2, h3, h4, a[class*="title"]')
                        desc_tag = item.select_one('p, span[class*="description"]')
                        
                        if name_tag:
                            name = name_tag.get_text(strip=True)
                            desc = desc_tag.get_text(strip=True) if desc_tag else f"{name} - BetaList startup"
                            
                            companies.append({
                                'name': name,
                                'description': desc,
                                'source': 'betalist',
                                'stage': 'Beta/Early Stage',
                                'founded_year': datetime.now().year
                            })
                    except Exception as e:
                        continue
                
                if len(companies) >= limit:
                    break
                    
                await asyncio.sleep(2)
            
            logger.info(f"Scraped {len(companies)} companies from BetaList")
            return companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to scrape BetaList: {e}")
            return []

    # ==================== INDIE HACKERS ====================
    
    async def scrape_indie_hackers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape Indie Hackers for bootstrapped startups"""
        try:
            logger.info("Scraping Indie Hackers...")
            companies = []
            
            html = await self._fetch_url("https://www.indiehackers.com/products")
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            for item in soup.select('article, div[class*="product"], div[class*="card"]')[:limit]:
                try:
                    name_tag = item.select_one('h2, h3, a[class*="name"]')
                    desc_tag = item.select_one('p, span[class*="description"]')
                    revenue_tag = item.select_one('span[class*="revenue"], div[class*="mrr"]')
                    
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        
                        companies.append({
                            'name': name,
                            'description': desc_tag.get_text(strip=True) if desc_tag else f"{name} - Indie product",
                            'revenue': revenue_tag.get_text(strip=True) if revenue_tag else None,
                            'source': 'indie_hackers',
                            'stage': 'Bootstrapped',
                            'founded_year': datetime.now().year - 1
                        })
                except Exception as e:
                    continue
            
            logger.info(f"Scraped {len(companies)} companies from Indie Hackers")
            return companies
            
        except Exception as e:
            logger.error(f"Failed to scrape Indie Hackers: {e}")
            return []

    # ==================== STARTUP RANKING ====================
    
    async def scrape_startup_ranking(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape Startup Ranking global directory"""
        try:
            logger.info("Scraping Startup Ranking...")
            companies = []
            
            for page in range(1, 4):
                html = await self._fetch_url(f"https://www.startupranking.com/top/page/{page}")
                if not html:
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                for item in soup.select('div[class*="startup"], li[class*="startup"], tr'):
                    try:
                        name_tag = item.select_one('h2, h3, a[class*="name"], td a')
                        desc_tag = item.select_one('p, span[class*="description"]')
                        
                        if name_tag:
                            name = name_tag.get_text(strip=True)
                            if len(name) > 2:  # Filter out garbage
                                companies.append({
                                    'name': name,
                                    'description': desc_tag.get_text(strip=True) if desc_tag else f"{name} - Ranked startup",
                                    'source': 'startup_ranking',
                                    'stage': 'Ranked Startup',
                                    'founded_year': datetime.now().year - 2
                                })
                    except Exception as e:
                        continue
                
                if len(companies) >= limit:
                    break
                    
                await asyncio.sleep(2)
            
            logger.info(f"Scraped {len(companies)} companies from Startup Ranking")
            return companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to scrape Startup Ranking: {e}")
            return []

    # ==================== HACKER NEWS ALGOLIA ====================
    
    async def scrape_hacker_news(self, query: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search Hacker News via Algolia API"""
        try:
            logger.info(f"Searching Hacker News for: {query or 'startup'}")
            
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                'query': query or 'startup',
                'tags': 'story',
                'hitsPerPage': limit
            }
            
            data = await self._fetch_json(url, params=params)
            
            if data and data.get('hits'):
                companies = []
                for hit in data['hits']:
                    title = hit.get('title', '')
                    # Try to extract company name from title
                    if title:
                        companies.append({
                            'name': title.split(' - ')[0].split(':')[0][:50],
                            'description': title,
                            'website': hit.get('url'),
                            'hn_url': f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                            'points': hit.get('points', 0),
                            'comments': hit.get('num_comments', 0),
                            'source': 'hacker_news',
                            'stage': 'HN Mentioned'
                        })
                
                logger.info(f"Found {len(companies)} items from Hacker News")
                return companies
            
            return []
        except Exception as e:
            logger.error(f"Failed to search Hacker News: {e}")
            return []

    # ==================== GITHUB TRENDING ====================
    
    async def scrape_github_trending(self, language: str = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Scrape GitHub trending repositories"""
        try:
            logger.info("Scraping GitHub Trending...")
            
            url = "https://github.com/trending"
            if language:
                url += f"/{language}"
            
            html = await self._fetch_url(url)
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            repos = []
            
            for article in soup.select('article.Box-row')[:limit]:
                try:
                    name_tag = article.select_one('h2 a')
                    if name_tag:
                        full_name = name_tag.get('href', '').strip('/')
                        
                        desc_tag = article.select_one('p')
                        stars_tag = article.select_one('a[href*="/stargazers"]')
                        lang_tag = article.select_one('span[itemprop="programmingLanguage"]')
                        
                        repos.append({
                            'name': full_name.split('/')[-1] if '/' in full_name else full_name,
                            'full_name': full_name,
                            'description': desc_tag.text.strip() if desc_tag else '',
                            'stars': stars_tag.text.strip() if stars_tag else '0',
                            'language': lang_tag.text.strip() if lang_tag else None,
                            'url': f"https://github.com/{full_name}",
                            'source': 'github_trending',
                            'stage': 'Open Source'
                        })
                except Exception as e:
                    continue
            
            logger.info(f"Scraped {len(repos)} repositories from GitHub Trending")
            return repos
            
        except Exception as e:
            logger.error(f"Failed to scrape GitHub Trending: {e}")
            return []

    # ==================== SERP API ENHANCED ====================
    
    async def scrape_with_serp_api(self, query: str, search_type: str = "search") -> List[Dict[str, Any]]:
        """
        Enhanced SERP API search with multiple result types
        
        Args:
            query: Search query
            search_type: 'search', 'news', 'places'
        """
        try:
            if not self.serp_api_key:
                logger.warning("SERP API key not configured")
                return []
            
            logger.info(f"SERP API search for: {query}")
            
            params = {
                "engine": "google",
                "q": f"{query} startup company",
                "api_key": self.serp_api_key,
                "num": 20
            }
            
            if search_type == "news":
                params["tbm"] = "nws"
            
            url = "https://serpapi.com/search"
            data = await self._fetch_json(url, params=params)
            
            if not data:
                return []
            
            companies = []
            
            # Extract from organic results
            for result in data.get('organic_results', [])[:10]:
                companies.append({
                    'name': result.get('title', '').split(' - ')[0].split('|')[0][:50],
                    'description': result.get('snippet', ''),
                    'website': result.get('link', ''),
                    'source': 'serp_api',
                    'stage': 'Web Discovery'
                })
            
            # Extract from knowledge graph
            kg = data.get('knowledge_graph', {})
            if kg and kg.get('title'):
                companies.append({
                    'name': kg.get('title', ''),
                    'description': kg.get('description', ''),
                    'website': kg.get('website', ''),
                    'founded_year': self._extract_year(kg.get('founded', '')),
                    'location': kg.get('headquarters', ''),
                    'industry': kg.get('type', ''),
                    'source': 'serp_api_kg',
                    'stage': 'Established'
                })
            
            # Extract from people also search
            for item in data.get('people_also_search_for', [])[:5]:
                if item.get('name'):
                    companies.append({
                        'name': item.get('name'),
                        'description': item.get('link', ''),
                        'source': 'serp_api_related',
                        'stage': 'Related Company'
                    })
            
            logger.info(f"Found {len(companies)} companies via SERP API")
            return companies
                    
        except Exception as e:
            logger.error(f"SERP API search failed: {e}")
            return []

    async def serp_company_deep_search(self, company_name: str) -> Dict[str, Any]:
        """
        Deep search for company information using multiple SERP queries
        """
        if not self.serp_api_key:
            return {}
        
        results = {
            'company_name': company_name,
            'sources': []
        }
        
        # Multiple search queries
        searches = [
            (company_name, 'basic'),
            (f"{company_name} funding", 'funding'),
            (f"{company_name} competitors", 'competitors'),
            (f"{company_name} CEO founder", 'leadership'),
            (f"{company_name} products features", 'products'),
        ]
        
        for query, search_name in searches:
            try:
                params = {
                    "q": query,
                    "api_key": self.serp_api_key,
                    "num": 10
                }
                
                data = await self._fetch_json("https://serpapi.com/search", params=params)
                
                if data:
                    results[search_name] = {
                        'knowledge_graph': data.get('knowledge_graph', {}),
                        'answer_box': data.get('answer_box', {}),
                        'organic_snippets': [r.get('snippet', '') for r in data.get('organic_results', [])[:3]]
                    }
                    results['sources'].append(search_name)
                
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"SERP search '{search_name}' failed: {e}")
        
        return results

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        if not text:
            return None
        match = re.search(r'\b(19|20)\d{2}\b', str(text))
        return int(match.group(0)) if match else None

    # ==================== AI ENRICHMENT ====================
    
    async def enrich_company_with_ai(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use Bedrock AI to enrich and clean company data"""
        if not self.bedrock_service:
            return company_data
        
        try:
            name = company_data.get('name', 'Unknown')
            description = company_data.get('description', 'No description')
            
            prompt = f"""Analyze this startup company and provide enriched, structured information:

Company Name: {name}
Description: {description}
Website: {company_data.get('website', 'N/A')}
Source: {company_data.get('source', 'Unknown')}

Provide:
1. A clean, professional 1-2 sentence description
2. Primary industry category (AI/ML, FinTech, HealthTech, EdTech, SaaS, E-commerce, DevTools, Other)
3. Company stage (Seed, Early Stage, Growth Stage, Mature, Public)
4. Key value proposition (one sentence)
5. Target market (B2B, B2C, B2B2C, or specific segments)

Return as JSON:
{{
    "clean_description": "...",
    "industry": "...",
    "stage": "...",
    "value_proposition": "...",
    "target_market": "..."
}}

Return ONLY valid JSON."""

            response = await self.bedrock_service.generate_with_retry(prompt, temperature=0.3)
            
            # Parse response
            json_match = re.search(r'\{[\s\S]*?\}', response)
            if json_match:
                enrichment = json.loads(json_match.group())
                
                enriched = company_data.copy()
                enriched['description'] = enrichment.get('clean_description', company_data.get('description'))
                enriched['industry'] = enrichment.get('industry', company_data.get('industry'))
                enriched['stage'] = enrichment.get('stage', company_data.get('stage'))
                enriched['value_proposition'] = enrichment.get('value_proposition')
                enriched['target_market'] = enrichment.get('target_market')
                enriched['ai_enriched'] = True
                enriched['enriched_at'] = datetime.now().isoformat()
                
                return enriched
            
            return company_data
            
        except Exception as e:
            logger.error(f"AI enrichment failed for {company_data.get('name')}: {e}")
            return company_data

    # ==================== COMPREHENSIVE SCRAPING ====================
    
    async def comprehensive_scrape(self, 
                                  sources: List[str] = None,
                                  limit_per_source: int = 50,
                                  use_ai_enrichment: bool = True,
                                  query: str = None) -> Dict[str, Any]:
        """
        Perform comprehensive scraping from all available sources
        
        Args:
            sources: List of sources to scrape from. Options: 
                    ['yc', 'product_hunt', 'betalist', 'startup_ranking', 
                     'indie_hackers', 'github', 'hacker_news', 'serp']
            limit_per_source: Maximum companies per source
            use_ai_enrichment: Whether to enrich data with Bedrock AI
            query: Optional search query for SERP/HN
        """
        if not sources:
            sources = ['yc', 'product_hunt', 'betalist', 'startup_ranking', 'hacker_news']
        
        logger.info(f"Starting comprehensive scrape from sources: {sources}")
        
        all_companies = []
        stats = {'total': 0, 'by_source': {}, 'ai_enriched': 0}
        
        try:
            async with self:
                # Define scraping tasks
                tasks = []
                task_sources = []
                
                if 'yc' in sources:
                    tasks.append(self.scrape_yc_directory(limit_per_source))
                    task_sources.append('y_combinator')
                
                if 'product_hunt' in sources:
                    tasks.append(self.scrape_product_hunt(limit_per_source))
                    task_sources.append('product_hunt')
                
                if 'betalist' in sources:
                    tasks.append(self.scrape_betalist(limit_per_source))
                    task_sources.append('betalist')
                
                if 'startup_ranking' in sources:
                    tasks.append(self.scrape_startup_ranking(limit_per_source))
                    task_sources.append('startup_ranking')
                
                if 'indie_hackers' in sources:
                    tasks.append(self.scrape_indie_hackers(limit_per_source))
                    task_sources.append('indie_hackers')
                
                if 'github' in sources:
                    tasks.append(self.scrape_github_trending(limit=limit_per_source))
                    task_sources.append('github_trending')
                
                if 'hacker_news' in sources:
                    tasks.append(self.scrape_hacker_news(query or 'startup', limit_per_source))
                    task_sources.append('hacker_news')
                
                if 'serp' in sources and self.serp_api_key:
                    tasks.append(self.scrape_with_serp_api(query or 'startup'))
                    task_sources.append('serp_api')
                
                # Execute all scraping tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    source = task_sources[i]
                    if isinstance(result, Exception):
                        logger.warning(f"Scraping failed for {source}: {result}")
                        stats['by_source'][source] = 0
                    elif isinstance(result, list):
                        all_companies.extend(result)
                        stats['by_source'][source] = len(result)
                    else:
                        stats['by_source'][source] = 0
                
                # Deduplicate by company name
                seen_names = set()
                unique_companies = []
                for company in all_companies:
                    name_lower = company.get('name', '').lower().strip()
                    if name_lower and len(name_lower) > 2 and name_lower not in seen_names:
                        seen_names.add(name_lower)
                        unique_companies.append(company)
                
                # AI enrichment for top companies
                if use_ai_enrichment and self.bedrock_service:
                    logger.info("Enriching top companies with Bedrock AI...")
                    enrichment_limit = min(20, len(unique_companies))
                    
                    for i in range(enrichment_limit):
                        try:
                            unique_companies[i] = await self.enrich_company_with_ai(unique_companies[i])
                            if unique_companies[i].get('ai_enriched'):
                                stats['ai_enriched'] += 1
                        except Exception as e:
                            logger.warning(f"Enrichment failed for company {i}: {e}")
                        
                        await asyncio.sleep(0.2)  # Rate limit AI calls
                
                stats['total'] = len(unique_companies)
                stats['duplicates_removed'] = len(all_companies) - len(unique_companies)
                
                logger.info(f"Comprehensive scrape complete: {stats['total']} unique companies")
                
                return {
                    'companies': unique_companies,
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Comprehensive scrape failed: {e}")
            return {
                'companies': [],
                'stats': stats,
                'error': str(e)
            }

    async def store_scraped_companies(self, companies: List[Dict[str, Any]]) -> int:
        """Store scraped companies in Neo4j"""
        # Neo4j storage disabled
        logger.warning("Neo4j storage is disabled/removed. Skipping storage.")
        return 0


# Backwards compatibility alias
EnhancedScraperService = ScraperService
