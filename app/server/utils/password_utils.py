import secrets
import string

import bcrypt


def generate_random_password(length):
    # Combine all alphanumeric characters (letters and digits)
    characters = string.ascii_letters + string.digits

    return ''.join(secrets.choice(characters) for _ in range(length))


def check_password(provided_password: str, stored_password_hash: str) -> bool:
    """
    Check if a provided password matches a stored password hash using bcrypt.

    Args:
        provided_password (str): The provided password.
        stored_password_hash (str): The stored password hash.
    """
    if is_match := bcrypt.checkpw(provided_password.encode(), stored_password_hash.encode()):
        return is_match
    return False
