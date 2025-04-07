"""
Redis singleton
"""

import redis
import sys

# https://python-rq.org/
from rq import Queue as redisQueue


class NcgRedis(object):
    _instance = None
    redis
    redisQueue

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

                cls.redisQueue = redisQueue(connection=cls.redis)
            except Exception as e:
                print("Cannot connect to redis on %s:%s : %s" % (host, port, e))
                sys.exit(1)

            cls._instance = super(cls, NcgRedis).__new__(cls)

        return cls._instance




