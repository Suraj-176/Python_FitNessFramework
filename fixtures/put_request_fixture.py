from .base_fixture import BaseRequestFixture

class PutRequestFixture(BaseRequestFixture):
    """HTTP PUT fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("PUT")
