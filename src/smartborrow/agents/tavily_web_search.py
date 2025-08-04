"""
Tavily Web Search Tool for SmartBorrow

This module provides web search capabilities using Tavily API to enhance
SmartBorrow with real-time information retrieval.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import hashlib
import time

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

@dataclass
class WebSearchResult:
    """Structured web search result"""
    title: str
    url: str
    content: str
    source_type: str
    credibility_score: float
    timestamp: datetime
    search_query: str

class WebSearchCache:
    """Cache for web search results to reduce API calls"""
    
    def __init__(self, cache_duration_hours: int = 24):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_file = Path("data/web_search_cache.json")
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached web search results")
        except Exception as e:
            logger.warning(f"Error loading web search cache: {e}")
            self.cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to file"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving web search cache: {e}")
    
    def _generate_cache_key(self, query: str, search_type: str = "basic") -> str:
        """Generate cache key for query"""
        key_data = {
            "query": query.lower().strip(),
            "search_type": search_type,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, query: str, search_type: str = "basic") -> Optional[List[WebSearchResult]]:
        """Get cached result if available and not expired"""
        cache_key = self._generate_cache_key(query, search_type)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cached_time = datetime.fromisoformat(cached_data["timestamp"])
            
            if datetime.now() - cached_time < self.cache_duration:
                # Convert back to WebSearchResult objects
                results = []
                for result_data in cached_data["results"]:
                    result = WebSearchResult(
                        title=result_data["title"],
                        url=result_data["url"],
                        content=result_data["content"],
                        source_type=result_data["source_type"],
                        credibility_score=result_data["credibility_score"],
                        timestamp=datetime.fromisoformat(result_data["timestamp"]),
                        search_query=result_data["search_query"]
                    )
                    results.append(result)
                return results
        
        return None
    
    def set(self, query: str, results: List[WebSearchResult], search_type: str = "basic") -> None:
        """Cache search results"""
        cache_key = self._generate_cache_key(query, search_type)
        
        # Convert to serializable format
        cached_results = []
        for result in results:
            cached_result = {
                "title": result.title,
                "url": result.url,
                "content": result.content,
                "source_type": result.source_type,
                "credibility_score": result.credibility_score,
                "timestamp": result.timestamp.isoformat(),
                "search_query": result.search_query
            }
            cached_results.append(cached_result)
        
        self.cache[cache_key] = {
            "results": cached_results,
            "timestamp": datetime.now().isoformat()
        }
        
        self._save_cache()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "expired_entries": 0,  # Simplified for now
            "active_entries": len(self.cache)
        }

class TavilyWebSearchTool(BaseTool):
    """Web search tool using Tavily API for real-time information"""
    
    name: str = "tavily_web_search"
    description: str = "Search the web for current information about student loans, financial aid, scholarships, and educational policies"
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 enable_caching: bool = True,
                 cache_duration_hours: int = 24,
                 max_results: int = 5):
        super().__init__()
        
        # Store configuration as instance variables
        self._api_key = api_key or os.getenv("TAVILY_API_KEY")
        self._enable_caching = enable_caching
        self._cache_duration_hours = cache_duration_hours
        self._max_results = max_results
        
        # Initialize client
        self._client = None
        if self._api_key:
            try:
                self._client = TavilyClient(api_key=self._api_key)
                logger.info("Tavily client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Tavily client: {e}")
        else:
            logger.warning("TAVILY_API_KEY not found. Web search will be disabled.")
        
        # Initialize cache
        self._cache = WebSearchCache(cache_duration_hours) if enable_caching else None
        
        # Search templates for different use cases
        self._search_templates = {
            "interest_rates": "current federal student loan interest rates {year}",
            "school_costs": "{school_name} tuition cost of attendance {year}",
            "policy_updates": "recent changes FAFSA student loan forgiveness {year}",
            "scholarships": "{criteria} scholarships {year} application deadline",
            "deadlines": "FAFSA deadline {year} financial aid application",
            "school_comparison": "{school1} vs {school2} financial aid cost comparison"
        }
    
    def _run(self, query: str, search_type: str = "basic") -> str:
        """Execute web search"""
        try:
            # Check cache first
            if self._enable_caching and self._cache:
                cached_results = self._cache.get(query, search_type)
                if cached_results:
                    logger.info(f"Using cached web search results for: {query}")
                    return self._format_results(cached_results)
            
            # Perform web search
            if not self._client:
                return "Web search is not available. Please configure TAVILY_API_KEY."
            
            logger.info(f"Performing web search for: {query}")
            
            # Execute search
            search_results = self._client.search(
                query=query,
                search_depth="basic" if search_type == "basic" else "advanced",
                max_results=self._max_results
            )
            
            # Process and structure results
            results = self._process_search_results(search_results, query)
            
            # Cache results
            if self._enable_caching and self._cache:
                self._cache.set(query, results, search_type)
            
            return self._format_results(results)
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return f"Error performing web search: {e}"
    
    def _process_search_results(self, search_results: Dict[str, Any], query: str) -> List[WebSearchResult]:
        """Process raw search results into structured format"""
        results = []
        
        try:
            for result in search_results.get("results", []):
                # Calculate credibility score based on source
                credibility_score = self._calculate_credibility_score(result.get("url", ""))
                
                web_result = WebSearchResult(
                    title=result.get("title", "No title"),
                    url=result.get("url", ""),
                    content=result.get("content", ""),
                    source_type=self._categorize_source(result.get("url", "")),
                    credibility_score=credibility_score,
                    timestamp=datetime.now(),
                    search_query=query
                )
                results.append(web_result)
        
        except Exception as e:
            logger.error(f"Error processing search results: {e}")
        
        return results
    
    def _calculate_credibility_score(self, url: str) -> float:
        """Calculate credibility score for a source"""
        url_lower = url.lower()
        
        # High credibility sources
        high_credibility = [
            "studentaid.gov", "ed.gov", "fafsa.gov", "irs.gov",
            "whitehouse.gov", "congress.gov", "supremecourt.gov"
        ]
        
        # Medium credibility sources
        medium_credibility = [
            "harvard.edu", "stanford.edu", "mit.edu", "berkeley.edu",
            "nytimes.com", "washingtonpost.com", "wsj.com",
            "forbes.com", "bloomberg.com", "reuters.com"
        ]
        
        # Check for high credibility
        for source in high_credibility:
            if source in url_lower:
                return 0.9
        
        # Check for medium credibility
        for source in medium_credibility:
            if source in url_lower:
                return 0.7
        
        # Default credibility
        return 0.5
    
    def _categorize_source(self, url: str) -> str:
        """Categorize the source type"""
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in [".gov", "government"]):
            return "government"
        elif any(domain in url_lower for domain in [".edu", "university", "college"]):
            return "educational"
        elif any(domain in url_lower for domain in [".org", "foundation"]):
            return "organization"
        elif any(domain in url_lower for domain in [".com", "business"]):
            return "commercial"
        else:
            return "other"
    
    def _format_results(self, results: List[WebSearchResult]) -> str:
        """Format search results for agent consumption"""
        if not results:
            return "No web search results found."
        
        formatted_results = []
        
        for i, result in enumerate(results[:self._max_results], 1):
            # Truncate content for readability
            content = result.content[:300] + "..." if len(result.content) > 300 else result.content
            
            formatted_result = f"""
{i}. {result.title}
   URL: {result.url}
   Source: {result.source_type} (Credibility: {result.credibility_score:.1f})
   Content: {content}
