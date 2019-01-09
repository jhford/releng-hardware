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
        info = {
                'datacenter': datacenter,
                'machine': machine,
                'lastseen': lastseen,
        }

        info['machines-last-status'] = r.hget('machines-last-status', entry)
        info['machines-last-taskid'] = r.hget('machines-last-taskid', entry)
        values.append(info)
    return json.dumps(values, indent=2), 200, {'content-type': 'application/json'}


@app.route('/machines/<machine>', methods=['GET'])
def machine_by_id(machine):
    info = {
        'lastseen': r.hget('machines', machine),
        'laststatus': r.hget('machines-last-status', machine),
        'lasttaskid': r.hget('machines-last-taskid', machine),
    }
    if not info['lastseen']:
        return 'unknown machine', 404, {}
    return json.dumps(info), 200, {'content-type': 'application/json'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))
