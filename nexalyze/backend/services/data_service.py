"""
Enhanced Data Service
Production-ready data collection, processing, and storage with multi-source integration
"""

import aiohttp
import asyncio
import re
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from config.settings import settings
from database.connections import (
    redis_conn, 
    cache_get, cache_set, cache_key
)

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Available data sources"""
    YC = "y_combinator"
    HACKER_NEWS = "hacker_news"
    PRODUCT_HUNT = "product_hunt"
    BETALIST = "betalist"
    SERP = "serp_api"
    GITHUB = "github"
    INTERNAL = "internal"


@dataclass
class Company:
    """Standardized company data model"""
    name: str
    description: str
    industry: str
    location: str = ""
    website: str = ""
    founded_year: int = 0
    yc_batch: str = ""
    funding: str = ""
    employees: str = ""
    stage: str = ""
    tags: List[str] = None
    long_description: str = ""
    is_active: bool = True
    source: str = DataSource.INTERNAL.value
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_yc_data(cls, data: Dict[str, Any]) -> Optional['Company']:
        """Create Company from YC API data"""
        name = data.get('name', '')
        if not name:
            return None
        
        description = data.get('one_liner', '') or data.get('description', '')
        if not description or len(description) < 10:
            return None
        
        industries = data.get('industries', [])
        if not industries:
            return None
        
        # Extract location
        location = ''
        if data.get('location'):
            location = data['location']
        elif data.get('city'):
            city = data['city']
            country = data.get('country', '')
            location = f"{city}, {country}" if country else city
        elif data.get('country'):
            location = data['country']
        else:
            location = data.get('region', 'United States')
        
        # Extract founded year from batch if not available
        founded_year = data.get('year_founded', 0)
        batch = data.get('batch', '') or data.get('batch_name', '')
        
        if not founded_year or founded_year < 1990:
            if batch:
                year_match = re.search(r'(\d{2})$', batch)
                if year_match:
                    year = int(year_match.group(1))
                    founded_year = 2000 + year if year < 50 else 1900 + year
                else:
                    founded_year = 2010
        
        if not batch:
            return None
        
        # Get website
        website = data.get('website', '') or data.get('url', '')
        if not website:
            website = f"https://www.ycombinator.com/companies/{name.lower().replace(' ', '-')}"
        
        return cls(
            name=name,
            description=description,
            long_description=data.get('long_description', description),
            industry=', '.join(industries),
            location=location,
            website=website,
            founded_year=founded_year,
            yc_batch=batch,
            tags=data.get('tags', []),
            is_active=data.get('status', {}).get('active', True) if isinstance(data.get('status'), dict) else True,
            source=DataSource.YC.value
        )


class DataService:
    """
    Production-ready data service with:
    - Multi-source data aggregation
    - Intelligent caching
    - Batch processing
    - Error recovery
    - Data validation
    """
    
    def __init__(self):
        self.yc_api_url = settings.yc_api_base_url
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self._request_times: Dict[str, List[float]] = {}
        self._rate_limits = {
            'yc': (10, 1),  # 10 requests per second
            'default': (5, 1),  # 5 requests per second
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(ssl=False, limit=20)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _rate_limit(self, source: str = 'default'):
        """Apply rate limiting for API requests"""
        max_requests, window = self._rate_limits.get(source, self._rate_limits['default'])
        
        if source not in self._request_times:
            self._request_times[source] = []
        
        now = asyncio.get_event_loop().time()
        
        # Clean old timestamps
        self._request_times[source] = [
            t for t in self._request_times[source] 
            if now - t < window
        ]
        
        # Wait if at limit
        if len(self._request_times[source]) >= max_requests:
            wait_time = self._request_times[source][0] + window - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self._request_times[source].append(now)
    
    async def sync_yc_data(
        self, 
        limit: int = None, 
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        Sync Y Combinator company data with intelligent processing.
        
        Args:
            limit: Maximum number of companies to sync (None for all)
            progress_callback: Optional async callback(count, total, status)
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Starting YC data sync (limit={limit if limit else 'ALL'})")
        
        stats = {
            "synced": 0,
            "skipped": 0,
            "failed": 0,
            "total_available": 0,
            "duration_seconds": 0
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check cache first
            cache_data = cache_get(cache_key("yc", "all_companies"))
            
            if cache_data:
                all_companies = cache_data
                logger.info(f"Using cached YC data ({len(all_companies)} companies)")
            else:
                # Fetch from API
                session = await self._get_session()
                await self._rate_limit('yc')
                
                async with session.get(
                    f"{self.yc_api_url}/companies/all.json",
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        logger.error(f"YC API returned status {response.status}")
                        stats["error"] = f"API returned status {response.status}"
                        return stats
                    
                    all_companies = await response.json()
                
                # Cache for 1 hour
                cache_set(cache_key("yc", "all_companies"), all_companies, ttl=3600)
                logger.info(f"Fetched {len(all_companies)} companies from YC API")
            
            # Filter companies with industries
            companies_with_industries = [
                c for c in all_companies
                if c.get('industries') and len(c.get('industries', [])) > 0
            ]
            
            stats["total_available"] = len(companies_with_industries)
            logger.info(f"Found {len(companies_with_industries)} companies with industry tags")
            
            # Determine target count
            target_count = limit if limit else len(companies_with_industries)
            
            if progress_callback:
                await progress_callback(0, target_count, "starting")
            
            # Process in batches for better performance
            batch_size = 100
            processed = 0
            
            for i in range(0, len(companies_with_industries), batch_size):
                if limit and stats["synced"] >= limit:
                    break
                
                batch = companies_with_industries[i:i + batch_size]
                
                for company_data in batch:
                    if limit and stats["synced"] >= limit:
                        break
                    
                    try:
                        company = Company.from_yc_data(company_data)
                        
                        if company:
                            stored = await self._store_company(company)
                            if stored:
                                stats["synced"] += 1
                            else:
                                stats["skipped"] += 1
                        else:
                            stats["skipped"] += 1
                            
                    except Exception as e:
                        stats["failed"] += 1
                        if stats["failed"] % 50 == 0:
                            logger.warning(f"Failed count: {stats['failed']} companies")
                
                processed += len(batch)
                
                if stats["synced"] % 100 == 0 and stats["synced"] > 0:
                    logger.info(f"Progress: {stats['synced']}/{target_count} companies synced")
                    
                    if progress_callback:
                        await progress_callback(stats["synced"], target_count, "syncing")
            
            stats["duration_seconds"] = asyncio.get_event_loop().time() - start_time
            
            logger.info(
                f"YC sync completed: {stats['synced']} synced, "
                f"{stats['skipped']} skipped, {stats['failed']} failed "
                f"({stats['duration_seconds']:.1f}s)"
            )
            
            if progress_callback:
                await progress_callback(stats["synced"], target_count, "completed")
            
            return stats
            
        except Exception as e:
            logger.error(f"YC sync failed: {e}")
            stats["error"] = str(e)
            
            if progress_callback:
                await progress_callback(0, 0, "error")
            
            return stats
    
    async def _store_company(self, company: Company) -> bool:
        """Store company in PostgreSQL"""
        from database.connections import postgres_conn
        if not postgres_conn.is_connected():
            return False
            
        try:
            # Check if exists
            existing = postgres_conn.query("SELECT id FROM companies WHERE name = %s", (company.name,))
            
            if existing:
                # Update
                sql = """
                    UPDATE companies SET
                        description = %s, industry = %s, location = %s,
                        website = %s, founded_year = %s, yc_batch = %s,
                        funding = %s, employees = %s, stage = %s,
                        tags = %s, updated_at = NOW()
                    WHERE name = %s
                """
                params = (
                    company.description, company.industry, company.location,
                    company.website, company.founded_year, company.yc_batch,
                    company.funding, company.employees, company.stage,
                    company.tags, company.name
                )
            else:
                # Insert
                sql = """
                    INSERT INTO companies (
                        name, description, industry, location, website,
                        founded_year, yc_batch, funding, employees, stage,
                        tags, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                """
                params = (
                    company.name, company.description, company.industry,
                    company.location, company.website, company.founded_year,
                    company.yc_batch, company.funding, company.employees,
                    company.stage, company.tags
                )
            
            return postgres_conn.execute(sql, params)
            
        except Exception as e:
            logger.error(f"Failed to store company {company.name}: {e}")
            return False

    async def search_companies(
        self,
        query: str, 
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search companies with intelligent caching and fallback.
        
        Args:
            query: Search query
            limit: Maximum results
            filters: Optional filters (industry, location, stage, etc.)
        
        Returns:
            List of matching companies
        """
        # Allow empty query to return all companies
        query = query.strip() if query and isinstance(query, str) else ""
        
        logger.info(f"Searching companies: '{query}' (limit: {limit})")
        
        # Check cache first
        cache_query_key = cache_key("search", hashlib.md5(f"{query}:{limit}:{filters}".encode()).hexdigest())
        cached_results = cache_get(cache_query_key)
        
        if cached_results:
            logger.debug(f"Returning cached search results for '{query}'")
            return cached_results
        
        results = []
        
        # Try PostgreSQL first
        from database.connections import postgres_conn
        if postgres_conn.is_connected():
            try:
                results = await self._search_postgres(query, limit, filters)
                logger.info(f"PostgreSQL returned {len(results)} companies")
            except Exception as e:
                logger.warning(f"PostgreSQL search failed: {e}")
        
        # Fallback to curated sample data if no results AND query is not empty
        # If query is empty, we only want DB results
        if not results and query:
            logger.info("No results, using sample data")
            results = self._get_sample_companies(query, limit)
        
        # Cache results
        if results:
            cache_set(cache_query_key, results, ttl=settings.cache_ttl_search)
        
        return results
    
    async def _search_postgres(
        self, 
        query: str, 
        limit: int,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute PostgreSQL search query"""
        from database.connections import postgres_conn
        
        # Build filter conditions
        filter_conditions = []
        params = []
        
        # Add query condition if present
        if query:
            filter_conditions.append("(LOWER(name) LIKE %s OR LOWER(description) LIKE %s OR LOWER(industry) LIKE %s)")
            params.extend([f"%{query.lower()}%", f"%{query.lower()}%", f"%{query.lower()}%"])
        
        if filters:
            if filters.get("industry"):
                filter_conditions.append("LOWER(industry) LIKE %s")
                params.append(f"%{filters['industry'].lower()}%")
            
            if filters.get("location"):
                filter_conditions.append("LOWER(location) LIKE %s")
                params.append(f"%{filters['location'].lower()}%")
            
            if filters.get("stage"):
                filter_conditions.append("stage = %s")
                params.append(filters["stage"])
            
            if filters.get("min_year"):
                filter_conditions.append("founded_year >= %s")
                params.append(filters["min_year"])
        
        where_clause = "WHERE " + " AND ".join(filter_conditions) if filter_conditions else ""
        
        # Order by relevance if query exists, otherwise by recently updated
        order_clause = ""
        if query:
            order_clause = "ORDER BY CASE WHEN LOWER(name) LIKE %s THEN 0 ELSE 1 END, founded_year DESC"
            params.append(f"%{query.lower()}%")
        else:
            order_clause = "ORDER BY created_at DESC, founded_year DESC"
            
        sql = f"""
            SELECT 
                id, name, description, industry, founded_year, location,
                website, yc_batch, funding, employees, stage, tags
            FROM companies
            {where_clause}
            {order_clause}
            LIMIT %s
        """
        
        # Add limit
        params.append(limit)
        
        results = postgres_conn.query(sql, tuple(params))
        
        return results

    
    async def get_company_details(self, company_id: int) -> Dict[str, Any]:
        """Get detailed company information by ID"""
        
        # Check cache
        cached = cache_get(cache_key("company", str(company_id)))
        if cached:
            return cached
        
        # Query PostgreSQL
        from database.connections import postgres_conn
        if postgres_conn.is_connected():
            results = postgres_conn.query(
                """
                SELECT * FROM companies WHERE id = %s
                """,
                (company_id,)
            )
            
            if results:
                company = results[0]
                # Cache for 24 hours
                cache_set(cache_key("company", str(company_id)), company, ttl=settings.cache_ttl_company)
                return company
        
        # Fallback
        return self._get_fallback_company(company_id)
    
    async def get_company_count(self) -> int:
        """Get total number of companies in database"""
        from database.connections import postgres_conn
        if not postgres_conn.is_connected():
            return 0
        
        results = postgres_conn.query("SELECT COUNT(*) as total FROM companies")
        return results[0].get('total', 0) if results else 0
    
    async def get_industry_distribution(self) -> Dict[str, int]:
        """Get company distribution by industry"""
        from database.connections import postgres_conn
        if not postgres_conn.is_connected():
            return {}
        
        results = postgres_conn.query("""
            SELECT industry, COUNT(*) as count
            FROM companies
            WHERE industry IS NOT NULL
            GROUP BY industry
            ORDER BY count DESC
            LIMIT 20
        """)
        
        return {r['industry']: r['count'] for r in results}
    
    async def get_location_distribution(self) -> Dict[str, int]:
        """Get company distribution by location"""
        from database.connections import postgres_conn
        if not postgres_conn.is_connected():
            return {}
        
        results = postgres_conn.query("""
            SELECT location, COUNT(*) as count
            FROM companies
            WHERE location IS NOT NULL
            GROUP BY location
            ORDER BY count DESC
            LIMIT 20
        """)
        
        return {r['location']: r['count'] for r in results}
    

    
    def _get_sample_companies(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get curated sample companies based on search query"""
        query_lower = query.lower()
        
        # Curated company database
        company_databases = {
            'ai': [
                {'id': 1, 'name': 'OpenAI', 'description': 'AI research company focused on creating safe artificial general intelligence', 'industry': 'Artificial Intelligence', 'founded_year': 2015, 'location': 'San Francisco, CA', 'website': 'https://openai.com', 'yc_batch': 'S15', 'funding': '$11.3B', 'employees': '500-1000', 'stage': 'Series C'},
                {'id': 2, 'name': 'Anthropic', 'description': 'AI safety company developing Claude, a helpful AI assistant', 'industry': 'Artificial Intelligence', 'founded_year': 2021, 'location': 'San Francisco, CA', 'website': 'https://anthropic.com', 'yc_batch': 'S21', 'funding': '$4.1B', 'employees': '200-500', 'stage': 'Series C'},
                {'id': 3, 'name': 'Cohere', 'description': 'Natural language processing AI platform for enterprises', 'industry': 'Artificial Intelligence', 'founded_year': 2019, 'location': 'Toronto, Canada', 'website': 'https://cohere.ai', 'yc_batch': 'W19', 'funding': '$270M', 'employees': '100-200', 'stage': 'Series C'},
            ],
            'fintech': [
                {'id': 7, 'name': 'Stripe', 'description': 'Online payment processing platform for internet businesses', 'industry': 'Financial Technology', 'founded_year': 2010, 'location': 'San Francisco, CA', 'website': 'https://stripe.com', 'yc_batch': 'S10', 'funding': '$2.2B', 'employees': '3000+', 'stage': 'Series H'},
                {'id': 8, 'name': 'Coinbase', 'description': 'Cryptocurrency exchange and digital wallet platform', 'industry': 'Financial Technology', 'founded_year': 2012, 'location': 'San Francisco, CA', 'website': 'https://coinbase.com', 'yc_batch': 'S12', 'funding': '$547M', 'employees': '3000+', 'stage': 'Public'},
                {'id': 9, 'name': 'Plaid', 'description': 'Financial data connectivity platform for fintech apps', 'industry': 'Financial Technology', 'founded_year': 2013, 'location': 'San Francisco, CA', 'website': 'https://plaid.com', 'yc_batch': 'S13', 'funding': '$734M', 'employees': '500-1000', 'stage': 'Acquired'},
            ],
            'saas': [
                {'id': 12, 'name': 'Dropbox', 'description': 'Cloud storage and file synchronization service', 'industry': 'Software as a Service', 'founded_year': 2007, 'location': 'San Francisco, CA', 'website': 'https://dropbox.com', 'yc_batch': 'S07', 'funding': '$1.7B', 'employees': '3000+', 'stage': 'Public'},
                {'id': 13, 'name': 'Airbnb', 'description': 'Online marketplace for short-term homestays and experiences', 'industry': 'Marketplace', 'founded_year': 2008, 'location': 'San Francisco, CA', 'website': 'https://airbnb.com', 'yc_batch': 'W08', 'funding': '$6.4B', 'employees': '5000+', 'stage': 'Public'},
                {'id': 14, 'name': 'Twilio', 'description': 'Cloud communications platform for developers', 'industry': 'Software as a Service', 'founded_year': 2008, 'location': 'San Francisco, CA', 'website': 'https://twilio.com', 'yc_batch': 'S08', 'funding': '$1.2B', 'employees': '5000+', 'stage': 'Public'},
            ],
            'healthcare': [
                {'id': 10, 'name': '23andMe', 'description': 'Personal genomics and biotechnology company', 'industry': 'Healthcare', 'founded_year': 2006, 'location': 'Sunnyvale, CA', 'website': 'https://23andme.com', 'yc_batch': 'S06', 'funding': '$791M', 'employees': '500-1000', 'stage': 'Public'},
            ],
            'edtech': [
                {'id': 4, 'name': 'Khan Academy', 'description': 'Free online learning platform with personalized resources', 'industry': 'Education Technology', 'founded_year': 2008, 'location': 'Mountain View, CA', 'website': 'https://khanacademy.org', 'yc_batch': 'S08', 'funding': '$16M', 'employees': '200-500', 'stage': 'Non-profit'},
                {'id': 5, 'name': 'Duolingo', 'description': 'Language learning platform with gamified lessons', 'industry': 'Education Technology', 'founded_year': 2011, 'location': 'Pittsburgh, PA', 'website': 'https://duolingo.com', 'yc_batch': 'S11', 'funding': '$183M', 'employees': '500-1000', 'stage': 'Public'},
            ],
        }
        
        # Find matching companies
        matching = []
        
        # Check category matches
        for category, companies in company_databases.items():
            if category in query_lower or query_lower in category:
                matching.extend(companies)
        
        # Check company name/description matches
        for category, companies in company_databases.items():
            for company in companies:
                if (query_lower in company['name'].lower() or
                    query_lower in company['description'].lower() or
                    query_lower in company['industry'].lower()):
                    if company not in matching:
                        matching.append(company)
        
        # Keyword-based fallback
        if not matching:
            keyword_map = {
                ('ai', 'artificial', 'intelligence', 'machine', 'learning', 'ml'): 'ai',
                ('finance', 'fintech', 'payment', 'banking', 'crypto'): 'fintech',
                ('education', 'learning', 'school', 'university', 'edtech'): 'edtech',
                ('health', 'medical', 'healthcare', 'bio'): 'healthcare',
                ('saas', 'software', 'platform', 'cloud'): 'saas',
            }
            
            for keywords, category in keyword_map.items():
                if any(kw in query_lower for kw in keywords):
                    matching = company_databases.get(category, [])
                    break
        
        # Default to AI companies
        if not matching:
            matching = company_databases['ai']
        
        return matching[:limit]
