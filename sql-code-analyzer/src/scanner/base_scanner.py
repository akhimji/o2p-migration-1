from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

from models.sql_query import SQLQuery

class BaseScanner(ABC):
    """Abstract base class for all scanners"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    @abstractmethod
    def scan(self) -> List[SQLQuery]:
        """Scan files and extract SQL queries"""
        pass
    
    @abstractmethod
    def get_tech_stack_info(self) -> Dict[str, Any]:
        """Get information about the tech stack"""
        pass