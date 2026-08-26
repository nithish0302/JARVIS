import httpx
from email.message import EmailMessage
import base64
from .google_auth import get_valid_token

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

def get_gmail_headers() -> dict:
    token = get_valid_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def parse_message_payload(payload: dict) -> tuple[str, str, str]:
    headers = payload.get("headers", [])
    subject = ""
    sender = ""
    date = ""
    for header in headers:
        name = header.get("name", "").lower()
        if name == "subject":
            subject = header.get("value", "")
        elif name == "from":
            sender = header.get("value", "")
        elif name == "date":
            date = header.get("value", "")
    return subject, sender, date

def get_unread_emails(max_results: int = 5) -> list[dict]:
    headers = get_gmail_headers()
    
    # Query for unread emails
    params = {
        "q": "is:unread",
        "maxResults": max_results
    }
    
    resp = httpx.get(f"{GMAIL_API_BASE}/messages", headers=headers, params=params, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    
    messages = data.get("messages", [])
    results = []
    
    for msg in messages:
        msg_id = msg["id"]
        # Fetch details
        detail_resp = httpx.get(f"{GMAIL_API_BASE}/messages/{msg_id}?format=metadata", headers=headers, timeout=30.0)
        detail_resp.raise_for_status()
        detail_data = detail_resp.json()
        
        subject, sender, date = parse_message_payload(detail_data.get("payload", {}))
        
        results.append({
            "message_id": msg_id,
            "subject": subject,
            "sender": sender,
            "snippet": detail_data.get("snippet", ""),
            "date": date
        })
        
    return results

def search_emails(query: str, max_results: int = 5) -> list[dict]:
    headers = get_gmail_headers()
    
    params = {
        "q": query,
        "maxResults": max_results
    }
    
    resp = httpx.get(f"{GMAIL_API_BASE}/messages", headers=headers, params=params, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    
    messages = data.get("messages", [])
    results = []
    
    for msg in messages:
        msg_id = msg["id"]
        detail_resp = httpx.get(f"{GMAIL_API_BASE}/messages/{msg_id}?format=metadata", headers=headers, timeout=30.0)
        detail_resp.raise_for_status()
        detail_data = detail_resp.json()
        
        subject, sender, date = parse_message_payload(detail_data.get("payload", {}))
        
        results.append({
            "message_id": msg_id,
            "subject": subject,
            "sender": sender,
            "snippet": detail_data.get("snippet", ""),
            "date": date
        })
        
    return results

def send_email(to: str, subject: str, body: str) -> bool:
    # NEVER called directly without confirm_action in the backend
    headers = get_gmail_headers()
    
    message = EmailMessage()
    message.set_content(body)
    message["To"] = to
    message["Subject"] = subject
    
    # URL-safe base64 encoding without padding
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode().strip("=")
    
    payload = {
        "raw": encoded_message
    }
    
    resp = httpx.post(f"{GMAIL_API_BASE}/messages/send", headers=headers, json=payload, timeout=30.0)
    resp.raise_for_status()
    
    return True

def get_email_detail(message_id: str) -> dict:
    headers = get_gmail_headers()
    
    resp = httpx.get(f"{GMAIL_API_BASE}/messages/{message_id}?format=full", headers=headers, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    
    subject, sender, date = parse_message_payload(data.get("payload", {}))
    
    return {
        "message_id": message_id,
        "subject": subject,
        "sender": sender,
        "date": date,
        "snippet": data.get("snippet", ""),
        "full_content": "Detailed parsing omitted. See payload for details."
    }
