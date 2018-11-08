# Proof of concept for listening to `releng-hardware` events
This is a repository which contains a proof of concept for listening to queue
messages regarding hardware under the `releng-hardware` psuedo-provisioner for
the purpose of tracking releng hardware.  It is not a fully formed codebase,
rather a simple codebase which can be developed into a fully featured tool.

It is written in Python 2.7, but should be possible to convert to Python 3.

The basic idea is to listen to any messages which are sent by the Queue for
workers which use the provisioner id 'releng-hardware' and represent activity
from a worker.  This is a task failing, completing, running or exception-ing.
Any of these messages show signs of active life on the instance.  It might be
desirable to track task exception states for each worker.

## Identifiers
Resources in this system are identified by `$DC:$HOSTNAME`.  Basically, I don't
know if it's safe to assume that hostnames are unique across all of
releng-hardware so I've included the datacenter in the identifier.

The `/machines` endpoint splits the datacenter id from the hostname, so if
desired, can be ignored

## Installation
A `setup.py` file is not provided because this is a proof of concept.  Writing
one is recommended.

The dependencies used are installed as follows:

```bash
pip install -r requirements.txt
```

## Configuration and Running
This system requires a Redis installation and a Pulse username and password.

The following commands will run the webserver and pulse listener in the
background.

```bash
$ cat .env.sh
export AMQP_USER=username
export AMQP_PASS=password
export REDIS_URL='redis://127.0.0.1:6379'
$ source .env.sh
$ python webserver.py &
$ python listen_to_pulse.py &
```

A script `preload_redis.py` exists which takes data in the format returned by
the `/machines` endpoint and inserts it into the redis storage.  This shouldn't
be needed though, since a 404 response from the `/machines/<id>` should be
enough to know that the machine has not been heard from since the database was
last initialized.

Here's an example index in the list

```json
[
  {
    "machine": "t-linux64-ms-100",
    "datacenter": "mdc1",
    "lastseen": "2018-11-08T08:47:50.939514"
  }
]
```

This document is read from standard input and inserts into redis.  The
production `REDIS_URL` must be set correctly, which is accessible from heroku
using the Heroku CLI tool as follows:

```bash
export $(heroku config:get -s REDIS_URL --app releng-hardware)
cat data-to-preload.json | python preload_redis.py
```

## Deployment
A sample deployment is made as Heroku app 'releng-hardware.herokuapp.com'.  It
uses two dynos, one for the webserver and one for the pulse listener.  There is
a shared Redis app which is automatically managed by Heroku for storing data.

## API
This app provides a very simple API.  It has two methods:

1. `https://releng-hardware.herokuapp.com/machines`: list all machines, their
   datacenter and time they were last seen
1. `https://releng-hardware.herokuapp.com/machines/mdc1:t-linux64-ms-100`: show
   the last time `t-linux64-ms-100` in `mdc1` was seen.

Both responses are content-type `application/json`.  Absence from the first
endpoint or a 404 from the second implies the machine has not been seen since
listening began
