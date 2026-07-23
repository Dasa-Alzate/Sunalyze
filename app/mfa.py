
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

DIGITS = 6
PERIOD = 30
SECRET_BYTES = 20
RECOVERY_CODE_COUNT = 10
_PBKDF2_ITERATIONS = 120000


def _fernet():
    configured = current_app.config.get('MFA_ENC_KEY')
    if configured:
        key = configured.encode('ascii') if isinstance(configured, str) else configured
    else:
        secret_key = current_app.config['SECRET_KEY']
        material = secret_key.encode('utf-8') if isinstance(secret_key, str) else secret_key
        key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(key)


def encrypt_secret(plaintext):
    return _fernet().encrypt(plaintext.encode('utf-8')).decode('ascii')


def decrypt_secret(token):
    if not token:
        return None
    raw = token.encode('ascii') if isinstance(token, str) else token
    try:
        return _fernet().decrypt(raw).decode('utf-8')
    except (InvalidToken, ValueError, TypeError):
        return None


def generate_secret():
    raw = secrets.token_bytes(SECRET_BYTES)
    return base64.b32encode(raw).decode('ascii').rstrip('=')


def _b32decode(secret):
    normalized = secret.strip().replace(' ', '').upper()
    padding = (-len(normalized)) % 8
    return base64.b32decode(normalized + ('=' * padding))


def hotp(secret, counter, digits=DIGITS):
    key = _b32decode(secret)
    msg = struct.pack('>Q', counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0f
    code = (
        (digest[offset] & 0x7f) << 24
        | (digest[offset + 1] & 0xff) << 16
        | (digest[offset + 2] & 0xff) << 8
        | (digest[offset + 3] & 0xff)
    )
    return str(code % (10 ** digits)).zfill(digits)


def totp(secret, at=None, period=PERIOD, digits=DIGITS):
    moment = int(time.time() if at is None else at)
    counter = moment // period
    return hotp(secret, counter, digits=digits)


def verify_totp(secret, code, at=None, window=1, period=PERIOD, digits=DIGITS):
    if not code or not code.strip().isdigit():
        return False
    candidate = code.strip()
    moment = int(time.time() if at is None else at)
    counter = moment // period
    for drift in range(-window, window + 1):
        expected = hotp(secret, counter + drift, digits=digits)
        if hmac.compare_digest(expected, candidate):
            return True
    return False


def provisioning_uri(secret, account_name, issuer):
    label = quote(f'{issuer}:{account_name}')
    params = (
        f'secret={secret}'
        f'&issuer={quote(issuer)}'
        f'&algorithm=SHA1'
        f'&digits={DIGITS}'
        f'&period={PERIOD}'
    )
    return f'otpauth://totp/{label}?{params}'


def generate_recovery_codes(count=RECOVERY_CODE_COUNT):
    return [f'{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}'
            for _ in range(count)]


def hash_recovery_code(code):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', code.strip().encode('utf-8'), salt,
                                 _PBKDF2_ITERATIONS)
    return f'pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}'


def verify_recovery_code(code, stored):
    try:
        algo, iterations, salt_hex, digest_hex = stored.split('$')
    except (ValueError, AttributeError):
        return False
    if algo != 'pbkdf2_sha256':
        return False
    digest = hashlib.pbkdf2_hmac('sha256', code.strip().encode('utf-8'),
                                 bytes.fromhex(salt_hex), int(iterations))
    return hmac.compare_digest(digest.hex(), digest_hex)
