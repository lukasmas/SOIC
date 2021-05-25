import string
from dataclasses import dataclass
from multiprocessing import Queue
from random import getrandbits, randrange


@dataclass
class RawMsg:
    msg_id: int
    destination: int
    msg: string


class Supervisor:

    def __init__(self, msg_count, node_count):
        self.task_list = []
        self.response_queue = Queue()
        self.unique_sequence = self.unique_id()
        self.queue_list = []
        self.msg_count = msg_count
        self.node_count = node_count
        self.netModules = dict()

    @staticmethod
    def unique_id():
        seed = getrandbits(8)
        while True:
            yield seed
            seed += 1

    def generate_task(self, port, tasks, new_node = True):
        for i in range(self.msg_count):
            msg = RawMsg(0, 0, "")
            msg.destination = self.generate_dest_port(port)
            msg.msg = f'Hi from {port} to {msg.destination}, have a nice day: {i}'
            msg.msg_id = next(self.unique_sequence)
            self.task_list.append(msg.msg_id)
            tasks.put(msg)

        if new_node:
            self.queue_list.append([port, tasks])

    def generate_dest_port(self, port, base_port=5000):
        dest = base_port + randrange(self.node_count)
        while dest == port:
            dest = base_port + randrange(self.node_count)
        return dest

    def get_results(self):
        msg_delivered = 0
        for i in range(self.response_queue.qsize()):
            msg_id = self.response_queue.get()
            if msg_id in self.task_list:
                msg_delivered = msg_delivered + 1

        print(f'Msg delivered: {msg_delivered} / {len(self.task_list)} ')

    def generate_new_tasks(self):
        for q in self.queue_list:
            self.generate_task(q[0], q[1], False)
