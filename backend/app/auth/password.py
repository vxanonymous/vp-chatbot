import logging
import bcrypt

logger = logging.getLogger(__name__)

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
    password_bytes = truncated_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    # Generate a secure hash for a password.
    # Uses bcrypt for secure password hashing.
    truncated_password = _truncate_password(password)
    password_bytes = truncated_password.encode('utf-8')
    
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')