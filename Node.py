import signal
import zmq
from enum import Enum
from Message import *


class NodeType(Enum):
    Subscriber = 1
    Publisher = 2
    Both = 3
    Null = 0


class Node:
    def __init__(self, sub_list, pub_port, queue, responses):
        self.type = NodeType.Null
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sub_context = zmq.Context()
        pub_context = zmq.Context()
        self.pub_port = pub_port
        self.sub_list = sub_list
        self.no_msg_in_row = 0
        self.no_msg_threshold = 10
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
        self.msg_list = []
        self.qtask = queue
        self.responses = responses
        print(
            f'Node type {self.type.name} created! id : {self.pub_port}, sub : {self.sub_list}, queue : {queue.qsize()}')

    def run(self):
        if self.type == NodeType.Subscriber:
            self.timeout()
        if self.type == NodeType.Publisher:
            self.send_msg()
        if self.type == NodeType.Both:
            self.timeout()

    def process_msg(self, msg):
        if msg.id_receiver == self.pub_port:
            if msg.msg_id not in self.msg_list:
                self.msg_list.append(msg.msg_id)
                self.responses.put(msg.msg_id)
                print(
                    f'{self.pub_port} : Msg {msg.msg_id} from {msg.id_sender} delivered: {msg.msg}, resp_q : {self.responses.qsize()}')
        else:
            if msg.ttl > 0:
                self.pub_socket.send(code_msg(msg))

    def send_msg(self):
        if not self.qtask.empty():
            task = self.qtask.get()
            msg_to_send = code_new_msg(self.pub_port, task.destination, task.msg_id, task.msg)
            self.pub_socket.send(msg_to_send)

    def timeout(self):
        while True:
            message = dict(self.poller.poll(1000))
            if message.get(self.sub_socket) == zmq.POLLIN:
                msg = decode_msg(self.sub_socket.recv(zmq.NOBLOCK))
                self.process_msg(msg)
                self.no_msg_in_row = 0
            else:
                self.no_msg_in_row = self.no_msg_in_row + 1
                self.send_msg()
                if self.qtask.empty() and self.no_msg_in_row >= self.no_msg_threshold:
                    return

