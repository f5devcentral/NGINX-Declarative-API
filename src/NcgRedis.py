"""
Redis singleton
"""

import redis
import sys
import queue

from AppLogger import get_logger

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
        logger = get_logger()

        if cls._instance is None:
            try:
                cls.redis = redis.Redis(host, port)
                logger.info(f"Connecting to Redis at {host}:{port}")

                cls.redis.set('NGINX_Declarative_API','test')
                cls.redis.delete('NGINX_Declarative_API')

                # Asynchronous queue
                cls.asyncQueue = queue.Queue()
            except Exception as e:
                logger.error(f"Cannot connect to Redis on {host}:{port} : {e}")
                sys.exit(1)

            logger.info("Redis connected")
            cls._instance = super(cls, NcgRedis).__new__(cls)

        return cls._instance




