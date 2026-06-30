from .base_fixture import BaseRequestFixture

class PatchRequestFixture(BaseRequestFixture):
    """HTTP PATCH fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("PATCH")
