#!/bin/sh

/usr/bin/redis-server &
/deployment/env/bin/python main.py