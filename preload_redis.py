import fileinput
import redis
import datetime
import sys
import os
import json

r = redis.from_url(os.environ.get("REDIS_URL"))

data = json.load(sys.stdin)
for entry in data:
    r.hset('machines', entry['datacenter'] + ':' + entry['machine'], entry['lastseen'])
