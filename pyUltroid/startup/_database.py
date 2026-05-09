# Ultroid - UserBot
# Copyright (C) 2021-2026 TeamUltroid

import ast
import os
import sys

from .. import run_as_module
from . import *

if run_as_module:
    from ..configs import Var

Redis = MongoClient = psycopg2 = Database = None
if Var.REDIS_URI or Var.REDISHOST:
    try:
        from redis import Redis
    except ImportError:
        os.system(f"{sys.executable} -m pip install -q redis hiredis")
        from redis import Redis

class _BaseDatabase:
    def __init__(self, *args, **kwargs):
        self._cache = {}

    def get_key(self, key):
        if key in self._cache:
            return self._cache[key]
        value = self._get_data(key)
        self._cache.update({key: value})
        return value

    def _get_data(self, key=None, data=None):
        if key:
            data = self.get(str(key))
        if data and isinstance(data, str):
            try:
                data = ast.literal_eval(data)
            except:
                pass
        return data

    def set_key(self, key, value, cache_only=False):
        value = self._get_data(data=value)
        self._cache[key] = value
        if cache_only: return
        return self.set(str(key), str(value))

    def del_key(self, key):
        if key in self._cache: del self._cache[key]
        self.delete(key)
        return True

class RedisDB(_BaseDatabase):
    def __init__(self, db_instance, *args, **kwargs):
        self.db = db_instance
        self.set = self.db.set
        self.get = self.db.get
        self.keys = self.db.keys
        self.delete = self.db.delete
        super().__init__()

    @property
    def name(self): return "Redis"
    
    def ping(self):
        try:
            return self.db.ping()
        except:
            return False

def UltroidDB():
    from .. import HOSTED_ON
    # --- UPSTASH SSL FIX ---
    REDIS_URL = Var.REDIS_URI or Var.REDISHOST
    
    # Force SSL for Upstash if needed
    if REDIS_URL and "upstash.io" in REDIS_URL and REDIS_URL.startswith("redis://"):
        REDIS_URL = REDIS_URL.replace("redis://", "rediss://")

    try:
        if Redis:
            if REDIS_URL and (REDIS_URL.startswith("redis") or REDIS_URL.startswith("rediss")):
                # Adding SSL Check & Health Check
                db = Redis.from_url(
                    REDIS_URL, 
                    decode_responses=True, 
                    socket_timeout=15,
                    retry_on_timeout=True,
                    health_check_interval=30,
                    ssl_cert_reqs=None # Trust Upstash SSL
                )
                return RedisDB(db_instance=db)
            
            db = Redis(host=REDIS_URL, port=Var.REDISPORT, password=Var.REDIS_PASSWORD, decode_responses=True)
            return RedisDB(db_instance=db)
        
        # Fallback to local
        from . import LocalDB
        return LocalDB()
    except Exception as err:
        LOGS.exception(err)
        sys.exit(1)
