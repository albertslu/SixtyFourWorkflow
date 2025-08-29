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
        
        # Add organization ID if provided
        if self.org_id:
            self.headers["x-org-id"] = self.org_id
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an async HTTP request to Sixtyfour API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Increase timeout for API calls that may take longer
        # Enrich-lead can take 2-3 minutes per request
        timeout = httpx.Timeout(180.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                logger.info(f"Making request to {url} with data: {data}")
                response = await client.post(url, headers=self.headers, json=data)
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successful response from {endpoint}: {result}")
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
                "name": "The individual's full name",
                "email": "The individual's email address",
                "phone": "The individual's phone number",
                "company": "The company the individual is associated with",
                "title": "The individual's job title",
                "linkedin": "LinkedIn URL for the person",
                "website": "Company website URL",
                "location": "The individual's location and/or company location",
                "industry": "Industry the person operates in",
                "github_url": "URL for their GitHub profile",
                "github_notes": "Take detailed notes on their GitHub profile."
            }
        
        data = {
            "lead_info": lead_info,
            "struct": struct
        }
        
        logger.info(f"Enriching lead: {lead_info.get('name', 'Unknown')}")
        return await self._make_request("enrich-lead", data)
    
    async def enrich_lead_async(self, lead_info: Dict[str, Any], struct: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Start an async lead enrichment job using Sixtyfour API
        
        Args:
            lead_info: Dictionary containing lead information (name, email, company, etc.)
            struct: Optional dictionary defining the structure of data to return
            
        Returns:
            Dictionary containing task_id and status for async job tracking
        """
        if struct is None:
            struct = {
                "name": "The individual's full name",
                "email": "The individual's email address",
                "phone": "The individual's phone number",
                "company": "The company the individual is associated with",
                "title": "The individual's job title",
                "linkedin": "LinkedIn URL for the person",
                "website": "Company website URL",
                "location": "The individual's location and/or company location",
                "industry": "Industry the person operates in",
                "github_url": "URL for their GitHub profile",
                "github_notes": "Take detailed notes on their GitHub profile."
            }
        
        data = {
            "lead_info": lead_info,
            "struct": struct
        }
        
        logger.info(f"Starting async enrichment for lead: {lead_info.get('name', 'Unknown')}")
        return await self._make_request("enrich-lead-async", data)
    
    async def get_job_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of an async job
        
        Args:
            task_id: The task ID returned from async endpoint
            
        Returns:
            Dictionary containing job status and results (if completed)
        """
        url = f"{self.base_url}/job-status/{task_id}"
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                logger.info(f"Checking job status for task: {task_id}")
                response = await client.get(url, headers=self.headers)
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Job status response: {result}")
                    return result
                else:
                    error_msg = f"Job status request failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise SixtyfourAPIError(error_msg)
                    
            except httpx.TimeoutException:
                error_msg = f"Request to job-status/{task_id} timed out"
                logger.error(error_msg)
                raise SixtyfourAPIError(error_msg)
            except httpx.RequestError as e:
                error_msg = f"Request error: {str(e)}"
                logger.error(error_msg)
                raise SixtyfourAPIError(error_msg)
    
    async def find_email(self, person_info: Dict[str, Any], bruteforce: bool = None, only_company_emails: bool = None) -> Dict[str, Any]:
        """
        Find email address for a person using Sixtyfour API
        
        Args:
            person_info: Dictionary containing person information (name, company, etc.)
            bruteforce: Optional - Whether to use brute force to find the email
            only_company_emails: Optional - When True, only return company email addresses
            
        Returns:
            Dictionary containing found email information
        """
        # Start with the basic required format
        data = {
            "lead": person_info
        }
        
        # Add optional parameters only if specified
        if bruteforce is not None:
            data["bruteforce"] = bruteforce
        if only_company_emails is not None:
            data["only_company_emails"] = only_company_emails
        
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
                # Extract structured_data from the API response and merge with original lead
                enriched_lead = {**leads[i]}
                
                if "structured_data" in result:
                    # Merge the structured data from the API response
                    enriched_lead.update(result["structured_data"])
                
                # Add additional metadata from the API response
                if "notes" in result:
                    enriched_lead["_enrichment_notes"] = result["notes"]
                if "confidence_score" in result:
                    enriched_lead["_confidence_score"] = result["confidence_score"]
                if "findings" in result:
                    enriched_lead["_findings"] = result["findings"]
                if "references" in result:
                    enriched_lead["_references"] = result["references"]
                
                enriched_lead["_enrichment_status"] = "success"
                enriched_leads.append(enriched_lead)
        
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
                # Process find-email API response
                email_result = {**persons[i]}
                
                if isinstance(result, dict):
                    # Handle the email field which is an array of tuples: [email, status, type]
                    if "email" in result and result["email"]:
                        emails = result["email"]
                        if emails and len(emails) > 0:
                            # Get the first email (primary email)
                            primary_email = emails[0]
                            if len(primary_email) >= 3:
                                email_result["email"] = primary_email[0]  # Email address
                                email_result["_email_status"] = primary_email[1]  # OK/UNKNOWN
                                email_result["_email_type"] = primary_email[2]  # COMPANY/PERSONAL
                            
                            # Store all found emails for reference
                            email_result["_all_emails"] = emails
                    
                    # Copy other fields from the response (name, company, title, etc.)
                    for key, value in result.items():
                        if key not in ["email"] and not key.startswith("_"):
                            # Only update if the field wasn't already in the original data
                            if key not in email_result:
                                email_result[key] = value
                
                email_result["_email_find_status"] = "success"
                email_results.append(email_result)
        
        logger.info(f"Completed batch email finding: {len([r for r in email_results if r.get('_email_find_status') == 'success'])} successful")
        return email_results


# Global service instance
sixtyfour_service = SixtyfourService()
