import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import logging
import time
from urllib.parse import urljoin, urlparse
import random

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 1  # Seconds between requests
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scrape_crunchbase_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Scrape basic company information from Crunchbase"""
        try:
            # Respectful scraping with delays
            await asyncio.sleep(self.rate_limit_delay)

            # Format URL (simplified for demo)
            search_url = f"https://www.crunchbase.com/discover/organization.companies/field/organizations/company_name/{company_name}"

            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_crunchbase_html(html, company_name)
                else:
                    logger.warning(f"Crunchbase request failed with status {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Failed to scrape Crunchbase for {company_name}: {e}")
            return None

    def _parse_crunchbase_html(self, html: str, company_name: str) -> Dict[str, Any]:
        """Parse Crunchbase HTML content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # This would contain actual parsing logic for Crunchbase
            # For demo purposes, return mock data
            return {
                'name': company_name,
                'description': f"Company information scraped for {company_name}",
                'funding_total': "$10M",
                'employees': "11-50",
                'founded_date': "2020",
                'headquarters': "San Francisco, CA",
                'website': f"https://www.{company_name.lower().replace(' ', '')}.com",
                'industries': ["Technology", "SaaS"],
                'source': 'crunchbase'
            }

        except Exception as e:
            logger.error(f"Failed to parse Crunchbase HTML for {company_name}: {e}")
            return {}

    async def scrape_angellist_startup(self, startup_name: str) -> Optional[Dict[str, Any]]:
        """Scrape startup information from AngelList/Wellfound"""
        try:
            await asyncio.sleep(self.rate_limit_delay)

            # AngelList public data scraping (respectful)
            search_url = f"https://wellfound.com/company/{startup_name.lower().replace(' ', '-')}"

            headers = {'User-Agent': random.choice(self.user_agents)}

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_angellist_html(html, startup_name)
                else:
                    logger.warning(f"AngelList request failed with status {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Failed to scrape AngelList for {startup_name}: {e}")
            return None

    def _parse_angellist_html(self, html: str, startup_name: str) -> Dict[str, Any]:
        """Parse AngelList HTML content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Mock data for demo - would contain actual parsing logic
            return {
                'name': startup_name,
                'description': f"AngelList data for {startup_name}",
                'stage': "Seed",
                'location': "San Francisco",
                'company_size': "1-10 employees",
                'markets': ["B2B", "SaaS"],
                'source': 'angellist'
            }

        except Exception as e:
            logger.error(f"Failed to parse AngelList HTML for {startup_name}: {e}")
            return {}

    async def batch_scrape_companies(self, company_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Scrape multiple companies with rate limiting"""
        results = {}

        async with self:  # Use context manager
            for name in company_names:
                # Scrape from multiple sources
                crunchbase_data = await self.scrape_crunchbase_company(name)
                angellist_data = await self.scrape_angellist_startup(name)

                # Combine data
                combined_data = {}
                if crunchbase_data:
                    combined_data.update(crunchbase_data)
                if angellist_data:
                    combined_data.update(angellist_data)

                if combined_data:
                    results[name] = combined_data

                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)

        return results
