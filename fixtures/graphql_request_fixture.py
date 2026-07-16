import json
import html
from .base_fixture import BaseRequestFixture

class GraphqlRequestFixture(BaseRequestFixture):
    """HTTP POST GraphQL fixture extending BaseRequestFixture."""
    
    def __init__(self) -> None:
        super().__init__()
        self._query: str = ""
        self._variables_json: str = "{}"
        
    def set_query(self, query: str) -> None:
        self._query = query
        
    def setQuery(self, query: str) -> None:
        self.set_query(query)
        
    def set_variables(self, variables: str) -> None:
        self._variables_json = variables
        
    def setVariables(self, variables: str) -> None:
        self.set_variables(variables)
        
    def execute(self) -> bool:
        # Construct the GraphQL payload structure
        unescaped_query = html.unescape(self._query)
        unescaped_vars = html.unescape(self._variables_json)
        
        try:
            vars_dict = json.loads(unescaped_vars) if unescaped_vars else {}
        except Exception:
            vars_dict = {}
            
        payload = {
            "query": unescaped_query,
            "variables": vars_dict
        }
        
        # Override the request body with the compiled GraphQL JSON payload
        self._body_json = json.dumps(payload)
        
        # Add custom Content-Type header if not specified
        if "Content-Type" not in self._custom_headers:
            self._custom_headers["Content-Type"] = "application/json"
            
        return self._make_request("POST")
