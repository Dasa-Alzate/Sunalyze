import os
from dotenv import load_dotenv

load_dotenv()

_db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:0000@localhost/sunalyze')
print(f"[config] raw DATABASE_URL length={len(_db_url)} starts_with={_db_url[:20]!r}", flush=True)
if _db_url.startswith('mysql://'):
    _db_url = 'mysql+pymysql://' + _db_url[len('mysql://'):]

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300