import aiohttp
import asyncio
from typing import List, Dict, Any
import json
import logging
from config.settings import settings
from database.connections import neo4j_conn, postgres_conn, redis_conn
from services.hacker_news_service import HackerNewsService
import requests


logger = logging.getLogger(__name__)


class DataService:
    def __init__(self):
        self.yc_api_url = settings.yc_api_base_url
        self.hacker_news_service = HackerNewsService()
    
    async def sync_yc_data(self, limit: int = 500):
        """Sync YC data - Stores companies with realistic filter"""
        logger.info(f"sync_yc_data called with limit={limit}")
        
        try:
            # Get all companies
            response = requests.get(f"{self.yc_api_url}/companies/all.json", timeout=60)
            
            if response.status_code == 200:
                all_companies = response.json()
                logger.info(f"Found {len(all_companies)} total companies from YC API")
                
                # Filter for companies with industries (most important filter)
                companies_with_industries = [
                    c for c in all_companies 
                    if c.get('industries') and len(c.get('industries', [])) > 0
                ]
                logger.info(f"Found {len(companies_with_industries)} companies with industry tags")
                
                # Process companies
                count = 0
                skipped = 0
                target_count = min(limit, len(companies_with_industries))
                
                logger.info(f"Syncing {target_count} companies...")
                
                for idx, company in enumerate(companies_with_industries):
                    if count >= target_count:
                        break
                    
                    # Try to store
                    was_stored = await self._store_company(company)
                    
                    if was_stored:
                        count += 1
                        if count % 100 == 0:
                            logger.info(f"Progress: {count}/{target_count} companies synced")
                    else:
                        skipped += 1
                
                logger.info(f"Sync completed: {count} companies synced successfully")
                return count
            else:
                logger.error(f"YC API returned status {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"sync_yc_data failed: {e}")
            return 0
    
    async def sync_yc_companies(self, batch_size: int = 1000) -> int:
        """Sync Y Combinator companies data"""
        try:
            # Use requests for synchronous call (easier for demo)
            logger.info("Starting YC companies sync...")
            response = requests.get(f"{self.yc_api_url}/companies/all.json", timeout=60)
            
            if response.status_code == 200:
                companies = response.json()
                
                # Store in PostgreSQL and Neo4j
                count = 0
                failed_count = 0
                total_companies = len(companies)
                logger.info(f"Found {total_companies} companies from YC API")
                
                # Process companies in batches for better performance
                for i in range(0, total_companies, batch_size):
                    batch = companies[i:i + batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1}/{(total_companies + batch_size - 1)//batch_size}")
                    
                    for company in batch:
                        try:
                            await self._store_company(company)
                            count += 1
                        except Exception as e:
                            failed_count += 1
                            logger.warning(f"Failed to store company {company.get('name', 'Unknown')}: {e}")
                            continue
                    
                    # Log progress after each batch
                    logger.info(f"Processed {count}/{total_companies} companies ({count/total_companies*100:.1f}%)")
                    
                logger.info(f"Sync completed: {count} companies synced, {failed_count} failed")
                return count
            else:
                logger.error(f"YC API returned status {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to sync YC companies: {e}")
            return 0
    
    async def _store_company(self, company_data: Dict[str, Any]) -> bool:
        """Store company data in databases - REALISTIC filter based on YC API
        Returns True if stored, False if skipped"""
        try:
            # Extract and normalize YC API fields
            name = company_data.get('name', '')
            if not name:
                return False  # Skip companies without names
            
            # YC API uses 'one_liner' for description
            description = company_data.get('one_liner', '') or company_data.get('description', '')
            if not description or len(description) < 10:  # Lowered from 20
                return False  # Skip companies without good descriptions
            
            # Get location - YC API provides this in multiple formats
            # Try all possible location fields from YC API
            location = ''
            if 'location' in company_data and company_data['location']:
                location = company_data['location']
            elif 'city' in company_data and company_data['city']:
                city = company_data['city']
                country = company_data.get('country', '')
                location = f"{city}, {country}" if country else city
            elif 'country' in company_data and company_data['country']:
                location = company_data['country']
            
            # If still no location, use region or default
            if not location:
                location = company_data.get('region', 'United States')  # Most YC companies are US-based
            
            # Get industry/tags - REQUIRED
            industries = company_data.get('industries', [])
            if not industries:
                return False  # Skip companies without industry tags
            industry = ', '.join(industries)
            
            # Founded year - OPTIONAL (use batch year if missing)
            founded_year = company_data.get('year_founded', 0)
            if not founded_year or founded_year < 1990:  # More lenient
                # Try to extract from batch
                batch = company_data.get('batch', '')
                if batch:
                    # Extract year from batch like "W21" -> 2021
                    import re
                    year_match = re.search(r'(\d{2})$', batch)
                    if year_match:
                        year = int(year_match.group(1))
                        founded_year = 2000 + year if year < 50 else 1900 + year
                    else:
                        founded_year = 2010  # Default
                else:
                    founded_year = 2010  # Default
            
            # Website URL - OPTIONAL
            website = company_data.get('website', '') or company_data.get('url', '')
            if not website:
                website = f"https://www.ycombinator.com/companies/{name.lower().replace(' ', '-')}"
            
            # YC batch - REQUIRED
            batch = company_data.get('batch', '') or company_data.get('batch_name', '')
            if not batch:
                return False  # Skip non-YC companies
            
            # Team size - YC API doesn't provide this reliably, skip it
            team_size = company_data.get('team_size', 0) or 0
            
            # Status
            status = company_data.get('status', {})
            is_active = status.get('active', True) if isinstance(status, dict) else True
            
            # Funding information
            long_description = company_data.get('long_description', description)
            tags = company_data.get('tags', [])
            
            # Store with ONLY essential requirements: name, description, industry, batch
            if all([name, description, industry, batch]):
                # Store in Neo4j
                if neo4j_conn.driver:
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
                                c.yc_batch = $batch,
                                c.is_active = $is_active,
                                c.tags = $tags,
                                c.updated_at = datetime()
                            """,
                            name=name,
                            description=description,
                            long_description=long_description,
                            industry=industry,
                            founded_year=founded_year,
                            location=location,
                            website=website,
                            batch=batch,
                            is_active=is_active,
                            tags=tags
                        )
                        return True  # Successfully stored
            
            return False  # Didn't meet minimum requirements
                    
        except Exception as e:
            logger.error(f"Failed to store company {company_data.get('name', 'Unknown')}: {e}")
            return False
    
    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search companies by query"""
        try:
            logger.info(f"DataService.search_companies called with query: '{query}', limit: {limit}")
            
            # First check Redis cache
            cache_key = f"search:{query}:{limit}"
            if redis_conn.client:
                try:
                    cached = redis_conn.client.get(cache_key)
                    if cached:
                        logger.info("Returning cached results")
                        return json.loads(cached)
                except:
                    pass  # Continue if cache fails
            
            # Query Neo4j
            results = []
            logger.info(f"Neo4j driver available: {neo4j_conn.driver is not None}")
            if neo4j_conn.driver:
                logger.info("Querying Neo4j database")
                with neo4j_conn.driver.session() as session:
                    result = session.run(
                        """
                        MATCH (c:Company) 
                        WHERE toLower(c.name) CONTAINS toLower($query) 
                           OR toLower(c.description) CONTAINS toLower($query)
                           OR toLower(c.industry) CONTAINS toLower($query)
                        RETURN c.name as name, c.description as description, 
                               c.industry as industry, c.founded_year as founded_year,
                               c.location as location, c.website as website,
                               c.yc_batch as yc_batch, id(c) as company_id
                        LIMIT $limit
                        """,
                        {"query": query, "limit": limit}
                    )
                    
                    for record in result:
                        company = {
                            'id': record['company_id'],
                            'name': record['name'],
                            'description': record['description'],
                            'industry': record['industry'],
                            'founded_year': record['founded_year'],
                            'location': record['location'],
                            'website': record['website'],
                            'yc_batch': record['yc_batch']
                        }
                        results.append(company)
                logger.info(f"Neo4j returned {len(results)} companies")
            else:
                logger.info("Neo4j driver not available, skipping database query")
            
            # If no results from Neo4j, return curated sample data based on query
            if not results:
                logger.info("No results from Neo4j, using sample data")
                results = self._get_sample_companies(query, limit)
                logger.info(f"Sample data returned {len(results)} companies")
            
            # Cache results
            if redis_conn.client and results:
                try:
                    redis_conn.client.setex(cache_key, 300, json.dumps(results))  # 5 min cache
                except:
                    pass  # Continue if cache fails
            
            return results
            
        except Exception as e:
            logger.error(f"Company search failed: {e}")
            return []

    def _get_sample_companies(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get curated sample companies based on search query"""
        query_lower = query.lower()
        
        # Define company databases by category
        company_databases = {
            'ai': [
                {
                    'id': 1,
                    'name': 'OpenAI',
                    'description': 'AI research company focused on creating safe artificial general intelligence',
                    'industry': 'Artificial Intelligence',
                    'founded_year': 2015,
                    'location': 'San Francisco, CA',
                    'website': 'https://openai.com',
                    'yc_batch': 'S15',
                    'funding': '$11.3B',
                    'employees': '500-1000',
                    'stage': 'Series C'
                },
                {
                    'id': 2,
                    'name': 'Anthropic',
                    'description': 'AI safety company developing Claude, a helpful AI assistant',
                    'industry': 'Artificial Intelligence',
                    'founded_year': 2021,
                    'location': 'San Francisco, CA',
                    'website': 'https://anthropic.com',
                    'yc_batch': 'S21',
                    'funding': '$4.1B',
                    'employees': '200-500',
                    'stage': 'Series C'
                },
                {
                    'id': 3,
                    'name': 'Cohere',
                    'description': 'Natural language processing AI platform for enterprises',
                    'industry': 'Artificial Intelligence',
                    'founded_year': 2019,
                    'location': 'Toronto, Canada',
                    'website': 'https://cohere.ai',
                    'yc_batch': 'W19',
                    'funding': '$270M',
                    'employees': '100-200',
                    'stage': 'Series C'
                }
            ],
            'edtech': [
                {
                    'id': 4,
                    'name': 'Khan Academy',
                    'description': 'Free online learning platform with personalized learning resources',
                    'industry': 'Education Technology',
                    'founded_year': 2008,
                    'location': 'Mountain View, CA',
                    'website': 'https://khanacademy.org',
                    'yc_batch': 'S08',
                    'funding': '$16M',
                    'employees': '200-500',
                    'stage': 'Non-profit'
                },
                {
                    'id': 5,
                    'name': 'Duolingo',
                    'description': 'Language learning platform with gamified lessons',
                    'industry': 'Education Technology',
                    'founded_year': 2011,
                    'location': 'Pittsburgh, PA',
                    'website': 'https://duolingo.com',
                    'yc_batch': 'S11',
                    'funding': '$183M',
                    'employees': '500-1000',
                    'stage': 'Public'
                },
                {
                    'id': 6,
                    'name': 'Coursera',
                    'description': 'Online learning platform offering courses from top universities',
                    'industry': 'Education Technology',
                    'founded_year': 2012,
                    'location': 'Mountain View, CA',
                    'website': 'https://coursera.org',
                    'yc_batch': 'S12',
                    'funding': '$464M',
                    'employees': '1000+',
                    'stage': 'Public'
                }
            ],
            'fintech': [
                {
                    'id': 7,
                    'name': 'Stripe',
                    'description': 'Online payment processing platform for internet businesses',
                    'industry': 'Financial Technology',
                    'founded_year': 2010,
                    'location': 'San Francisco, CA',
                    'website': 'https://stripe.com',
                    'yc_batch': 'S10',
                    'funding': '$2.2B',
                    'employees': '3000+',
                    'stage': 'Series H'
                },
                {
                    'id': 8,
                    'name': 'Coinbase',
                    'description': 'Cryptocurrency exchange and digital wallet platform',
                    'industry': 'Financial Technology',
                    'founded_year': 2012,
                    'location': 'San Francisco, CA',
                    'website': 'https://coinbase.com',
                    'yc_batch': 'S12',
                    'funding': '$547M',
                    'employees': '3000+',
                    'stage': 'Public'
                },
                {
                    'id': 9,
                    'name': 'Plaid',
                    'description': 'Financial data connectivity platform for fintech apps',
                    'industry': 'Financial Technology',
                    'founded_year': 2013,
                    'location': 'San Francisco, CA',
                    'website': 'https://plaid.com',
                    'yc_batch': 'S13',
                    'funding': '$734M',
                    'employees': '500-1000',
                    'stage': 'Acquired'
                }
            ],
            'healthcare': [
                {
                    'id': 10,
                    'name': '23andMe',
                    'description': 'Personal genomics and biotechnology company',
                    'industry': 'Healthcare',
                    'founded_year': 2006,
                    'location': 'Sunnyvale, CA',
                    'website': 'https://23andme.com',
                    'yc_batch': 'S06',
                    'funding': '$791M',
                    'employees': '500-1000',
                    'stage': 'Public'
                },
                {
                    'id': 11,
                    'name': 'Veracyte',
                    'description': 'Molecular diagnostics company for cancer detection',
                    'industry': 'Healthcare',
                    'founded_year': 2008,
                    'location': 'South San Francisco, CA',
                    'website': 'https://veracyte.com',
                    'yc_batch': 'S08',
                    'funding': '$300M',
                    'employees': '200-500',
                    'stage': 'Public'
                }
            ],
            'saas': [
                {
                    'id': 12,
                    'name': 'Dropbox',
                    'description': 'Cloud storage and file synchronization service',
                    'industry': 'Software as a Service',
                    'founded_year': 2007,
                    'location': 'San Francisco, CA',
                    'website': 'https://dropbox.com',
                    'yc_batch': 'S07',
                    'funding': '$1.7B',
                    'employees': '3000+',
                    'stage': 'Public'
                },
                {
                    'id': 13,
                    'name': 'Airbnb',
                    'description': 'Online marketplace for short-term homestays and experiences',
                    'industry': 'Software as a Service',
                    'founded_year': 2008,
                    'location': 'San Francisco, CA',
                    'website': 'https://airbnb.com',
                    'yc_batch': 'W08',
                    'funding': '$6.4B',
                    'employees': '5000+',
                    'stage': 'Public'
                },
                {
                    'id': 14,
                    'name': 'Twilio',
                    'description': 'Cloud communications platform for developers',
                    'industry': 'Software as a Service',
                    'founded_year': 2008,
                    'location': 'San Francisco, CA',
                    'website': 'https://twilio.com',
                    'yc_batch': 'S08',
                    'funding': '$1.2B',
                    'employees': '5000+',
                    'stage': 'Public'
                }
            ]
        }
        
        # Find matching companies based on query
        matching_companies = []
        
        # Check for exact category matches
        for category, companies in company_databases.items():
            if category in query_lower or query_lower in category:
                matching_companies.extend(companies)
        
        # Check for partial matches in company names and descriptions
        for category, companies in company_databases.items():
            for company in companies:
                if (query_lower in company['name'].lower() or 
                    query_lower in company['description'].lower() or
                    query_lower in company['industry'].lower()):
                    if company not in matching_companies:
                        matching_companies.append(company)
        
        # If no specific matches, return companies from the most relevant category
        if not matching_companies:
            if any(word in query_lower for word in ['ai', 'artificial', 'intelligence', 'machine', 'learning']):
                matching_companies = company_databases['ai']
            elif any(word in query_lower for word in ['education', 'learning', 'school', 'university']):
                matching_companies = company_databases['edtech']
            elif any(word in query_lower for word in ['finance', 'fintech', 'payment', 'banking']):
                matching_companies = company_databases['fintech']
            elif any(word in query_lower for word in ['health', 'medical', 'healthcare']):
                matching_companies = company_databases['healthcare']
            elif any(word in query_lower for word in ['saas', 'software', 'platform']):
                matching_companies = company_databases['saas']
            else:
                matching_companies = company_databases['ai']
        
        return matching_companies[:limit]
    
    async def get_company_details(self, company_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific company"""
        try:
            # First try to get from Neo4j
            if neo4j_conn.driver:
                with neo4j_conn.driver.session() as session:
                    result = session.run(
                        """
                        MATCH (c:Company) WHERE id(c) = $company_id 
                        RETURN c.name as name, c.description as description, 
                               c.industry as industry, c.founded_year as founded_year,
                               c.location as location, c.website as website,
                               c.yc_batch as yc_batch, id(c) as company_id
                        """,
                        {"company_id": company_id}
                    )
                    record = result.single()
                    if record:
                        return {
                            'id': record['company_id'],
                            'name': record['name'],
                            'description': record['description'],
                            'industry': record['industry'],
                            'founded_year': record['founded_year'],
                            'location': record['location'],
                            'website': record['website'],
                            'yc_batch': record['yc_batch']
                        }
            # Fallback to sample
            sample_companies = self._get_sample_companies("", 100)
            for company in sample_companies:
                if company['id'] == company_id:
                    return company
            return {
                'id': company_id,
                'name': f'Company {company_id}',
                'description': 'Company details not available',
                'industry': 'Unknown',
                'founded_year': 2020,
                'location': 'Unknown',
                'website': 'N/A',
                'yc_batch': 'N/A',
                'funding': 'N/A',
                'employees': 'N/A',
                'stage': 'Unknown'
            }
        except Exception as e:
            logger.error(f"Failed to get company details for ID {company_id}: {e}")
            return {
                'id': company_id,
                'name': f'Company {company_id}',
                'description': 'Error retrieving company details',
                'industry': 'Unknown',
                'founded_year': 2020,
                'location': 'Unknown',
                'website': 'N/A',
                'yc_batch': 'N/A'
            }
    
    async def get_knowledge_graph(self, company_id: int) -> Dict[str, Any]:
        """Get knowledge graph data for visualization"""
        try:
            nodes = []
            edges = []
            if neo4j_conn.driver:
                with neo4j_conn.driver.session() as session:
                    result = session.run(
                        """
                        MATCH (c:Company) WHERE id(c) = $company_id 
                        OPTIONAL MATCH (c)-[r]-(related) 
                        RETURN c, type(r) as rel_type, related LIMIT 20
                        """,
                        {"company_id": company_id}
                    )
                    company_added = False
                    for record in result:
                        company = record['c']
                        if not company_added:
                            nodes.append({
                                'id': f"company_{company_id}",
                                'label': company.get('name', f'Company {company_id}'),
                                'group': 'company',
                                'size': 30,
                                'color': '#1f77b4'
                            })
                            company_added = True
                        if record['related']:
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
                                'label': record['rel_type'] or 'related'
                            })
            if not nodes:
                nodes = [
                    {
                        'id': f'company_{company_id}',
                        'label': f'Company {company_id}',
                        'group': 'company',
                        'size': 30,
                        'color': '#1f77b4'
                    },
                    {
                        'id': 'competitor_1',
                        'label': 'Competitor A',
                        'group': 'competitor',
                        'size': 25,
                        'color': '#ff7f0e'
                    },
                    {
                        'id': 'investor_1',
                        'label': 'Investor X',
                        'group': 'investor',
                        'size': 20,
                        'color': '#2ca02c'
                    }
                ]
                edges = [
                    {
                        'from': f'company_{company_id}',
                        'to': 'competitor_1',
                        'label': 'competes_with'
                    },
                    {
                        'from': f'company_{company_id}',
                        'to': 'investor_1',
                        'label': 'funded_by'
                    }
                ]
            return {'nodes': nodes, 'edges': edges}
        except Exception as e:
            logger.error(f"Knowledge graph retrieval failed: {e}")
            return {'nodes': [], 'edges': []}

    async def get_knowledge_graph_by_name(self, company_name: str) -> Dict[str, Any]:
        """Get AI-enhanced knowledge graph data for visualization by company name"""
        try:
            nodes = []
            edges = []
            company_id = None
            company_data = None
            
            # First try to get from Neo4j
            if neo4j_conn.driver:
                with neo4j_conn.driver.session() as session:
                    result = session.run(
                        """
                        MATCH (c:Company) 
                        WHERE toLower(c.name) = toLower($company_name)
                        RETURN c, id(c) as company_id
                        LIMIT 1
                        """,
                        {"company_name": company_name}
                    )
                    record = result.single()
                    if record:
                        company_id = record['company_id']
                        company_data = record['c']
                        
                        # Add main company node
                        nodes.append({
                            'id': f"company_{company_id}",
                            'label': company_data.get('name', company_name),
                            'group': 'main_company',
                            'size': 40,
                            'color': '#1f77b4',
                            'physics': False,
                            'title': f"{company_data.get('description', '')[:100]}..."
                        })
                        
                        # Get existing relationships
                        relationships_result = session.run(
                            """
                            MATCH (c:Company) WHERE id(c) = $company_id
                            OPTIONAL MATCH (c)-[r]-(related:Company)
                            RETURN c, type(r) as rel_type, related LIMIT 10
                            """,
                            {"company_id": company_id}
                        )
                        
                        for rel_record in relationships_result:
                            if rel_record['related']:
                                related = rel_record['related']
                                related_id = f"related_{len(nodes)}"
                                nodes.append({
                                    'id': related_id,
                                    'label': related.get('name', 'Related Company'),
                                    'group': 'related_company',
                                    'size': 25,
                                    'color': '#ff7f0e',
                                    'title': f"{related.get('description', '')[:80]}..."
                                })
                                edges.append({
                                    'from': f"company_{company_id}",
                                    'to': related_id,
                                    'label': rel_record['rel_type'] or 'related',
                                    'arrows': 'to'
                                })
                        
                        # If sparse data, enhance with AI-discovered relationships
                        if len(nodes) < 5:
                            logger.info(f"Sparse graph for {company_name}, enhancing with AI...")
                            ai_nodes, ai_edges = await self._ai_enhance_knowledge_graph(
                                company_name, 
                                company_data,
                                existing_node_count=len(nodes)
                            )
                            nodes.extend(ai_nodes)
                            edges.extend(ai_edges)
            
            # If no Neo4j data, create AI-powered graph
            if not nodes:
                logger.info(f"No Neo4j data for {company_name}, creating AI-powered graph...")
                nodes, edges = await self._create_ai_powered_knowledge_graph(company_name)
            
            return {
                'nodes': nodes, 
                'edges': edges, 
                'company_name': company_name, 
                'total_nodes': len(nodes), 
                'total_edges': len(edges),
                'ai_enhanced': len(nodes) > 1
            }
        except Exception as e:
            logger.error(f"Knowledge graph retrieval failed for {company_name}: {e}")
            return {'nodes': [], 'edges': [], 'error': str(e)}

    def _create_sample_knowledge_graph(self, company_name: str) -> tuple:
        company_lower = company_name.lower()
        if any(word in company_lower for word in ['ai', 'artificial', 'openai', 'anthropic']):
            return self._create_ai_company_graph(company_name)
        elif any(word in company_lower for word in ['fintech', 'stripe', 'payment']):
            return self._create_fintech_company_graph(company_name)
        elif any(word in company_lower for word in ['health', 'medical', 'bio']):
            return self._create_healthcare_company_graph(company_name)
        else:
            return self._create_generic_company_graph(company_name)

    def _create_ai_company_graph(self, company_name: str) -> tuple:
        nodes = [
            {'id': 'main', 'label': company_name, 'group': 'main_company', 'size': 40, 'color': '#1f77b4'},
            {'id': 'comp1', 'label': 'OpenAI', 'group': 'competitor', 'size': 35, 'color': '#ff7f0e'},
            {'id': 'comp2', 'label': 'Anthropic', 'group': 'competitor', 'size': 30, 'color': '#ff7f0e'},
            {'id': 'comp3', 'label': 'Google AI', 'group': 'competitor', 'size': 35, 'color': '#ff7f0e'},
            {'id': 'inv1', 'label': 'Andreessen Horowitz', 'group': 'investor', 'size': 25, 'color': '#2ca02c'},
            {'id': 'inv2', 'label': 'Sequoia Capital', 'group': 'investor', 'size': 25, 'color': '#2ca02c'},
            {'id': 'tech1', 'label': 'Microsoft', 'group': 'partner', 'size': 30, 'color': '#d62728'},
            {'id': 'tech2', 'label': 'NVIDIA', 'group': 'partner', 'size': 25, 'color': '#d62728'},
            {'id': 'market1', 'label': 'Enterprise AI', 'group': 'market', 'size': 20, 'color': '#9467bd'},
            {'id': 'market2', 'label': 'Consumer AI', 'group': 'market', 'size': 20, 'color': '#9467bd'}
        ]
        edges = [
            {'from': 'main', 'to': 'comp1', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'main', 'to': 'comp2', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'main', 'to': 'comp3', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'inv1', 'to': 'main', 'label': 'invested_in', 'color': '#2ca02c'},
            {'from': 'inv2', 'to': 'main', 'label': 'invested_in', 'color': '#2ca02c'},
            {'from': 'main', 'to': 'tech1', 'label': 'partners_with', 'color': '#d62728'},
            {'from': 'main', 'to': 'tech2', 'label': 'partners_with', 'color': '#d62728'},
            {'from': 'main', 'to': 'market1', 'label': 'serves', 'color': '#9467bd'},
            {'from': 'main', 'to': 'market2', 'label': 'serves', 'color': '#9467bd'}
        ]
        return nodes, edges

    def _create_fintech_company_graph(self, company_name: str) -> tuple:
        nodes = [
            {'id': 'main', 'label': company_name, 'group': 'main_company', 'size': 40, 'color': '#1f77b4'},
            {'id': 'comp1', 'label': 'Stripe', 'group': 'competitor', 'size': 35, 'color': '#ff7f0e'},
            {'id': 'comp2', 'label': 'Square', 'group': 'competitor', 'size': 30, 'color': '#ff7f0e'},
            {'id': 'comp3', 'label': 'PayPal', 'group': 'competitor', 'size': 35, 'color': '#ff7f0e'},
            {'id': 'inv1', 'label': 'Tiger Global', 'group': 'investor', 'size': 25, 'color': '#2ca02c'},
            {'id': 'bank1', 'label': 'JPMorgan Chase', 'group': 'partner', 'size': 30, 'color': '#d62728'},
            {'id': 'market1', 'label': 'Online Payments', 'group': 'market', 'size': 20, 'color': '#9467bd'},
        ]
        edges = [
            {'from': 'main', 'to': 'comp1', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'main', 'to': 'comp2', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'inv1', 'to': 'main', 'label': 'invested_in', 'color': '#2ca02c'},
            {'from': 'main', 'to': 'bank1', 'label': 'partners_with', 'color': '#d62728'},
            {'from': 'main', 'to': 'market1', 'label': 'operates_in', 'color': '#9467bd'}
        ]
        return nodes, edges

    def _create_healthcare_company_graph(self, company_name: str) -> tuple:
        nodes = [
            {'id': 'main', 'label': company_name, 'group': 'main_company', 'size': 40, 'color': '#1f77b4'},
            {'id': 'comp1', 'label': 'Teladoc', 'group': 'competitor', 'size': 30, 'color': '#ff7f0e'},
            {'id': 'comp2', 'label': '23andMe', 'group': 'competitor', 'size': 25, 'color': '#ff7f0e'},
            {'id': 'inv1', 'label': 'Kleiner Perkins', 'group': 'investor', 'size': 25, 'color': '#2ca02c'},
            {'id': 'hospital1', 'label': 'Mayo Clinic', 'group': 'partner', 'size': 25, 'color': '#d62728'},
            {'id': 'market1', 'label': 'Digital Health', 'group': 'market', 'size': 20, 'color': '#9467bd'}
        ]
        edges = [
            {'from': 'main', 'to': 'comp1', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'inv1', 'to': 'main', 'label': 'invested_in', 'color': '#2ca02c'},
            {'from': 'main', 'to': 'hospital1', 'label': 'partners_with', 'color': '#d62728'},
            {'from': 'main', 'to': 'market1', 'label': 'operates_in', 'color': '#9467bd'}
        ]
        return nodes, edges

    def _create_generic_company_graph(self, company_name: str) -> tuple:
        nodes = [
            {'id': 'main', 'label': company_name, 'group': 'main_company', 'size': 40, 'color': '#1f77b4'},
            {'id': 'comp1', 'label': f'{company_name} Competitor 1', 'group': 'competitor', 'size': 25, 'color': '#ff7f0e'},
            {'id': 'comp2', 'label': f'{company_name} Competitor 2', 'group': 'competitor', 'size': 25, 'color': '#ff7f0e'},
            {'id': 'inv1', 'label': 'Venture Capital Fund', 'group': 'investor', 'size': 25, 'color': '#2ca02c'},
            {'id': 'partner1', 'label': 'Strategic Partner', 'group': 'partner', 'size': 20, 'color': '#d62728'},
            {'id': 'market1', 'label': 'Target Market', 'group': 'market', 'size': 20, 'color': '#9467bd'}
        ]
        edges = [
            {'from': 'main', 'to': 'comp1', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'main', 'to': 'comp2', 'label': 'competes_with', 'color': '#ff7f0e'},
            {'from': 'inv1', 'to': 'main', 'label': 'invested_in', 'color': '#2ca02c'},
            {'from': 'main', 'to': 'partner1', 'label': 'partners_with', 'color': '#d62728'},
            {'from': 'main', 'to': 'market1', 'label': 'serves', 'color': '#9467bd'}
        ]
        return nodes, edges
    
    async def collect_hacker_news_data(self, company_name: str, limit: int = 50) -> Dict[str, Any]:
        """Collect Hacker News data for a specific company"""
        try:
            logger.info(f"Collecting Hacker News data for {company_name}")
            
            async with HackerNewsService() as hn_service:
                # Get company mentions from Hacker News
                mentions = await hn_service.get_company_mentions(company_name, limit)
                
                # Store in knowledge graph
                await hn_service.store_hn_data(company_name, mentions)
                
                # Format for display
                formatted_mentions = {
                    'stories': [hn_service.format_hn_item(item) for item in mentions['stories']],
                    'jobs': [hn_service.format_hn_item(item) for item in mentions['jobs']],
                    'show_hn': [hn_service.format_hn_item(item) for item in mentions['show_hn']],
                    'ask_hn': [hn_service.format_hn_item(item) for item in mentions['ask_hn']],
                    'total_mentions': mentions['total_mentions'],
                    'company_name': company_name
                }
                
                logger.info(f"Collected {mentions['total_mentions']} HN mentions for {company_name}")
                return formatted_mentions
                
        except Exception as e:
            logger.error(f"Failed to collect HN data for {company_name}: {e}")
            return {
                'stories': [],
                'jobs': [],
                'show_hn': [],
                'ask_hn': [],
                'total_mentions': 0,
                'company_name': company_name,
                'error': str(e)
            }
    
    async def collect_hn_data_for_companies(self, company_names: List[str], limit_per_company: int = 30) -> Dict[str, Dict[str, Any]]:
        """Collect Hacker News data for multiple companies"""
        try:
            logger.info(f"Collecting HN data for {len(company_names)} companies")
            
            results = {}
            async with HackerNewsService() as hn_service:
                for company_name in company_names:
                    try:
                        mentions = await hn_service.get_company_mentions(company_name, limit_per_company)
                        await hn_service.store_hn_data(company_name, mentions)
                        
                        results[company_name] = {
                            'stories': [hn_service.format_hn_item(item) for item in mentions['stories']],
                            'jobs': [hn_service.format_hn_item(item) for item in mentions['jobs']],
                            'show_hn': [hn_service.format_hn_item(item) for item in mentions['show_hn']],
                            'ask_hn': [hn_service.format_hn_item(item) for item in mentions['ask_hn']],
                            'total_mentions': mentions['total_mentions']
                        }
                        
                        logger.info(f"Collected {mentions['total_mentions']} HN mentions for {company_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to collect HN data for {company_name}: {e}")
                        results[company_name] = {
                            'stories': [],
                            'jobs': [],
                            'show_hn': [],
                            'ask_hn': [],
                            'total_mentions': 0,
                            'error': str(e)
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to collect HN data for companies: {e}")
            return {}
    
    async def get_company_with_hn_data(self, company_id: int) -> Dict[str, Any]:
        """Get company details with Hacker News data"""
        try:
            # Get basic company details
            company_details = await self.get_company_details(company_id)
            
            if company_details and company_details.get('name'):
                # Get Hacker News data
                hn_data = await self.collect_hacker_news_data(company_details['name'])
                company_details['hacker_news'] = hn_data
            
            return company_details
            
        except Exception as e:
            logger.error(f"Failed to get company with HN data for ID {company_id}: {e}")
            return await self.get_company_details(company_id)
    
    async def _ai_enhance_knowledge_graph(self, company_name: str, company_data: Dict, existing_node_count: int) -> tuple:
        """Use AI to discover relationships and enhance sparse knowledge graphs"""
        try:
            from agents.crew_manager import CrewManager
            crew_manager = CrewManager()
            
            # Prepare company context
            industry = company_data.get('industry', 'Unknown')
            description = company_data.get('description', '')
            location = company_data.get('location', 'Unknown')
            
            # Ask LLM to identify key relationships
            prompt = f"""For the company "{company_name}" in the {industry} industry, identify 4-6 key entities they would interact with.

Company: {company_name}
Description: {description}
Location: {location}

List:
1. 2-3 direct competitors (companies in same space)
2. 1-2 technology partners or platforms they likely use
3. 1-2 market segments or customer types they serve

Be specific and realistic. Format as: Category|EntityName"""

            response = await crew_manager.handle_conversation(prompt, f"kg_{company_name}")
            
            # Parse LLM response and create nodes/edges
            nodes = []
            edges = []
            node_id_counter = existing_node_count
            
            # Parse response (fallback to industry-based if parsing fails)
            if isinstance(response, str) and response:
                lines = response.split('\n')
                for line in lines:
                    if '|' in line:
                        try:
                            category, entity = line.strip().split('|', 1)
                            category = category.lower().strip()
                            entity = entity.strip()
                            
                            # Determine group and relationship
                            if 'competitor' in category:
                                group = 'competitor'
                                rel_label = 'competes_with'
                                color = '#ff7f0e'
                            elif 'partner' in category or 'platform' in category:
                                group = 'partner'
                                rel_label = 'partners_with'
                                color = '#2ca02c'
                            elif 'market' in category or 'customer' in category:
                                group = 'market'
                                rel_label = 'serves'
                                color = '#9467bd'
                            else:
                                group = 'related'
                                rel_label = 'related_to'
                                color = '#d62728'
                            
                            node_id = f"ai_node_{node_id_counter}"
                            nodes.append({
                                'id': node_id,
                                'label': entity,
                                'group': group,
                                'size': 22,
                                'color': color,
                                'title': f"{category}: {entity}"
                            })
                            
                            edges.append({
                                'from': f"company_{existing_node_count-1}" if existing_node_count > 0 else 'main',
                                'to': node_id,
                                'label': rel_label,
                                'arrows': 'to',
                                'color': color
                            })
                            
                            node_id_counter += 1
                        except Exception as e:
                            logger.debug(f"Failed to parse line '{line}': {e}")
                            continue
            
            # If AI didn't provide enough, add industry-based fallback
            if len(nodes) < 3:
                nodes, edges = self._create_industry_based_graph_enhancement(
                    company_name, 
                    industry,
                    node_id_counter
                )
            
            logger.info(f"AI enhanced graph for {company_name} with {len(nodes)} nodes")
            return nodes, edges
            
        except Exception as e:
            logger.error(f"AI enhancement failed for {company_name}: {e}")
            # Fallback to generic enhancement
            return self._create_industry_based_graph_enhancement(company_name, "Technology", existing_node_count)
    
    def _create_industry_based_graph_enhancement(self, company_name: str, industry: str, start_id: int) -> tuple:
        """Create graph enhancement based on industry patterns"""
        nodes = []
        edges = []
        
        industry_lower = industry.lower() if industry else ""
        
        # Industry-specific entities
        if any(word in industry_lower for word in ['ai', 'machine learning', 'artificial']):
            entities = [
                ('OpenAI', 'competitor', 'competes_with', '#ff7f0e'),
                ('AWS/Azure', 'partner', 'uses_platform', '#2ca02c'),
                ('Enterprise AI Market', 'market', 'serves', '#9467bd')
            ]
        elif any(word in industry_lower for word in ['fintech', 'payment', 'finance']):
            entities = [
                ('Stripe', 'competitor', 'competes_with', '#ff7f0e'),
                ('Banks/Financial Institutions', 'partner', 'partners_with', '#2ca02c'),
                ('SMB/Enterprise', 'market', 'serves', '#9467bd')
            ]
        elif any(word in industry_lower for word in ['health', 'medical', 'bio']):
            entities = [
                ('Healthcare Providers', 'customer', 'serves', '#9467bd'),
                ('FDA/Regulatory', 'related', 'complies_with', '#d62728'),
                ('Medical Research', 'market', 'supports', '#9467bd')
            ]
        elif any(word in industry_lower for word in ['education', 'edtech']):
            entities = [
                ('Coursera', 'competitor', 'competes_with', '#ff7f0e'),
                ('Schools/Universities', 'customer', 'serves', '#9467bd'),
                ('Online Learning Market', 'market', 'operates_in', '#9467bd')
            ]
        elif any(word in industry_lower for word in ['ecommerce', 'retail', 'marketplace']):
            entities = [
                ('Amazon', 'competitor', 'competes_with', '#ff7f0e'),
                ('Shopify', 'partner', 'integrates_with', '#2ca02c'),
                ('Online Shoppers', 'market', 'serves', '#9467bd')
            ]
        else:
            # Generic tech company
            entities = [
                ('Industry Leader', 'competitor', 'competes_with', '#ff7f0e'),
                ('Cloud Platform', 'partner', 'uses', '#2ca02c'),
                ('Target Market', 'market', 'serves', '#9467bd')
            ]
        
        for idx, (entity, group, rel_label, color) in enumerate(entities):
            node_id = f"ind_node_{start_id + idx}"
            nodes.append({
                'id': node_id,
                'label': entity,
                'group': group,
                'size': 20,
                'color': color,
                'title': f"{group}: {entity}"
            })
            edges.append({
                'from': 'main' if start_id == 0 else f"company_{start_id-1}",
                'to': node_id,
                'label': rel_label,
                'arrows': 'to',
                'color': color
            })
        
        return nodes, edges
    
    async def _create_ai_powered_knowledge_graph(self, company_name: str) -> tuple:
        """Create a complete knowledge graph using AI when no Neo4j data exists"""
        try:
            # Search for company in our data first
            companies = await self.search_companies(company_name, 1)
            company_data = companies[0] if companies else {}
            
            # Main company node
            nodes = [{
                'id': 'main',
                'label': company_name,
                'group': 'main_company',
                'size': 40,
                'color': '#1f77b4',
                'physics': False,
                'title': company_data.get('description', f"{company_name} - No description available")[:100]
            }]
            edges = []
            
            # Get AI-enhanced relationships
            ai_nodes, ai_edges = await self._ai_enhance_knowledge_graph(
                company_name,
                company_data,
                existing_node_count=1
            )
            
            nodes.extend(ai_nodes)
            edges.extend(ai_edges)
            
            logger.info(f"Created AI-powered graph for {company_name} with {len(nodes)} nodes")
            return nodes, edges
            
        except Exception as e:
            logger.error(f"AI-powered graph creation failed for {company_name}: {e}")
            # Final fallback to sample graph
            return self._create_sample_knowledge_graph(company_name)
