import os
import taskcluster
import redis
import datetime

from mozillapulse.consumers import GenericConsumer, PulseConfiguration

amqp_user = os.environ.get('AMQP_USER', None)
amqp_pass = os.environ.get('AMQP_PASS', None)


class TaskMessagesConsumer(GenericConsumer):

    def __init__(self, **kwargs):
        self.r = r = redis.from_url(os.environ.get("REDIS_URL"))  # TODO: Ask John about it.
        self.queueEvents = queueEvents = taskcluster.QueueEvents()
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

        if 'status' in body:
            taskId = body['status']['taskId']
            state = body['status']['runs'][body['runId']].get('state', 'missing-state')
            reasonResolved = body['status']['runs'][body['runId']].get('reasonResolved', 'unresolved')

        if not workerGroup or not workerId:
            print('DEBUG: This message is missing workerGroup or workerId')
            print(json.dumps(body, indent=2))  # TODO: Ask John about it.
            return

        print('blipity bloop {}:{}, {}, {}, {}'.format(workerGroup, workerId, taskId, state, reasonResolved))

        lastseen = datetime.datetime.utcnow().isoformat()

        pipeline = self.r.pipeline()
        pipeline.hset('machines', workerGroup + ':' + workerId, lastseen)
        pipeline.hset('machines-last-status', workerGroup + ':' + workerId, state + '_' + reasonResolved)
        pipeline.hset('machines-last-taskid', workerGroup + ':' + workerId, taskId)
        pipeline.execute()

        msg.ack()


def main():
    c = TaskMessagesConsumer(user=amqp_user, password=amqp_pass)
    c.listen()


if __name__ == '__main__':
    main()
