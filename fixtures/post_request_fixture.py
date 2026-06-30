from .base_fixture import BaseRequestFixture

class PostRequestFixture(BaseRequestFixture):
    """HTTP POST fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("POST")
