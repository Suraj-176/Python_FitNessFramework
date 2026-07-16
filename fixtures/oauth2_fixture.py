from .auth_fixture import AuthFixture

class Oauth2Fixture(AuthFixture):
    """
    Dedicated Python SLIM Decision Table fixture for OAuth2 authentication flows.
    Inherits from AuthFixture and defaults to client_credentials grant type.
    """
    def __init__(self) -> None:
        super().__init__()
        self._grant_type = "client_credentials"  # Default to standard client credentials flow
