"""
auth.py - Google Application Default Credentials (ADC) Authentication Provider for UVT
"""
import logging
from typing import Optional, Tuple
import google.auth
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger("UVT.Auth")

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/generative-language"
]

class ADCAuthProvider:
    """
    Manages Google Application Default Credentials (ADC), generating
    and refreshing short-lived OAuth 2.0 access tokens.
    """
    def __init__(self, scopes: Optional[list[str]] = None, quota_project_id: Optional[str] = None):
        self.scopes = scopes or DEFAULT_SCOPES
        self.quota_project_id = quota_project_id
        self._credentials: Optional[Credentials] = None
        self._project_id: Optional[str] = None

    def initialize(self) -> Tuple[str, str]:
        """
        Loads Google Application Default Credentials from system environment or
        ~/.config/gcloud/application_default_credentials.json.
        """
        logger.info("Initializing Google Application Default Credentials (ADC)...")
        self._credentials, self._project_id = google.auth.default(
            scopes=self.scopes,
            quota_project_id=self.quota_project_id
        )
        
        # Initial token generation
        self.refresh_token()
        logger.info(f"ADC initialized successfully. Active Project: {self._project_id}")
        return self.get_access_token(), self.get_project_id()

    def refresh_token(self) -> str:
        """Refreshes the OAuth 2.0 access token using a Google auth Request."""
        if not self._credentials:
            raise RuntimeError("Credentials not initialized. Call initialize() first.")
        
        req = Request()
        self._credentials.refresh(req)
        logger.debug("Successfully refreshed Google ADC access token.")
        return self._credentials.token

    def get_access_token(self) -> str:
        """Returns the current valid access token, auto-refreshing if expired or missing."""
        if not self._credentials:
            self.initialize()
        
        if not self._credentials.valid:
            return self.refresh_token()
        
        return self._credentials.token

    def get_project_id(self) -> str:
        """Returns the active Google Cloud project ID."""
        return self._project_id or self.quota_project_id or "mehdigolzari"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    provider = ADCAuthProvider()
    token, proj = provider.initialize()
    print(f"Project ID: {proj}")
    print(f"Token Prefix: {token[:20]}... (Length: {len(token)})")
