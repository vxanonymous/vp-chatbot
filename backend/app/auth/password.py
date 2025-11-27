import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_password(password: str) -> str:
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password
    
    truncated_bytes = password_bytes[:72]
    while truncated_bytes and (truncated_bytes[-1] & 0x80) and not (truncated_bytes[-1] & 0x40):
        truncated_bytes = truncated_bytes[:-1]
    
    try:
        result = truncated_bytes.decode('utf-8')
    except UnicodeDecodeError:
        truncated_bytes = truncated_bytes[:-1]
        result = truncated_bytes.decode('utf-8', errors='ignore')
    
    result_bytes = result.encode('utf-8')
    if len(result_bytes) > 72:
        while len(result.encode('utf-8')) > 72 and len(result) > 0:
            result = result[:-1]
    
    final_bytes = result.encode('utf-8')
    if len(final_bytes) > 72:
        result = result[:18]
    
    return result

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify a plain text password against its hash
    truncated_password = _truncate_password(plain_password)
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Generate a secure hash for a password.
    # Uses bcrypt for secure password hashing.
    truncated_password = _truncate_password(password)
    
    try:
        return pwd_context.hash(truncated_password)
    except ValueError as e:
        if "72 bytes" in str(e) or "longer than 72" in str(e).lower():
            logger.error(f"Bcrypt error: {e}. Password length: {len(truncated_password.encode('utf-8'))} bytes")
            emergency_pwd = truncated_password[:9]
            return pwd_context.hash(emergency_pwd)
        raise