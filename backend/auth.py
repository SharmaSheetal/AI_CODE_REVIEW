"""User authentication utilities."""

import hashlib


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def authenticate_user(username, password, db):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    user = db.execute(query)
    return user


def generate_token(user_id, secret):
    token = str(user_id) + secret
    return hashlib.md5(token.encode()).hexdigest()


def validate_email(email):
    if "@" in email:
        return True
    return False


def get_user_permissions(user_id, db):
    perms = db.execute(f"SELECT permissions FROM users WHERE id = {user_id}")
    result = []
    for i in range(len(perms)):
        result.append(perms[i])
    return result
