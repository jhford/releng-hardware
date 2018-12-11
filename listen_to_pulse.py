import os
import taskcluster
import redis
import datetime

from mozillapulse.consumers import GenericConsumer, PulseConfiguration
amqp_user = os.environ.get('AMQP_USER', None)
amqp_pass = os.environ.get('AMQP_PASS', None)

class TaskMessagesConsumer(GenericConsumer):

    def __init__(self, **kwargs):
        self.r = r = redis.from_url(os.environ.get("REDIS_URL"))
        self.queueEvents = queueEvents = taskcluster.QueueEvents();
        self.exchangeInfo = exchangeInfo = [
            queueEvents.taskRunning(provisionerId='releng-hardware'),
            queueEvents.taskCompleted(provisionerId='releng-hardware'),
            queueEvents.taskFailed(provisionerId='releng-hardware'),
            queueEvents.taskException(provisionerId='releng-hardware'),

        ]
        super(TaskMessagesConsumer, self).__init__(
            PulseConfiguration(**kwargs),
            applabel='releng-hardware',
            exchange=[x['exchange'] for x in exchangeInfo],
            topic=[x['routingKeyPattern'] for x in exchangeInfo],
            callback=lambda body, msg: self.handle_message(body, msg),
            **kwargs)


    def handle_message(self, body, msg):
        workerGroup = body.get('workerGroup')
        workerId = body.get('workerId')

        if not workerGroup or not workerId:
            print('DEBUG: This message is missing workerGroup or workerId')
            print(json.dumps(body, indent=2))
            return

        print('blipity bloop %s:%s' % (workerGroup, workerId))

        lastseen = datetime.datetime.utcnow().isoformat()

        self.r.hset('machines', workerGroup + ':' + workerId, lastseen)

        msg.ack()


def main():
    c = TaskMessagesConsumer(user=amqp_user, password=amqp_pass);
    c.listen()

if __name__ == '__main__':
    main()
