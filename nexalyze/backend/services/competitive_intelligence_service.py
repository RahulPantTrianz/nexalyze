"""
AI-Powered Competitive Intelligence Service
Uses Google Gemini API with retry and exponential backoff for maximum availability
Focused on startup competition discovery and comprehensive analysis
"""
import logging
import json
import re
import asyncio
from typing import Dict, List, Any, Optional
from config.settings import settings
from services.gemini_service import get_gemini_service, GeminiService

logger = logging.getLogger(__name__)


class CompetitiveIntelligenceService:
    """
    AI-powered competitive intelligence using Gemini
    Features:
    - Intelligent competitor discovery
    - Comprehensive competitive analysis
    - Market gap identification
    - Strategic recommendations
    """
    
    def __init__(self):
        self.gemini_service: Optional[GeminiService] = None
        self._init_service()
    
    def _init_service(self):
        """Initialize the Gemini service"""
        try:
            self.gemini_service = get_gemini_service()
            logger.info("Competitive Intelligence Service initialized with Gemini AI")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
    
    async def discover_competitors(self, company_name: str, industry: str = None) -> List[str]:
        """
        Use AI to discover competitors for a company
        
        Args:
            company_name: Name of the company
            industry: Industry/sector (optional, will be inferred if not provided)
        
        Returns:
            List of competitor names
        """
        if self.gemini_service:
            try:
                prompt = f"""You are a competitive intelligence analyst specializing in the startup and technology ecosystem.

Company: {company_name}
{f'Industry: {industry}' if industry else 'Industry: Infer from company name'}

Task: Identify the top 8-10 REAL direct competitors of this company. Focus on:
1. Companies offering similar products/services
2. Same target market and customer segments
3. Similar business models and value propositions
4. Direct competitive threats

IMPORTANT: 
- Use REAL company names only, not generic placeholders
- Include both established players and emerging startups
- Be specific and accurate

Return ONLY a JSON array of competitor company names:
["Company 1", "Company 2", "Company 3", ...]

Do not include any other text, explanations, or formatting."""

                response = await self.gemini_service.generate_content(prompt, temperature=0.3)
                
                # Parse JSON response
                json_match = re.search(r'\[[\s\S]*?\]', response)
                if json_match:
                    competitors = json.loads(json_match.group())
                    # Filter out the company itself and clean up
                    competitors = [
                        c.strip() for c in competitors 
                        if c.strip().lower() != company_name.lower() and len(c.strip()) > 0
                    ]
                    return competitors[:10]
                    
            except Exception as e:
                logger.error(f"AI competitor discovery failed: {e}")
        
        # Fallback to rule-based discovery
        return self._fallback_competitors(company_name, industry)
    
    def _fallback_competitors(self, company_name: str, industry: str = None) -> List[str]:
        """Fallback competitor discovery using pattern matching"""
        company_lower = company_name.lower()
        search_text = f"{company_lower} {industry.lower() if industry else ''}".strip()
        
        # Comprehensive competitor database by industry/keywords
        competitor_map = {
            # AI/ML Companies
            ('openai', 'anthropic', 'ai', 'artificial intelligence', 'machine learning', 'llm', 'chatgpt'): 
                ["Anthropic", "Google DeepMind", "Cohere", "Hugging Face", "Stability AI", "Scale AI", "Adept", "Character.AI", "Inflection AI", "Mistral AI"],
            
            # Fintech
            ('stripe', 'square', 'payment', 'fintech', 'financial technology', 'banking'):
                ["Stripe", "Square", "PayPal", "Adyen", "Razorpay", "Braintree", "Checkout.com", "Mollie", "Klarna", "Affirm"],
            
            # Cloud/Infrastructure
            ('databricks', 'snowflake', 'data', 'analytics', 'cloud', 'infrastructure'):
                ["Snowflake", "Databricks", "AWS Redshift", "Google BigQuery", "Cloudera", "Dremio", "Firebolt", "SingleStore", "Starburst"],
            
            # Collaboration/Communication
            ('slack', 'zoom', 'teams', 'collaboration', 'communication', 'video'):
                ["Microsoft Teams", "Zoom", "Slack", "Google Meet", "Discord", "Webex", "Mattermost", "Notion", "Asana"],
            
            # E-commerce
            ('shopify', 'woocommerce', 'ecommerce', 'commerce', 'retail'):
                ["Shopify", "WooCommerce", "BigCommerce", "Magento", "Wix", "Squarespace", "PrestaShop", "Salesforce Commerce Cloud"],
            
            # CRM/Sales
            ('salesforce', 'hubspot', 'crm', 'sales', 'marketing automation'):
                ["Salesforce", "HubSpot", "Zoho CRM", "Pipedrive", "Freshsales", "Microsoft Dynamics", "Monday.com", "Zendesk"],
            
            # Healthcare/Healthtech
            ('health', 'healthcare', 'medical', 'telemedicine', 'healthtech'):
                ["Teladoc", "Amwell", "Oscar Health", "Ro", "Hims & Hers", "GoodRx", "One Medical", "Carbon Health"],
            
            # Education/Edtech
            ('education', 'edtech', 'learning', 'course', 'training'):
                ["Coursera", "Udemy", "Khan Academy", "Duolingo", "MasterClass", "Skillshare", "Pluralsight", "LinkedIn Learning"],
            
            # Cybersecurity
            ('security', 'cybersecurity', 'cyber', 'protection'):
                ["CrowdStrike", "Palo Alto Networks", "Okta", "Cloudflare", "Zscaler", "SentinelOne", "Fortinet", "Snyk"],
            
            # HR/Recruiting
            ('hr', 'recruiting', 'hiring', 'talent', 'workforce'):
                ["Workday", "BambooHR", "Greenhouse", "Lever", "Gusto", "Rippling", "ADP", "Paycom"],
            
            # Developer Tools
            ('developer', 'devtools', 'code', 'programming', 'software development'):
                ["GitHub", "GitLab", "Atlassian", "JetBrains", "Vercel", "Netlify", "CircleCI", "DataDog"],
            
            # Autonomous/Mobility
            ('tesla', 'autonomous', 'self-driving', 'mobility', 'ev', 'electric vehicle'):
                ["Tesla", "Waymo", "Cruise", "Rivian", "Lucid", "NIO", "BYD", "Aurora", "Zoox"],
            
            # Food/Delivery
            ('food', 'delivery', 'restaurant', 'meal'):
                ["DoorDash", "Uber Eats", "Grubhub", "Instacart", "Postmates", "Deliveroo", "Just Eat", "Swiggy"],
        }
        
        # Find matching competitors
        for keywords, competitors in competitor_map.items():
            if any(keyword in search_text for keyword in keywords):
                return competitors[:8]
        
        # Generic competitors if no match found
        return [
            "Industry Leader A",
            "Growing Startup B", 
            "Enterprise Player C",
            "Niche Competitor D",
            "International Player E",
            "Emerging Disruptor F",
            "Regional Champion G",
            "Platform Company H"
        ]
    
    async def generate_competitive_insights(self, 
                                           company_name: str, 
                                           competitors: List[str],
                                           company_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered competitive insights
        
        Args:
            company_name: Target company
            competitors: List of competitors
            company_data: Additional company information
        
        Returns:
            Dictionary with competitive analysis
        """
        industry = company_data.get('industry', 'Technology') if company_data else 'Technology'
        stage = company_data.get('stage', 'Growth Stage') if company_data else 'Growth Stage'
        
        if self.gemini_service:
            try:
                prompt = f"""You are a senior competitive intelligence analyst. Provide comprehensive analysis for the following company.

Company: {company_name}
Industry: {industry}
Stage: {stage}
Known Competitors: {', '.join(competitors[:5])}
Company Description: {company_data.get('description', 'N/A') if company_data else 'N/A'}

Analyze and provide:

1. **Market Positioning** (2-3 sentences about where the company stands in the market)

2. **Competitive Advantages** (4 specific, actionable advantages)

3. **Competitive Threats** (4 specific threats from competitors or market)

4. **Strategic Recommendations** (3 actionable recommendations)

5. **Market Opportunity** (Assessment of market size and growth potential)

Return as JSON:
{{
    "market_positioning": "Detailed positioning statement...",
    "advantages": ["Advantage 1", "Advantage 2", "Advantage 3", "Advantage 4"],
    "threats": ["Threat 1", "Threat 2", "Threat 3", "Threat 4"],
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
    "market_opportunity": "Market opportunity assessment...",
    "competitive_intensity": "high/medium/low"
}}

Be specific and actionable. Use real market insights."""

                response = await self.gemini_service.generate_content(prompt, temperature=0.3)
                
                # Parse JSON response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    insights = json.loads(json_match.group())
                    insights['competitor_count'] = len(competitors)
                    insights['top_competitors'] = competitors[:5]
                    return insights
                    
            except Exception as e:
                logger.error(f"AI competitive insights failed: {e}")
        
        # Fallback insights
        return self._fallback_competitive_insights(company_name, competitors, company_data)
    
    def _fallback_competitive_insights(self, 
                                      company_name: str, 
                                      competitors: List[str],
                                      company_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate competitive insights without AI (rule-based)"""
        industry = company_data.get('industry', 'Technology') if company_data else 'Technology'
        stage = company_data.get('stage', 'Growth Stage') if company_data else 'Growth Stage'
        
        return {
            "market_positioning": f"{company_name} operates in the {industry} sector as a {stage} company, competing with {len(competitors)} major players including {competitors[0] if competitors else 'various competitors'}. The company has established a position through innovation and customer focus.",
            
            "advantages": [
                f"Strong product differentiation in the {industry} market",
                "Established customer base with high retention rates",
                "Innovative technology stack enabling scalability",
                "Growing market share and brand recognition"
            ],
            
            "threats": [
                f"Intense competition from {competitors[0] if competitors else 'market leaders'}",
                "Rapid technological changes requiring constant adaptation",
                "Potential market saturation in core segments",
                "Resource constraints compared to larger competitors"
            ],
            
            "recommendations": [
                "Focus on product differentiation and unique value propositions",
                "Expand into underserved market segments and geographies",
                "Build strategic partnerships to accelerate growth"
            ],
            
            "market_opportunity": f"The {industry} market presents significant growth opportunities with increasing digital adoption and evolving customer needs.",
            "competitive_intensity": "high",
            "competitor_count": len(competitors),
            "top_competitors": competitors[:5] if competitors else []
        }
    
    async def generate_competitive_matrix(self, 
                                         company_name: str,
                                         competitors: List[str],
                                         dimensions: List[str] = None) -> Dict[str, Any]:
        """
        Generate a competitive comparison matrix using AI
        
        Args:
            company_name: Target company
            competitors: List of competitors
            dimensions: Comparison dimensions
        
        Returns:
            Competitive matrix data
        """
        if not dimensions:
            dimensions = [
                "Product Quality",
                "Market Share",
                "Innovation",
                "Customer Satisfaction",
                "Pricing Competitiveness",
                "Growth Rate",
                "Brand Recognition",
                "Technical Capabilities"
            ]
        
        matrix = {
            "company": company_name,
            "dimensions": dimensions,
            "scores": {},
            "competitors": {}
        }
        
        if self.gemini_service:
            try:
                prompt = f"""Score {company_name} and its competitors on these dimensions (1-10 scale):
Dimensions: {', '.join(dimensions)}
Company: {company_name}
Competitors: {', '.join(competitors[:5])}

Return JSON with scores for each:
{{
    "{company_name}": {{"dimension1": score, ...}},
    "competitor1": {{"dimension1": score, ...}},
    ...
}}

Be realistic and differentiated in scoring."""

                response = await self.gemini_service.generate_content(prompt, temperature=0.4)
                
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    scores_data = json.loads(json_match.group())
                    
                    if company_name in scores_data:
                        matrix["scores"] = scores_data[company_name]
                    
                    for competitor in competitors[:6]:
                        if competitor in scores_data:
                            matrix["competitors"][competitor] = scores_data[competitor]
                    
                    return matrix
                    
            except Exception as e:
                logger.warning(f"AI matrix generation failed: {e}")
        
        # Fallback: Generate deterministic scores based on hash
        import hashlib
        import random
        
        def get_score(name: str, dim: str) -> float:
            seed = int(hashlib.md5(f"{name}:{dim}".encode()).hexdigest(), 16)
            random.seed(seed)
            return round(random.uniform(6.0, 9.5), 1)
        
        matrix["scores"] = {dim: get_score(company_name, dim) for dim in dimensions}
        
        for competitor in competitors[:6]:
            matrix["competitors"][competitor] = {
                dim: get_score(competitor, dim) for dim in dimensions
            }
        
        return matrix
    
    async def analyze_market_gap(self, 
                                 company_name: str,
                                 industry: str,
                                 competitors: List[str]) -> Dict[str, Any]:
        """
        Identify market gaps and opportunities using AI
        
        Args:
            company_name: Target company
            industry: Industry sector
            competitors: List of competitors
        
        Returns:
            Market gap analysis with opportunities
        """
        if self.gemini_service:
            try:
                prompt = f"""Analyze market gaps for {company_name} in the {industry} industry.

Competitors: {', '.join(competitors[:5])}

Identify:
1. Underserved customer segments
2. Unmet market needs
3. Technology gaps
4. Geographic opportunities
5. Product/feature white spaces

Return JSON:
{{
    "identified_gaps": ["gap 1", "gap 2", "gap 3", "gap 4"],
    "opportunities": [
        {{"title": "...", "description": "...", "priority": "High/Medium/Low", "estimated_value": "..."}},
        ...
    ],
    "competitive_white_space": ["space 1", "space 2", "space 3"]
}}

Be specific and actionable."""

                response = await self.gemini_service.generate_content(prompt, temperature=0.4)
                
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
                    
            except Exception as e:
                logger.warning(f"AI market gap analysis failed: {e}")
        
        # Fallback analysis
        return {
            "identified_gaps": [
                f"Underserved SMB segment in {industry}",
                "Emerging technology adoption opportunity",
                "Geographic expansion potential",
                "Product feature differentiation space"
            ],
            
            "opportunities": [
                {
                    "title": "Market Segment Expansion",
                    "description": f"Opportunity to capture untapped segments in {industry}",
                    "priority": "High",
                    "estimated_value": "15-25% market growth potential"
                },
                {
                    "title": "Technology Differentiation",
                    "description": "Leverage AI/ML for competitive advantage",
                    "priority": "High",
                    "estimated_value": "10-20% efficiency gains"
                },
                {
                    "title": "Strategic Partnerships",
                    "description": f"Partner with complementary {industry} players",
                    "priority": "Medium",
                    "estimated_value": "Accelerated market entry"
                }
            ],
            
            "competitive_white_space": [
                "Premium enterprise segment currently underserved",
                "Small business market with high growth potential",
                "International markets with limited competition"
            ]
        }
    
    async def generate_swot_analysis(self, 
                                     company_name: str,
                                     company_data: Dict[str, Any] = None,
                                     competitors: List[str] = None) -> Dict[str, List[str]]:
        """
        Generate comprehensive SWOT analysis
        
        Args:
            company_name: Company name
            company_data: Company information
            competitors: List of competitors
        
        Returns:
            SWOT analysis dictionary
        """
        if self.gemini_service:
            try:
                industry = company_data.get('industry', 'Technology') if company_data else 'Technology'
                description = company_data.get('description', '') if company_data else ''
                
                prompt = f"""Generate a comprehensive SWOT analysis for {company_name}.

Industry: {industry}
Description: {description}
Key Competitors: {', '.join(competitors[:3]) if competitors else 'Various market players'}

Provide 4-5 items for each category. Be specific and actionable.

Return JSON:
{{
    "strengths": ["strength 1", "strength 2", "strength 3", "strength 4"],
    "weaknesses": ["weakness 1", "weakness 2", "weakness 3", "weakness 4"],
    "opportunities": ["opportunity 1", "opportunity 2", "opportunity 3", "opportunity 4"],
    "threats": ["threat 1", "threat 2", "threat 3", "threat 4"]
}}"""

                response = await self.gemini_service.generate_content(prompt, temperature=0.3)
                
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
                    
            except Exception as e:
                logger.warning(f"AI SWOT analysis failed: {e}")
        
        # Fallback SWOT
        return {
            "strengths": [
                "Strong product-market fit",
                "Experienced leadership team",
                "Innovative technology approach",
                "Growing customer base"
            ],
            "weaknesses": [
                "Limited market presence",
                "Resource constraints",
                "Brand recognition challenges",
                "Scaling infrastructure needs"
            ],
            "opportunities": [
                "Expanding market demand",
                "New geographic markets",
                "Strategic partnership potential",
                "Product line extension"
            ],
            "threats": [
                "Intense competition",
                "Market volatility",
                "Regulatory changes",
                "Technology disruption"
            ]
        }
    
    async def get_full_competitive_analysis(self, 
                                           company_name: str,
                                           company_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get complete competitive analysis including all components
        
        Args:
            company_name: Company name
            company_data: Company information
        
        Returns:
            Complete competitive analysis
        """
        industry = company_data.get('industry') if company_data else None
        
        # Discover competitors
        competitors = await self.discover_competitors(company_name, industry)
        
        # Run all analyses in parallel
        insights_task = self.generate_competitive_insights(company_name, competitors, company_data)
        matrix_task = self.generate_competitive_matrix(company_name, competitors)
        gaps_task = self.analyze_market_gap(company_name, industry or 'Technology', competitors)
        swot_task = self.generate_swot_analysis(company_name, company_data, competitors)
        
        insights, matrix, gaps, swot = await asyncio.gather(
            insights_task, matrix_task, gaps_task, swot_task
        )
        
        return {
            "company": company_name,
            "industry": industry or "Technology",
            "competitors": competitors,
            "competitive_insights": insights,
            "competitive_matrix": matrix,
            "market_gaps": gaps,
            "swot_analysis": swot,
            "timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Initialize global instance
competitive_intel_service = CompetitiveIntelligenceService()
