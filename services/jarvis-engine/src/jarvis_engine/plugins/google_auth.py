import os
import urllib.parse
import httpx
from .credential_store import store_credential, get_credential
from ..core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8765/plugins/google/callback"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]

def init_google_oauth():
    """OAuth init function. Tokens are stored when received; nothing to initialize here."""
    pass

def get_authorization_url() -> str:
    """Builds the Google OAuth URL."""
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        raise ValueError("Google Client ID not configured.")
        
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    
    query = urllib.parse.urlencode(params)
    return f"{GOOGLE_AUTH_URL}?{query}"

def handle_callback(code: str) -> None:
    """Exchanges code for tokens and stores them."""
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials missing.")
        
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=30.0)
    response.raise_for_status()
    
    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    if access_token:
        store_credential("google", "access_token", access_token)
    if refresh_token:
        store_credential("google", "refresh_token", refresh_token)

def get_valid_token() -> str:
    """Returns access token, refreshing if necessary."""
    access_token = get_credential("google", "access_token")
    refresh_token = get_credential("google", "refresh_token")
    
    if not access_token:
        raise ValueError("No access token available.")
        
    try:
        # Check validity (Tokeninfo is fast)
        resp = httpx.get(
            f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}", 
            timeout=10.0
        )
        if resp.status_code == 200:
            return access_token
    except Exception:
        pass
        
    # Refresh
    if not refresh_token:
        raise ValueError("Token expired and no refresh token available.")
        
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=30.0)
    response.raise_for_status()
    
    new_tokens = response.json()
    new_access = new_tokens.get("access_token")
    if new_access:
        store_credential("google", "access_token", new_access)
        return new_access
        
    raise ValueError("Failed to refresh token.")
