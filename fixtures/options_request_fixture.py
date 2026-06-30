from .base_fixture import BaseRequestFixture

class OptionsRequestFixture(BaseRequestFixture):
    """HTTP OPTIONS fixture extending BaseRequestFixture."""
    
    def execute(self) -> bool:
        return self._make_request("OPTIONS")
