from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_password(password: str) -> str:
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        truncated = password_bytes[:72]
        while truncated and (truncated[-1] & 0x80) and not (truncated[-1] & 0x40):
            truncated = truncated[:-1]
        password = truncated.decode('utf-8', errors='ignore')
        final_bytes = password.encode('utf-8')
        if len(final_bytes) > 72:
            while len(password.encode('utf-8')) > 72 and len(password) > 0:
                password = password[:-1]
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify a plain text password against its hash
    truncated_password = _truncate_password(plain_password)
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Generate a secure hash for a password.
    # Uses bcrypt for secure password hashing.
    truncated_password = _truncate_password(password)
    return pwd_context.hash(truncated_password)