"""
            formatted_results.append(formatted_result)
        
        summary = f"Found {len(results)} web search results. "
        summary += f"Sources include: {', '.join(set(r.source_type for r in results))}"
        
        return summary + "\n\n" + "\n".join(formatted_results)
    
    def search_interest_rates(self, year: str = "2024-2025") -> str:
        """Specialized search for current interest rates"""
        query = self._search_templates["interest_rates"].format(year=year)
        return self._run(query, "basic")
    
    def search_school_costs(self, school_name: str, year: str = "2024-2025") -> str:
        """Specialized search for school-specific costs"""
        query = self._search_templates["school_costs"].format(school_name=school_name, year=year)
        return self._run(query, "basic")
    
    def search_policy_updates(self, year: str = "2024") -> str:
        """Specialized search for policy updates"""
        query = self._search_templates["policy_updates"].format(year=year)
        return self._run(query, "advanced")
    
    def search_scholarships(self, criteria: str, year: str = "2024-2025") -> str:
        """Specialized search for scholarships"""
        query = self._search_templates["scholarships"].format(criteria=criteria, year=year)
        return self._run(query, "basic")
    
    def search_deadlines(self, year: str = "2024-2025") -> str:
        """Specialized search for application deadlines"""
        query = self._search_templates["deadlines"].format(year=year)
        return self._run(query, "basic")
    
    def search_school_comparison(self, school1: str, school2: str) -> str:
        """Specialized search for school comparisons"""
        query = self._search_templates["school_comparison"].format(school1=school1, school2=school2)
        return self._run(query, "advanced")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._cache:
            return {"caching_enabled": False}
        
        return {
            "caching_enabled": True,
            "cache_size": len(self._cache.cache),
            "cache_duration_hours": self._cache.cache_duration.total_seconds() / 3600
        }

def create_tavily_web_search_tool(api_key: Optional[str] = None,
                                 enable_caching: bool = True,
                                 cache_duration_hours: int = 24,
                                 max_results: int = 5) -> TavilyWebSearchTool:
    """Factory function to create Tavily web search tool"""
    return TavilyWebSearchTool(
        api_key=api_key,
        enable_caching=enable_caching,
        cache_duration_hours=cache_duration_hours,
        max_results=max_results
    ) 