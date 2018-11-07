from flask import Flask
import redis
import json
import os

r = redis.from_url(os.environ.get("REDIS_URL"))

app = Flask(__name__)

@app.route('/machines', methods=['GET'])
def machines():
    result = r.hgetall('machines')
    values = list()
    for entry, lastseen in result.iteritems():
        datacenter, _, machine = entry.partition(':')
        values.append({'datacenter': datacenter, 'machine': machine, 'lastseen': lastseen})
    return (json.dumps(values, indent=2), 200, {'content-type': 'application/json'});

@app.route('/machines/<machine>', methods=['GET'])
def machine_by_id(machine):
    lastseen = r.hget('machines', machine)
    if not lastseen:
        return ('unknown machine', 404, {})
    return (json.dumps(lastseen), 200, {'content-type': 'application/json'});

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

