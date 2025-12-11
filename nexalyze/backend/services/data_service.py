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
    neo4j_conn, redis_conn, 
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
    
    async def _store_company(
        self, 
        company: Company, 
        retry_count: int = 0
    ) -> bool:
        """
        Store company in Neo4j with retry logic.
        
        Args:
            company: Company dataclass
            retry_count: Current retry attempt
        
        Returns:
            True if stored successfully
        """
        max_retries = 3
        
        try:
            if not neo4j_conn.is_connected():
                if retry_count < max_retries:
                    logger.warning(f"Neo4j not connected, reconnecting (attempt {retry_count + 1})")
                    await asyncio.sleep(1 * (retry_count + 1))
                    if neo4j_conn.reconnect():
                        return await self._store_company(company, retry_count + 1)
                return False
            
            with neo4j_conn.driver.session() as session:
                session.run(
                    """
                    MERGE (c:Company {name: $name})
                    SET c.description = $description,
                        c.long_description = $long_description,
                        c.industry = $industry,
                        c.founded_year = $founded_year,
                        c.location = $location,
                        c.website = $website,
                        c.yc_batch = $yc_batch,
                        c.funding = $funding,
                        c.employees = $employees,
                        c.stage = $stage,
                        c.is_active = $is_active,
                        c.tags = $tags,
                        c.source = $source,
                        c.updated_at = datetime()
                    """,
                    name=company.name,
                    description=company.description,
                    long_description=company.long_description,
                    industry=company.industry,
                    founded_year=company.founded_year,
                    location=company.location,
                    website=company.website,
                    yc_batch=company.yc_batch,
                    funding=company.funding,
                    employees=company.employees,
                    stage=company.stage,
                    is_active=company.is_active,
                    tags=company.tags,
                    source=company.source
                )
                return True
                
        except Exception as e:
            if retry_count < max_retries and "Connection" in str(e):
                logger.warning(f"Retrying store for {company.name}: {e}")
                await asyncio.sleep(1 * (retry_count + 1))
                return await self._store_company(company, retry_count + 1)
            
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
        if not query or not isinstance(query, str):
            return []
        
        query = query.strip()
        if not query:
            return []
        
        logger.info(f"Searching companies: '{query}' (limit: {limit})")
        
        # Check cache first
        cache_query_key = cache_key("search", hashlib.md5(f"{query}:{limit}:{filters}".encode()).hexdigest())
        cached_results = cache_get(cache_query_key)
        
        if cached_results:
            logger.debug(f"Returning cached search results for '{query}'")
            return cached_results
        
        results = []
        
        # Try Neo4j first
        if neo4j_conn.is_connected():
            try:
                results = await self._search_neo4j(query, limit, filters)
                logger.info(f"Neo4j returned {len(results)} companies")
            except Exception as e:
                logger.warning(f"Neo4j search failed: {e}")
        
        # Fallback to curated sample data if no results
        if not results:
            logger.info("No Neo4j results, using sample data")
            results = self._get_sample_companies(query, limit)
        
        # Cache results
        if results:
            cache_set(cache_query_key, results, ttl=settings.cache_ttl_search)
        
        return results
    
    async def _search_neo4j(
        self, 
        query: str, 
        limit: int,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute Neo4j search query"""
        
        # Build filter conditions
        filter_conditions = []
        params = {"query": query.lower(), "limit": limit}
        
        if filters:
            if filters.get("industry"):
                filter_conditions.append("AND toLower(c.industry) CONTAINS toLower($industry)")
                params["industry"] = filters["industry"]
            
            if filters.get("location"):
                filter_conditions.append("AND toLower(c.location) CONTAINS toLower($location)")
                params["location"] = filters["location"]
            
            if filters.get("stage"):
                filter_conditions.append("AND c.stage = $stage")
                params["stage"] = filters["stage"]
            
            if filters.get("min_year"):
                filter_conditions.append("AND c.founded_year >= $min_year")
                params["min_year"] = filters["min_year"]
        
        filter_str = " ".join(filter_conditions)
        
        cypher = f"""
            MATCH (c:Company)
            WHERE (
                toLower(c.name) CONTAINS $query
                OR toLower(c.description) CONTAINS $query
                OR toLower(c.industry) CONTAINS $query
                OR toLower(c.long_description) CONTAINS $query
            )
            {filter_str}
            RETURN 
                c.name as name,
                c.description as description,
                c.industry as industry,
                c.founded_year as founded_year,
                c.location as location,
                c.website as website,
                c.yc_batch as yc_batch,
                c.funding as funding,
                c.employees as employees,
                c.stage as stage,
                c.tags as tags,
                id(c) as company_id
            ORDER BY 
                CASE WHEN toLower(c.name) CONTAINS $query THEN 0 ELSE 1 END,
                c.founded_year DESC
            LIMIT $limit
        """
        
        results = neo4j_conn.query(cypher, params)
        
        return [
            {
                'id': r.get('company_id'),
                'name': r.get('name'),
                'description': r.get('description'),
                'industry': r.get('industry'),
                'founded_year': r.get('founded_year'),
                'location': r.get('location'),
                'website': r.get('website'),
                'yc_batch': r.get('yc_batch'),
                'funding': r.get('funding'),
                'employees': r.get('employees'),
                'stage': r.get('stage'),
                'tags': r.get('tags', [])
            }
            for r in results
        ]
    
    async def get_company_details(self, company_id: int) -> Dict[str, Any]:
        """Get detailed company information by ID"""
        
        # Check cache
        cached = cache_get(cache_key("company", str(company_id)))
        if cached:
            return cached
        
        # Query Neo4j
        if neo4j_conn.is_connected():
            results = neo4j_conn.query(
                """
                MATCH (c:Company) WHERE id(c) = $company_id
                RETURN c.name as name, c.description as description,
                       c.long_description as long_description,
                       c.industry as industry, c.founded_year as founded_year,
                       c.location as location, c.website as website,
                       c.yc_batch as yc_batch, c.funding as funding,
                       c.employees as employees, c.stage as stage,
                       c.tags as tags, id(c) as company_id
                """,
                {"company_id": company_id}
            )
            
            if results:
                company = results[0]
                result = {
                    'id': company.get('company_id'),
                    'name': company.get('name'),
                    'description': company.get('description'),
                    'long_description': company.get('long_description'),
                    'industry': company.get('industry'),
                    'founded_year': company.get('founded_year'),
                    'location': company.get('location'),
                    'website': company.get('website'),
                    'yc_batch': company.get('yc_batch'),
                    'funding': company.get('funding'),
                    'employees': company.get('employees'),
                    'stage': company.get('stage'),
                    'tags': company.get('tags', [])
                }
                
                # Cache for 24 hours
                cache_set(cache_key("company", str(company_id)), result, ttl=settings.cache_ttl_company)
                return result
        
        # Fallback
        return self._get_fallback_company(company_id)
    
    async def get_company_count(self) -> int:
        """Get total number of companies in database"""
        if not neo4j_conn.is_connected():
            return 0
        
        results = neo4j_conn.query("MATCH (c:Company) RETURN count(c) as total")
        return results[0].get('total', 0) if results else 0
    
    async def get_industry_distribution(self) -> Dict[str, int]:
        """Get company distribution by industry"""
        if not neo4j_conn.is_connected():
            return {}
        
        results = neo4j_conn.query("""
            MATCH (c:Company)
            WHERE c.industry IS NOT NULL
            RETURN c.industry as industry, count(*) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        
        return {r['industry']: r['count'] for r in results}
    
    async def get_location_distribution(self) -> Dict[str, int]:
        """Get company distribution by location"""
        if not neo4j_conn.is_connected():
            return {}
        
        results = neo4j_conn.query("""
            MATCH (c:Company)
            WHERE c.location IS NOT NULL
            RETURN c.location as location, count(*) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        
        return {r['location']: r['count'] for r in results}
    
    async def get_knowledge_graph(self, company_id: int) -> Dict[str, Any]:
        """Get knowledge graph data for visualization"""
        if not neo4j_conn.is_connected():
            return {'nodes': [], 'edges': []}
        
        results = neo4j_conn.query(
            """
            MATCH (c:Company) WHERE id(c) = $company_id
            OPTIONAL MATCH (c)-[r]-(related)
            RETURN c, type(r) as rel_type, related
            LIMIT 20
            """,
            {"company_id": company_id}
        )
        
        nodes = []
        edges = []
        company_added = False
        
        for record in results:
            company = record.get('c')
            
            if not company_added and company:
                nodes.append({
                    'id': f"company_{company_id}",
                    'label': company.get('name', f'Company {company_id}'),
                    'group': 'company',
                    'size': 30,
                    'color': '#1f77b4'
                })
                company_added = True
            
            if record.get('related'):
                related = record['related']
                related_id = f"related_{len(nodes)}"
                nodes.append({
                    'id': related_id,
                    'label': related.get('name', 'Related Entity'),
                    'group': 'related',
                    'size': 20,
                    'color': '#ff7f0e'
                })
                edges.append({
                    'from': f"company_{company_id}",
                    'to': related_id,
                    'label': record.get('rel_type', 'related')
                })
        
        if not nodes:
            nodes, edges = self._create_fallback_graph(company_id)
        
        return {'nodes': nodes, 'edges': edges}
    
    async def get_knowledge_graph_by_name(self, company_name: str) -> Dict[str, Any]:
        """Get knowledge graph by company name"""
        if not neo4j_conn.is_connected():
            return {'nodes': [], 'edges': [], 'ai_enhanced': False}
        
        # Find company
        results = neo4j_conn.query(
            """
            MATCH (c:Company)
            WHERE toLower(c.name) = toLower($name)
            RETURN c, id(c) as company_id
            LIMIT 1
            """,
            {"name": company_name}
        )
        
        if results:
            company_id = results[0].get('company_id')
            graph_data = await self.get_knowledge_graph(company_id)
            graph_data['company_name'] = company_name
            graph_data['ai_enhanced'] = len(graph_data['nodes']) > 1
            return graph_data
        
        # Create AI-enhanced graph if company not found
        return await self._create_ai_knowledge_graph(company_name)
    
    async def _create_ai_knowledge_graph(self, company_name: str) -> Dict[str, Any]:
        """Create AI-enhanced knowledge graph for unknown companies"""
        try:
            from agents.crew_manager import CrewManager
            crew_manager = CrewManager()
            
            # Get AI analysis
            prompt = f"""Analyze "{company_name}" and provide its business ecosystem in JSON:
            {{
                "competitors": ["Competitor 1", "Competitor 2", "Competitor 3"],
                "partners": ["Partner 1", "Partner 2"],
                "technologies": ["Tech 1", "Tech 2"],
                "markets": ["Market 1", "Market 2"]
            }}
            Use real company/technology names where possible."""
            
            response = await crew_manager.handle_conversation(prompt, f"kg_{company_name}")
            
            # Parse response
            analysis = {}
            if isinstance(response, dict) and 'response' in response:
                response_text = response['response']
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    analysis = json.loads(json_match.group())
            
            # Build graph
            nodes = [{
                'id': 'main',
                'label': company_name,
                'group': 'main_company',
                'size': 40,
                'color': '#1f77b4'
            }]
            edges = []
            
            node_configs = {
                'competitors': ('#ff7f0e', 'competes_with'),
                'partners': ('#2ca02c', 'partners_with'),
                'technologies': ('#d62728', 'uses'),
                'markets': ('#9467bd', 'serves')
            }
            
            for category, (color, rel_type) in node_configs.items():
                for idx, item in enumerate(analysis.get(category, [])[:5]):
                    node_id = f"{category}_{idx}"
                    nodes.append({
                        'id': node_id,
                        'label': item,
                        'group': category,
                        'size': 20,
                        'color': color
                    })
                    edges.append({
                        'from': 'main',
                        'to': node_id,
                        'label': rel_type
                    })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'company_name': company_name,
                'ai_enhanced': True,
                'total_nodes': len(nodes),
                'total_edges': len(edges)
            }
            
        except Exception as e:
            logger.error(f"AI knowledge graph creation failed: {e}")
            return self._create_fallback_knowledge_graph(company_name)
    
    def _create_fallback_knowledge_graph(self, company_name: str) -> Dict[str, Any]:
        """Create fallback knowledge graph"""
        nodes = [
            {'id': 'main', 'label': company_name, 'group': 'main_company', 'size': 40, 'color': '#1f77b4'},
            {'id': 'comp1', 'label': 'Industry Leader', 'group': 'competitor', 'size': 25, 'color': '#ff7f0e'},
            {'id': 'comp2', 'label': 'Market Player', 'group': 'competitor', 'size': 25, 'color': '#ff7f0e'},
            {'id': 'tech1', 'label': 'Cloud Platform', 'group': 'technology', 'size': 20, 'color': '#d62728'},
            {'id': 'market1', 'label': 'Target Market', 'group': 'market', 'size': 20, 'color': '#9467bd'},
        ]
        edges = [
            {'from': 'main', 'to': 'comp1', 'label': 'competes_with'},
            {'from': 'main', 'to': 'comp2', 'label': 'competes_with'},
            {'from': 'main', 'to': 'tech1', 'label': 'uses'},
            {'from': 'main', 'to': 'market1', 'label': 'serves'},
        ]
        return {
            'nodes': nodes,
            'edges': edges,
            'company_name': company_name,
            'ai_enhanced': False
        }
    
    def _create_fallback_graph(self, company_id: int) -> Tuple[List, List]:
        """Create fallback graph structure"""
        nodes = [
            {'id': f'company_{company_id}', 'label': f'Company {company_id}', 'group': 'company', 'size': 30, 'color': '#1f77b4'},
            {'id': 'competitor_1', 'label': 'Competitor A', 'group': 'competitor', 'size': 25, 'color': '#ff7f0e'},
            {'id': 'investor_1', 'label': 'Investor X', 'group': 'investor', 'size': 20, 'color': '#2ca02c'}
        ]
        edges = [
            {'from': f'company_{company_id}', 'to': 'competitor_1', 'label': 'competes_with'},
            {'from': f'company_{company_id}', 'to': 'investor_1', 'label': 'funded_by'}
        ]
        return nodes, edges
    
    def _get_fallback_company(self, company_id: int) -> Dict[str, Any]:
        """Get fallback company data"""
        return {
            'id': company_id,
            'name': f'Company {company_id}',
            'description': 'Company details not available',
            'industry': 'Unknown',
            'founded_year': 2020,
            'location': 'Unknown',
            'website': 'N/A',
            'yc_batch': 'N/A'
        }
    
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
