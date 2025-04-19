import requests
import time
from typing import List, Dict, Any, Optional

class SolvedAcAPI:
    BASE_URL = "https://solved.ac/api/v3"
    
    @staticmethod
    def get_problem_by_id(problem_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single problem's details by its ID
        
        Args:
            problem_id: The Baekjoon problem ID
            
        Returns:
            Problem data or None if not found
        """
        url = f"{SolvedAcAPI.BASE_URL}/problem/show"
        params = {"problemId": problem_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching problem {problem_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_problems_by_ids(problem_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple problems by IDs using the lookup endpoint
        
        Args:
            problem_ids: List of Baekjoon problem IDs
            
        Returns:
            List of problem data dictionaries
        """
        url = f"{SolvedAcAPI.BASE_URL}/problem/lookup"
        
        # Convert list to comma-separated string
        problemIds = ",".join(problem_ids)
        params = {"problemIds": problemIds}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error fetching problems: {str(e)}")
            return []
    
    @staticmethod
    def get_problems_by_tier(tier: int, page: int = 1, sort: str = "id", direction: str = "asc") -> List[Dict[str, Any]]:
        """
        Fetch problems filtered by tier
        
        Args:
            tier: Problem difficulty tier (0-30)
            page: Page number for pagination
            sort: Field to sort by (id, level, title, solved, etc.)
            direction: Sort direction (asc or desc)
            
        Returns:
            List of problem data dictionaries
        """
        url = f"{SolvedAcAPI.BASE_URL}/problem/search"
        params = {
            "query": f"tier:{tier}",
            "page": page,
            "sort": sort,
            "direction": direction
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"Error fetching problems by tier {tier}: {str(e)}")
            return []
    
    @staticmethod
    def get_problem_tags(problem_id: str) -> List[Dict[str, Any]]:
        """
        Get the tags for a specific problem
        
        Args:
            problem_id: The Baekjoon problem ID
            
        Returns:
            List of tag dictionaries
        """
        problem_data = SolvedAcAPI.get_problem_by_id(problem_id)
        if problem_data and "tags" in problem_data:
            return problem_data["tags"]
        return [] 