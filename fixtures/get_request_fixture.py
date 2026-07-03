from .base_fixture import BaseRequestFixture

class GetRequestFixture(BaseRequestFixture):
    """HTTP GET fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("GET")
