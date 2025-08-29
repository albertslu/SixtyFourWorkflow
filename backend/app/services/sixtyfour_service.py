"""
Sixtyfour API service for lead enrichment and email finding
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from loguru import logger

from core.config import settings


class SixtyfourAPIError(Exception):
    """Custom exception for Sixtyfour API errors"""
    pass


class SixtyfourService:
    """Service class for interacting with Sixtyfour API"""
    
    def __init__(self):
        self.base_url = settings.sixtyfour_base_url
        self.api_key = settings.sixtyfour_api_key
        self.org_id = settings.sixtyfour_org_id
        
        if not self.api_key:
            raise ValueError("SIXTYFOUR_API_KEY environment variable is required")
        
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an async HTTP request to Sixtyfour API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Making request to {url}")
                response = await client.post(url, headers=self.headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successful response from {endpoint}")
                    return result
                else:
                    error_msg = f"API request failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise SixtyfourAPIError(error_msg)
                    
            except httpx.TimeoutException:
                error_msg = f"Request to {endpoint} timed out"
                logger.error(error_msg)
                raise SixtyfourAPIError(error_msg)
            except httpx.RequestError as e:
                error_msg = f"Request error: {str(e)}"
                logger.error(error_msg)
                raise SixtyfourAPIError(error_msg)
    
    async def enrich_lead(self, lead_info: Dict[str, Any], struct: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Enrich lead information using Sixtyfour API
        
        Args:
            lead_info: Dictionary containing lead information (name, email, company, etc.)
            struct: Optional dictionary defining the structure of data to return
            
        Returns:
            Dictionary containing enriched lead data
        """
        if struct is None:
            struct = {
                "name": "Full name",
                "email": "Email address", 
                "company": "Company name",
                "title": "Job title",
                "linkedin": "LinkedIn URL",
                "website": "Company website",
                "location": "Location",
                "industry": "Industry",
                "phone": "Phone number",
                "education": "Educational background including university"
            }
        
        data = {
            "lead_info": lead_info,
            "struct": struct
        }
        
        logger.info(f"Enriching lead: {lead_info.get('name', 'Unknown')}")
        return await self._make_request("enrich-lead", data)
    
    async def find_email(self, person_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find email address for a person using Sixtyfour API
        
        Args:
            person_info: Dictionary containing person information (name, company, etc.)
            
        Returns:
            Dictionary containing found email information
        """
        # Note: The exact endpoint structure for find-email may need adjustment
        # based on actual Sixtyfour API documentation
        data = {
            "person_info": person_info,
            "struct": {
                "email": "Primary email address",
                "confidence": "Confidence score for the email",
                "source": "Source of the email information"
            }
        }
        
        logger.info(f"Finding email for: {person_info.get('name', 'Unknown')}")
        return await self._make_request("find-email", data)
    
    async def batch_enrich_leads(self, leads: List[Dict[str, Any]], struct: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Enrich multiple leads concurrently for better performance
        
        Args:
            leads: List of lead information dictionaries
            struct: Optional structure definition
            
        Returns:
            List of enriched lead data
        """
        logger.info(f"Starting batch enrichment of {len(leads)} leads")
        
        # Create tasks for concurrent execution
        tasks = [self.enrich_lead(lead, struct) for lead in leads]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        enriched_leads = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to enrich lead {i}: {str(result)}")
                # Return original lead data with error flag
                enriched_leads.append({
                    **leads[i],
                    "_enrichment_error": str(result),
                    "_enrichment_status": "failed"
                })
            else:
                enriched_leads.append({
                    **result,
                    "_enrichment_status": "success"
                })
        
        logger.info(f"Completed batch enrichment: {len([r for r in enriched_leads if r.get('_enrichment_status') == 'success'])} successful")
        return enriched_leads
    
    async def batch_find_emails(self, persons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find emails for multiple persons concurrently
        
        Args:
            persons: List of person information dictionaries
            
        Returns:
            List of email finding results
        """
        logger.info(f"Starting batch email finding for {len(persons)} persons")
        
        tasks = [self.find_email(person) for person in persons]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        email_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to find email for person {i}: {str(result)}")
                email_results.append({
                    **persons[i],
                    "_email_find_error": str(result),
                    "_email_find_status": "failed"
                })
            else:
                email_results.append({
                    **result,
                    "_email_find_status": "success"
                })
        
        logger.info(f"Completed batch email finding: {len([r for r in email_results if r.get('_email_find_status') == 'success'])} successful")
        return email_results


# Global service instance
sixtyfour_service = SixtyfourService()
