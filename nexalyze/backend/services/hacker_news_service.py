import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta
from config.settings import settings
from database.connections import neo4j_conn, postgres_conn, redis_conn
import requests

logger = logging.getLogger(__name__)

class HackerNewsService:
    def __init__(self):
        self.base_url = settings.hacker_news_api_base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_story_ids(self, story_type: str = "newstories", limit: int = 100) -> List[int]:
        """Get list of story IDs from Hacker News API"""
        try:
            url = f"{self.base_url}/{story_type}.json"
            
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        return story_ids[:limit]
            else:
                # Fallback to requests for synchronous calls
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    story_ids = response.json()
                    return story_ids[:limit]
            
            logger.error(f"Failed to fetch {story_type} IDs: HTTP {response.status}")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching {story_type} IDs: {e}")
            return []
    
    async def get_item_details(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific item"""
        try:
            url = f"{self.base_url}/item/{item_id}.json"
            
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            else:
                # Fallback to requests
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching item {item_id}: {e}")
            return None
    
    async def get_multiple_items(self, item_ids: List[int], max_concurrent: int = 10) -> List[Dict[str, Any]]:
        """Get multiple items concurrently with rate limiting"""
        items = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_item(item_id: int):
            async with semaphore:
                return await self.get_item_details(item_id)
        
        tasks = [fetch_item(item_id) for item_id in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result is not None:
                items.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Failed to fetch item: {result}")
        
        return items
    
    async def search_stories_by_keywords(self, keywords: List[str], story_types: List[str] = None, 
                                       limit: int = 50, max_age_days: int = 7) -> List[Dict[str, Any]]:
        """Search for stories containing specific keywords"""
        if story_types is None:
            story_types = ["newstories", "topstories", "beststories"]
        
        matching_stories = []
        cutoff_time = int((datetime.now() - timedelta(days=max_age_days)).timestamp())
        
        try:
            # Get story IDs from different categories
            all_story_ids = []
            for story_type in story_types:
                story_ids = await self.get_story_ids(story_type, limit)
                all_story_ids.extend(story_ids)
            
            # Remove duplicates while preserving order
            unique_story_ids = list(dict.fromkeys(all_story_ids))
            
            # Get item details for all stories
            items = await self.get_multiple_items(unique_story_ids[:limit * 2])  # Get more to filter
            
            # Filter by keywords and age
            for item in items:
                if not item or item.get('type') != 'story':
                    continue
                
                # Check age
                if item.get('time', 0) < cutoff_time:
                    continue
                
                # Check for keyword matches
                title = item.get('title', '').lower()
                text = item.get('text', '').lower()
                url = item.get('url', '').lower()
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if (keyword_lower in title or 
                        keyword_lower in text or 
                        keyword_lower in url):
                        
                        # Add metadata
                        item['matched_keyword'] = keyword
                        item['matched_in'] = []
                        if keyword_lower in title:
                            item['matched_in'].append('title')
                        if keyword_lower in text:
                            item['matched_in'].append('text')
                        if keyword_lower in url:
                            item['matched_in'].append('url')
                        
                        matching_stories.append(item)
                        break  # Only add once per story
            
            # Sort by score and time
            matching_stories.sort(key=lambda x: (x.get('score', 0), x.get('time', 0)), reverse=True)
            
            return matching_stories[:limit]
            
        except Exception as e:
            logger.error(f"Error searching stories by keywords: {e}")
            return []
    
    async def search_jobs_by_keywords(self, keywords: List[str], limit: int = 20, 
                                    max_age_days: int = 30) -> List[Dict[str, Any]]:
        """Search for job postings containing specific keywords"""
        matching_jobs = []
        cutoff_time = int((datetime.now() - timedelta(days=max_age_days)).timestamp())
        
        try:
            # Get job story IDs
            job_ids = await self.get_story_ids("jobstories", limit * 2)
            
            # Get job details
            jobs = await self.get_multiple_items(job_ids)
            
            # Filter by keywords and age
            for job in jobs:
                if not job or job.get('type') != 'job':
                    continue
                
                # Check age
                if job.get('time', 0) < cutoff_time:
                    continue
                
                # Check for keyword matches
                title = job.get('title', '').lower()
                text = job.get('text', '').lower()
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in title or keyword_lower in text:
                        job['matched_keyword'] = keyword
                        job['matched_in'] = []
                        if keyword_lower in title:
                            job['matched_in'].append('title')
                        if keyword_lower in text:
                            job['matched_in'].append('text')
                        
                        matching_jobs.append(job)
                        break
            
            # Sort by time (newest first)
            matching_jobs.sort(key=lambda x: x.get('time', 0), reverse=True)
            
            return matching_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching jobs by keywords: {e}")
            return []
    
    async def search_show_hn_by_keywords(self, keywords: List[str], limit: int = 20, 
                                       max_age_days: int = 7) -> List[Dict[str, Any]]:
        """Search for Show HN posts containing specific keywords"""
        matching_show_hn = []
        cutoff_time = int((datetime.now() - timedelta(days=max_age_days)).timestamp())
        
        try:
            # Get story IDs from different categories
            all_story_ids = []
            for story_type in ["newstories", "topstories", "beststories"]:
                story_ids = await self.get_story_ids(story_type, limit * 2)
                all_story_ids.extend(story_ids)
            
            # Remove duplicates
            unique_story_ids = list(dict.fromkeys(all_story_ids))
            
            # Get item details
            items = await self.get_multiple_items(unique_story_ids[:limit * 3])
            
            # Filter for Show HN posts
            for item in items:
                if not item or item.get('type') != 'story':
                    continue
                
                # Check if it's a Show HN post
                title = item.get('title', '')
                if not title.lower().startswith('show hn:'):
                    continue
                
                # Check age
                if item.get('time', 0) < cutoff_time:
                    continue
                
                # Check for keyword matches
                title_lower = title.lower()
                text = item.get('text', '').lower()
                url = item.get('url', '').lower()
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if (keyword_lower in title_lower or 
                        keyword_lower in text or 
                        keyword_lower in url):
                        
                        item['matched_keyword'] = keyword
                        item['matched_in'] = []
                        if keyword_lower in title_lower:
                            item['matched_in'].append('title')
                        if keyword_lower in text:
                            item['matched_in'].append('text')
                        if keyword_lower in url:
                            item['matched_in'].append('url')
                        
                        matching_show_hn.append(item)
                        break
            
            # Sort by score and time
            matching_show_hn.sort(key=lambda x: (x.get('score', 0), x.get('time', 0)), reverse=True)
            
            return matching_show_hn[:limit]
            
        except Exception as e:
            logger.error(f"Error searching Show HN by keywords: {e}")
            return []
    
    async def search_ask_hn_by_keywords(self, keywords: List[str], limit: int = 20, 
                                      max_age_days: int = 7) -> List[Dict[str, Any]]:
        """Search for Ask HN posts containing specific keywords"""
        matching_ask_hn = []
        cutoff_time = int((datetime.now() - timedelta(days=max_age_days)).timestamp())
        
        try:
            # Get story IDs from different categories
            all_story_ids = []
            for story_type in ["newstories", "topstories", "beststories"]:
                story_ids = await self.get_story_ids(story_type, limit * 2)
                all_story_ids.extend(story_ids)
            
            # Remove duplicates
            unique_story_ids = list(dict.fromkeys(all_story_ids))
            
            # Get item details
            items = await self.get_multiple_items(unique_story_ids[:limit * 3])
            
            # Filter for Ask HN posts
            for item in items:
                if not item or item.get('type') != 'story':
                    continue
                
                # Check if it's an Ask HN post
                title = item.get('title', '')
                if not title.lower().startswith('ask hn:'):
                    continue
                
                # Check age
                if item.get('time', 0) < cutoff_time:
                    continue
                
                # Check for keyword matches
                title_lower = title.lower()
                text = item.get('text', '').lower()
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in title_lower or keyword_lower in text:
                        item['matched_keyword'] = keyword
                        item['matched_in'] = []
                        if keyword_lower in title_lower:
                            item['matched_in'].append('title')
                        if keyword_lower in text:
                            item['matched_in'].append('text')
                        
                        matching_ask_hn.append(item)
                        break
            
            # Sort by score and time
            matching_ask_hn.sort(key=lambda x: (x.get('score', 0), x.get('time', 0)), reverse=True)
            
            return matching_ask_hn[:limit]
            
        except Exception as e:
            logger.error(f"Error searching Ask HN by keywords: {e}")
            return []
    
    async def get_company_mentions(self, company_name: str, limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Get all types of mentions for a company"""
        keywords = [company_name]
        
        # Add common variations
        if ' ' in company_name:
            keywords.extend(company_name.split())
        
        try:
            # Search different types of content
            stories = await self.search_stories_by_keywords(keywords, limit=limit//4)
            jobs = await self.search_jobs_by_keywords(keywords, limit=limit//4)
            show_hn = await self.search_show_hn_by_keywords(keywords, limit=limit//4)
            ask_hn = await self.search_ask_hn_by_keywords(keywords, limit=limit//4)
            
            return {
                'stories': stories,
                'jobs': jobs,
                'show_hn': show_hn,
                'ask_hn': ask_hn,
                'total_mentions': len(stories) + len(jobs) + len(show_hn) + len(ask_hn)
            }
            
        except Exception as e:
            logger.error(f"Error getting company mentions for {company_name}: {e}")
            return {
                'stories': [],
                'jobs': [],
                'show_hn': [],
                'ask_hn': [],
                'total_mentions': 0
            }
    
    async def store_hn_data(self, company_name: str, mentions_data: Dict[str, List[Dict[str, Any]]]):
        """Store Hacker News data in Neo4j for knowledge graph"""
        try:
            if not neo4j_conn.driver:
                logger.warning("Neo4j not available, skipping data storage")
                return
            
            with neo4j_conn.driver.session() as session:
                # Create or update company node
                session.run(
                    """
                    MERGE (c:Company {name: $company_name})
                    SET c.last_hn_update = datetime(),
                        c.hn_mentions_count = $total_mentions
                    """,
                    company_name=company_name,
                    total_mentions=mentions_data.get('total_mentions', 0)
                )
                
                # Create HN story nodes and relationships
                for story in mentions_data.get('stories', []):
                    session.run(
                        """
                        MATCH (c:Company {name: $company_name})
                        MERGE (s:HNStory {id: $story_id})
                        SET s.title = $title,
                            s.url = $url,
                            s.score = $score,
                            s.time = $time,
                            s.matched_keyword = $matched_keyword,
                            s.matched_in = $matched_in
                        MERGE (c)-[:MENTIONED_IN]->(s)
                        """,
                        company_name=company_name,
                        story_id=story.get('id'),
                        title=story.get('title', ''),
                        url=story.get('url', ''),
                        score=story.get('score', 0),
                        time=story.get('time', 0),
                        matched_keyword=story.get('matched_keyword', ''),
                        matched_in=story.get('matched_in', [])
                    )
                
                # Create HN job nodes and relationships
                for job in mentions_data.get('jobs', []):
                    session.run(
                        """
                        MATCH (c:Company {name: $company_name})
                        MERGE (j:HNJob {id: $job_id})
                        SET j.title = $title,
                            j.text = $text,
                            j.time = $time,
                            j.matched_keyword = $matched_keyword,
                            j.matched_in = $matched_in
                        MERGE (c)-[:HIRING_IN]->(j)
                        """,
                        company_name=company_name,
                        job_id=job.get('id'),
                        title=job.get('title', ''),
                        text=job.get('text', ''),
                        time=job.get('time', 0),
                        matched_keyword=job.get('matched_keyword', ''),
                        matched_in=job.get('matched_in', [])
                    )
                
                logger.info(f"Stored HN data for {company_name}")
                
        except Exception as e:
            logger.error(f"Error storing HN data for {company_name}: {e}")
    
    def format_hn_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Format HN item for display"""
        if not item:
            return {}
        
        # Convert timestamp to readable date
        timestamp = item.get('time', 0)
        if timestamp:
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_str = 'Unknown'
        
        return {
            'id': item.get('id'),
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'score': item.get('score', 0),
            'by': item.get('by', ''),
            'time': timestamp,
            'date': date_str,
            'descendants': item.get('descendants', 0),
            'text': item.get('text', ''),
            'type': item.get('type', ''),
            'matched_keyword': item.get('matched_keyword', ''),
            'matched_in': item.get('matched_in', []),
            'hn_url': f"https://news.ycombinator.com/item?id={item.get('id')}" if item.get('id') else ''
        }
