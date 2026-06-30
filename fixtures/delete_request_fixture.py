from .base_fixture import BaseRequestFixture

class DeleteRequestFixture(BaseRequestFixture):
    """HTTP DELETE fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("DELETE")
