"""
Redis singleton
"""

import redis
import sys
import queue


class NcgRedis(object):
    _instance = None
    redis
    asyncQueue = None

    # All submitted config declarations
    # For each entry key is the configUid
    # Value is:
    # - the threaded autosync job for autosync declarations
    # - "static" for declarations not in autosync mode
    declarationsList = {}

    def __new__(cls, host, port):
        if cls._instance is None:
            try:
                cls.redis = redis.Redis(host, port)
                print(f"Connecting to redis at {host}:{port}")

                cls.redis.set('NGINX_Declarative_API','test')
                cls.redis.delete('NGINX_Declarative_API')

                # Asynchronous queue
                cls.asyncQueue = queue.Queue()
            except Exception as e:
                print(f"Cannot connect to redis on {host}:{port} : {e}")
                sys.exit(1)

            cls._instance = super(cls, NcgRedis).__new__(cls)

        return cls._instance




