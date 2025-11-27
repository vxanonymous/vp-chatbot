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
    original_bytes = len(password.encode('utf-8'))
    truncated_password = _truncate_password(password)
    
    password_bytes = truncated_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        while password_bytes and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
            password_bytes = password_bytes[:-1]
        truncated_password = password_bytes.decode('utf-8', errors='ignore')
        logger.warning(f"Password force-truncated to {len(truncated_password.encode('utf-8'))} bytes")
    
    final_check = truncated_password.encode('utf-8')
    if len(final_check) > 72:
        truncated_password = truncated_password[:18]
        logger.error(f"Password still too long after truncation, using first 18 chars")
    
    final_bytes = len(truncated_password.encode('utf-8'))
    if final_bytes > 72:
        logger.error(f"CRITICAL: Password still {final_bytes} bytes after all truncation attempts!")
        truncated_password = truncated_password[:18]
        final_bytes = len(truncated_password.encode('utf-8'))
        if final_bytes > 72:
            raise ValueError(f"Cannot truncate password to <= 72 bytes (final: {final_bytes})")
    
    if original_bytes > 72:
        logger.info(f"Password truncated from {original_bytes} to {final_bytes} bytes")
    
    final_verification = len(truncated_password.encode('utf-8'))
    if final_verification > 72:
        logger.error(f"CRITICAL: Password {final_verification} bytes > 72 before hash! Using emergency truncation.")
        truncated_password = truncated_password[:18]
        final_verification = len(truncated_password.encode('utf-8'))
    
    try:
        return pwd_context.hash(truncated_password)
    except ValueError as e:
        if "72 bytes" in str(e) or "longer than 72" in str(e).lower():
            logger.error(f"Bcrypt error: {e}. Original: {original_bytes} bytes, Final: {final_verification} bytes, String: {len(truncated_password)} chars")
            emergency_pwd = truncated_password[:18] if len(truncated_password) > 18 else truncated_password
            emergency_bytes = len(emergency_pwd.encode('utf-8'))
            logger.error(f"Emergency truncation to {emergency_bytes} bytes")
            return pwd_context.hash(emergency_pwd)
        raise