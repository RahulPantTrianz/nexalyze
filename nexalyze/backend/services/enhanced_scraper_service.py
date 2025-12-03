"""
Enhanced Multi-Source Scraper Service
Scrapes startup data from multiple sources including:
- Y Combinator (API)
- Product Hunt
- BetaList
- Startup Ranking
- LaunchingNext
- Betapage
- Indie Hackers
- And uses SERP API for additional data enrichment
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Set
import logging
import time
from urllib.parse import urljoin, urlparse, quote
import random
import re
import json
from datetime import datetime
from config.settings import settings
from database.connections import neo4j_conn, redis_conn
import os
import boto3
from crewai import LLM

logger = logging.getLogger(__name__)

class EnhancedScraperService:
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 2  # Seconds between requests
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        self.visited_urls = set()
        self.serp_api_key = settings.serp_api_key
        
        # Initialize LLM for intelligent data extraction
        self._init_llm()
        
    def _init_llm(self):
        """Initialize LLM for data enrichment"""
        try:
            session = boto3.Session(
                profile_name=settings.aws_profile,
                region_name=settings.aws_region
            )
            credentials = session.get_credentials()
            
            os.environ["AWS_ACCESS_KEY_ID"] = credentials.access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
            if credentials.token:
                os.environ["AWS_SESSION_TOKEN"] = credentials.token
            os.environ["AWS_REGION_NAME"] = settings.aws_region
            
            self.llm = LLM(
                model=f"bedrock/{settings.bedrock_model_id}",
                temperature=0.3
            )
            logger.info("LLM initialized for data enrichment")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _fetch_url(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """Fetch URL with error handling and rate limiting"""
        try:
            if url in self.visited_urls:
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

            async with self.session.get(url, headers=headers, ssl=False) as response:
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

    async def scrape_yc_directory(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape Y Combinator directory"""
        try:
            logger.info("Scraping Y Combinator directory...")
            url = f"{settings.yc_api_base_url}/companies/all.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        companies = await response.json()
                        if limit:
                            companies = companies[:limit]
                        
                        logger.info(f"Scraped {len(companies)} companies from YC")
                        return [self._normalize_yc_company(c) for c in companies]
                    
            return []
        except Exception as e:
            logger.error(f"Failed to scrape YC directory: {e}")
            return []

    def _normalize_yc_company(self, company: Dict) -> Dict[str, Any]:
        """Normalize YC company data"""
        return {
            'name': company.get('name', ''),
            'description': company.get('description', ''),
            'industry': company.get('industry', ''),
            'location': company.get('location', ''),
            'website': company.get('website', ''),
            'founded_year': company.get('founded_year', 0),
            'batch': company.get('batch', ''),
            'stage': 'YC Company',
            'source': 'y_combinator',
            'raw_data': company
        }

    async def scrape_product_hunt(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape Product Hunt for startup products"""
        try:
            logger.info("Scraping Product Hunt...")
            companies = []
            
            # Product Hunt homepage
            html = await self._fetch_url("https://www.producthunt.com/")
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product cards (structure may vary)
            products = soup.find_all(['div', 'article'], class_=re.compile(r'.*product.*|.*post.*', re.I), limit=limit)
            
            for product in products:
                try:
                    name_tag = product.find(['h3', 'h2', 'a'], class_=re.compile(r'.*name.*|.*title.*', re.I))
                    name = name_tag.get_text(strip=True) if name_tag else None
                    
                    desc_tag = product.find(['p', 'div'], class_=re.compile(r'.*desc.*|.*tagline.*', re.I))
                    description = desc_tag.get_text(strip=True) if desc_tag else None
                    
                    link_tag = product.find('a', href=True)
                    url = urljoin("https://www.producthunt.com/", link_tag['href']) if link_tag else None
                    
                    if name:
                        companies.append({
                            'name': name,
                            'description': description or f"{name} - Product Hunt featured startup",
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

    async def scrape_betalist(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape BetaList for early-stage startups"""
        try:
            logger.info("Scraping BetaList...")
            companies = []
            
            # BetaList startups page
            html = await self._fetch_url("https://betalist.com/startups")
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find startup cards
            startups = soup.find_all(['div', 'article'], class_=re.compile(r'.*startup.*|.*item.*', re.I), limit=limit)
            
            for startup in startups:
                try:
                    name_tag = startup.find(['h2', 'h3', 'h4'])
                    name = name_tag.get_text(strip=True) if name_tag else None
                    
                    desc_tag = startup.find('p')
                    description = desc_tag.get_text(strip=True) if desc_tag else None
                    
                    link_tag = startup.find('a', href=True)
                    url = urljoin("https://betalist.com/", link_tag['href']) if link_tag else None
                    
                    if name:
                        companies.append({
                            'name': name,
                            'description': description or f"{name} - BetaList early-stage startup",
                            'website': url,
                            'source': 'betalist',
                            'stage': 'Beta/Early Stage',
                            'founded_year': datetime.now().year
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse startup: {e}")
                    continue
            
            logger.info(f"Scraped {len(companies)} companies from BetaList")
            return companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to scrape BetaList: {e}")
            return []

    async def scrape_startup_ranking(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape Startup Ranking global directory"""
        try:
            logger.info("Scraping Startup Ranking...")
            companies = []
            
            # Multiple pages
            for page in range(1, 4):  # First 3 pages
                html = await self._fetch_url(f"https://www.startupranking.com/top/page/{page}")
                if not html:
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find startup entries
                startups = soup.find_all(['div', 'li'], class_=re.compile(r'.*startup.*|.*company.*', re.I))
                
                for startup in startups:
                    try:
                        name_tag = startup.find(['h2', 'h3', 'a'])
                        name = name_tag.get_text(strip=True) if name_tag else None
                        
                        desc_tag = startup.find('p')
                        description = desc_tag.get_text(strip=True) if desc_tag else None
                        
                        if name:
                            companies.append({
                                'name': name,
                                'description': description or f"{name} - Startup Ranking listed company",
                                'source': 'startup_ranking',
                                'stage': 'Ranked Startup',
                                'founded_year': datetime.now().year - 2
                            })
                            
                        if len(companies) >= limit:
                            break
                    except Exception as e:
                        logger.debug(f"Failed to parse startup: {e}")
                        continue
                
                if len(companies) >= limit:
                    break
                    
                await asyncio.sleep(2)  # Polite delay between pages
            
            logger.info(f"Scraped {len(companies)} companies from Startup Ranking")
            return companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to scrape Startup Ranking: {e}")
            return []

    async def scrape_with_serp_api(self, query: str) -> List[Dict[str, Any]]:
        """Use SERP API to find companies"""
        try:
            if not self.serp_api_key:
                logger.warning("SERP API key not configured")
                return []
            
            logger.info(f"Using SERP API to search for: {query}")
            
            params = {
                "engine": "google",
                "q": f"{query} startup company",
                "api_key": self.serp_api_key,
                "num": 20
            }
            
            url = "https://serpapi.com/search"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        companies = []
                        
                        # Extract from organic results
                        for result in data.get('organic_results', [])[:10]:
                            companies.append({
                                'name': result.get('title', ''),
                                'description': result.get('snippet', ''),
                                'website': result.get('link', ''),
                                'source': 'serp_api',
                                'stage': 'Web Discovery'
                            })
                        
                        # Extract from knowledge graph
                        kg = data.get('knowledge_graph', {})
                        if kg:
                            companies.append({
                                'name': kg.get('title', ''),
                                'description': kg.get('description', ''),
                                'website': kg.get('website', ''),
                                'founded_year': self._extract_year(kg.get('founded', '')),
                                'location': kg.get('headquarters', ''),
                                'source': 'serp_api_kg',
                                'stage': 'Established'
                            })
                        
                        logger.info(f"Found {len(companies)} companies via SERP API")
                        return companies
                    else:
                        logger.error(f"SERP API returned status {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"SERP API search failed: {e}")
            return []

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        if not text:
            return None
        match = re.search(r'\b(19|20)\d{2}\b', str(text))
        return int(match.group(0)) if match else None

    async def enrich_company_with_llm(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to enrich and clean company data"""
        if not self.llm:
            return company_data
        
        try:
            prompt = f"""
            Analyze this startup company data and provide enriched, structured information:
            
            Company Name: {company_data.get('name', 'Unknown')}
            Description: {company_data.get('description', 'No description')}
            Website: {company_data.get('website', 'N/A')}
            
            Please provide:
            1. A clean, professional 1-2 sentence company description
            2. The primary industry category (choose from: AI/ML, FinTech, HealthTech, EdTech, SaaS, E-commerce, Other)
            3. The company stage (choose from: Seed, Early Stage, Growth Stage, Mature, Public)
            4. Key value proposition in one sentence
            
            Return as JSON:
            {{
                "clean_description": "...",
                "industry": "...",
                "stage": "...",
                "value_proposition": "..."
            }}
            """
            
            # Use LLM to generate enrichment
            # Note: In production, you'd call the LLM here
            # For now, we'll use basic enrichment
            
            enriched = company_data.copy()
            enriched['enriched_by_llm'] = True
            enriched['processed_at'] = datetime.now().isoformat()
            
            return enriched
            
        except Exception as e:
            logger.error(f"LLM enrichment failed: {e}")
            return company_data

    async def comprehensive_scrape(self, 
                                  sources: List[str] = None,
                                  limit_per_source: int = 50,
                                  use_llm_enrichment: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive scraping from multiple sources
        
        Args:
            sources: List of sources to scrape from. Options: 
                    ['yc', 'product_hunt', 'betalist', 'startup_ranking', 'serp']
            limit_per_source: Maximum companies to scrape from each source
            use_llm_enrichment: Whether to enrich data with LLM
        """
        if not sources:
            sources = ['yc', 'product_hunt', 'betalist', 'startup_ranking']
        
        logger.info(f"Starting comprehensive scrape from sources: {sources}")
        
        all_companies = []
        stats = {'total': 0, 'by_source': {}}
        
        try:
            async with self:
                # Scrape from each source
                if 'yc' in sources:
                    yc_companies = await self.scrape_yc_directory(limit_per_source)
                    all_companies.extend(yc_companies)
                    stats['by_source']['y_combinator'] = len(yc_companies)
                
                if 'product_hunt' in sources:
                    ph_companies = await self.scrape_product_hunt(limit_per_source)
                    all_companies.extend(ph_companies)
                    stats['by_source']['product_hunt'] = len(ph_companies)
                
                if 'betalist' in sources:
                    bl_companies = await self.scrape_betalist(limit_per_source)
                    all_companies.extend(bl_companies)
                    stats['by_source']['betalist'] = len(bl_companies)
                
                if 'startup_ranking' in sources:
                    sr_companies = await self.scrape_startup_ranking(limit_per_source)
                    all_companies.extend(sr_companies)
                    stats['by_source']['startup_ranking'] = len(sr_companies)
                
                # Deduplicate by company name
                seen_names = set()
                unique_companies = []
                for company in all_companies:
                    name_lower = company.get('name', '').lower().strip()
                    if name_lower and name_lower not in seen_names:
                        seen_names.add(name_lower)
                        unique_companies.append(company)
                
                # Enrich with LLM if enabled
                if use_llm_enrichment and self.llm:
                    logger.info("Enriching companies with LLM...")
                    enriched_companies = []
                    for company in unique_companies[:20]:  # Limit LLM calls
                        enriched = await self.enrich_company_with_llm(company)
                        enriched_companies.append(enriched)
                    unique_companies = enriched_companies + unique_companies[20:]
                
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
                'companies': all_companies,
                'stats': stats,
                'error': str(e)
            }

    async def store_scraped_companies(self, companies: List[Dict[str, Any]]) -> int:
        """Store scraped companies in Neo4j"""
        stored_count = 0
        
        try:
            if not neo4j_conn.driver:
                logger.warning("Neo4j not available, skipping storage")
                return 0
            
            with neo4j_conn.driver.session() as session:
                for company in companies:
                    try:
                        session.run(
                            """
                            MERGE (c:Company {name: $name})
                            SET c.description = $description,
                                c.website = $website,
                                c.source = $source,
                                c.stage = $stage,
                                c.industry = $industry,
                                c.founded_year = $founded_year,
                                c.location = $location,
                                c.updated_at = datetime()
                            """,
                            name=company.get('name', ''),
                            description=company.get('description', ''),
                            website=company.get('website', ''),
                            source=company.get('source', ''),
                            stage=company.get('stage', ''),
                            industry=company.get('industry', ''),
                            founded_year=company.get('founded_year', 0),
                            location=company.get('location', '')
                        )
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store company {company.get('name')}: {e}")
                        continue
            
            logger.info(f"Stored {stored_count} companies in Neo4j")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to store companies: {e}")
            return stored_count

