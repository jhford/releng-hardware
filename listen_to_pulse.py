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

        if not workerGroup or not workerId:
            print('DEBUG: This message is missing workerGroup or workerId')
            print(json.dumps(body, indent=2))  # TODO: Ask John about it.
            return

        print('blipity bloop {}:{}'.format(workerGroup, workerId))

        lastseen = datetime.datetime.utcnow().isoformat()
        taskStatus = ""

        if self.exchangeInfo == self.queueEvents.taskRunning(provisionerId='releng-hardware'):
            taskStatus = "Running"
        elif self.exchangeInfo == self.queueEvents.taskCompleted(provisionerId='releng-hardware'):
            taskStatus = "Completed"
        elif self.exchangeInfo == self.queueEvents.taskFailed(provisionerId='releng-hardware'):
            taskStatus = "Failed!"
        elif self.exchangeInfo == self.queueEvents.taskException(provisionerId='releng-hardware'):
            taskStatus = "Exception!"
        else:
            print("Unknown task type!")

        self.r.hset('machines', workerGroup + ':' + workerId, lastseen, taskStatus)  # TODO: Ask John about it.

        msg.ack()


def main():
    c = TaskMessagesConsumer(user=amqp_user, password=amqp_pass)
    c.listen()


if __name__ == '__main__':
    main()
