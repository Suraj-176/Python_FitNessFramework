from .base_fixture import BaseRequestFixture

class HeadRequestFixture(BaseRequestFixture):
    """HTTP HEAD fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("HEAD")
