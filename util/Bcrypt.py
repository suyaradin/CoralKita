from werkzeug.security import check_password_hash, generate_password_hash


def hashPassword(plainTextPassword):
    """
    Hashes a plain text password using Werkzeug's PBKDF2-HMAC-SHA256.
    Store the returned string in the database — never store plain text.
    """
    return generate_password_hash(plainTextPassword)


def checkPassword(plainTextPassword, hashedPassword):
    """
    Verifies a plain text password against a stored hash.
    Returns True if they match, False otherwise.
    Invalid or malformed hashes return False to avoid crashing login.
    """
    if not hashedPassword:
        return False
    if isinstance(hashedPassword, bytes):
        hashedPassword = hashedPassword.decode("utf-8", errors="ignore")
    elif not isinstance(hashedPassword, str):
        return False
    return check_password_hash(hashedPassword, plainTextPassword)