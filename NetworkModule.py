import zmq
import signal
from enum import Enum
from random import choices, randrange

population = [1, 2]
weights = [0.01, 0.99]


class NodeType(Enum):
    Subscriber = 1
    Publisher = 2
    Both = 3
    Null = 0


class NetworkModule:
    def __init__(self, sub_list, pub_port, msgs):
        self.type = NodeType.Null
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sub_context = zmq.Context()
        pub_context = zmq.Context()

        self.sub_list = sub_list
        if pub_port:
            self.type = NodeType.Publisher
            self.pub_socket = pub_context.socket(zmq.PUB)
            self.pub_socket.bind('tcp://*:' + str(pub_port))
        if self.sub_list:
            if self.type == NodeType.Publisher:
                self.type = NodeType.Both
            else:
                self.type = NodeType.Subscriber
            self.sub_socket = sub_context.socket(zmq.SUB)
            for sub_point in sub_list:
                self.sub_socket.connect('tcp://localhost:' + str(sub_point))
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
            self.poller = zmq.Poller()
            self.poller.register(self.sub_socket, zmq.POLLIN)
            self.new_config = msgs

    def send_msg(self, msg):
        self.check_if_new_config()
        self.pub_socket.send(self.draw_noise(msg))

    def receive_msg(self):
        self.check_if_new_config()
        message = dict(self.poller.poll(1000))
        if message.get(self.sub_socket) == zmq.POLLIN:
            return self.sub_socket.recv(zmq.NOBLOCK)
        else:
            return {}

    def check_if_new_config(self):
        if not self.new_config.empty():
            new_node = self.new_config.get()
            self.sub_socket.connect('tcp://localhost:' + str(new_node))

    @staticmethod
    def draw_noise(coded_msg):
        if choices(population, weights)[0] == 1:
            index = randrange(0, 127)
            bit = randrange(0, 7)

            modified = coded_msg[index] ^ bit
            coded_new = b''
            for i in range(128):
                if i == index:
                    coded_new = coded_new + bytes([modified])
                    continue
                coded_new = coded_new + bytes([coded_msg[i]])
            return coded_new

        return coded_msg
