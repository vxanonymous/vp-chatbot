import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_password(password: str) -> str:
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password
    
    truncated = password_bytes[:72]
    while truncated and (truncated[-1] & 0x80) and not (truncated[-1] & 0x40):
        truncated = truncated[:-1]
    
    try:
        password = truncated.decode('utf-8')
    except UnicodeDecodeError:
        truncated = truncated[:-1]
        password = truncated.decode('utf-8', errors='ignore')
    
    final_bytes = password.encode('utf-8')
    if len(final_bytes) > 72:
        while len(password.encode('utf-8')) > 72 and len(password) > 0:
            password = password[:-1]
    
    final_check = password.encode('utf-8')
    if len(final_check) > 72:
        password = password[:36]
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify a plain text password against its hash
    truncated_password = _truncate_password(plain_password)
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Generate a secure hash for a password.
    # Uses bcrypt for secure password hashing.
    original_bytes = len(password.encode('utf-8'))
    truncated_password = _truncate_password(password)
    final_bytes = len(truncated_password.encode('utf-8'))
    
    if original_bytes > 72:
        logger.debug(f"Password truncated from {original_bytes} to {final_bytes} bytes")
    
    if final_bytes > 72:
        logger.warning(f"Password still {final_bytes} bytes after truncation, forcing to 36 chars")
        truncated_password = truncated_password[:36]
        final_bytes = len(truncated_password.encode('utf-8'))
    
    if final_bytes > 72:
        raise ValueError(f"Password cannot be truncated to <= 72 bytes (current: {final_bytes})")
    
    return pwd_context.hash(truncated_password)