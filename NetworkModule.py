import string
from dataclasses import dataclass

import zmq
import signal
from enum import Enum
from random import choices, randrange
from StatisticsCollector import DamageStatistics
import logging

population = [1, 0]
weights = [0.01, 0.99]


class NodeType(Enum):
    Subscriber = 1
    Publisher = 2
    Both = 3
    Null = 0

@dataclass
class NetModuleMsg:
    action: string
    node_id: int


class NetworkModule:
    def __init__(self, sub_list, pub_port, msgs, stats):
        self.type = NodeType.Null
        logging.basicConfig(filename='simulation.log', encoding='utf-8', level=logging.DEBUG)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sub_context = zmq.Context()
        pub_context = zmq.Context()
        self.sub_list = sub_list
        self.id = pub_port
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
            self.stats_q = stats
            self.stats = DamageStatistics()

    def send_msg(self, msg):
        self.check_if_new_config()
        self.pub_socket.send(self.draw_noise(msg))
        logging.info(f'{self.id} NetMod messages damaged: {self.stats.damaged} / {self.stats.total_sent}')
        self.stats_q.put([self.id, self.stats])

    def receive_msg(self):
        self.check_if_new_config()
        message = dict(self.poller.poll(1000))
        if message.get(self.sub_socket) == zmq.POLLIN:
            return self.sub_socket.recv(zmq.NOBLOCK)
        else:
            return {}

    def check_if_new_config(self):
        if not self.new_config.empty():
            action = self.new_config.get()
            if action.action == "add":
                self.sub_socket.connect('tcp://localhost:' + str(action.node_id))
            if action.action == "delete":
                if action.node_id in self.sub_list:
                    self.sub_socket.disconnect('tcp://localhost:' + str(action.node_id))

    def draw_noise(self, coded_msg):
        self.stats.total_sent = self.stats.total_sent + 1
        if choices(population, weights)[0] == 1:
            self.stats.damaged = self.stats.damaged + 1
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
