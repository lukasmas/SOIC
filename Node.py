import time

import zmq

from Message import *
import logging


def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest


def find_next_node(graph, start, end):
    return find_shortest_path(graph, start, end)[1]


class Node:
    def __init__(self, pub_port, network_module, queue, responses):
        logging.basicConfig(filename='simulation.log', encoding='utf-8', level=logging.DEBUG)
        self.no_msg_in_row = 0
        self.no_msg_threshold = 10
        self.msg_list = []
        self.qtask = queue
        self.responses = responses
        self.connections = dict()
        self.pub_port = pub_port
        self.last_localization_time = None
        self.netModule = network_module
        logging.info(
            f'Node created! id : {self.pub_port}, queue : {queue.qsize()}')

    def run(self):
        self.localize_other_nodes()
        self.timeout()

    def process_msg(self, msg):
        if msg.msg_code == 0x0:
            if msg.id_receiver == self.pub_port:
                if msg.msg_id not in self.msg_list:
                    self.msg_list.append(msg.msg_id)
                    self.responses.put(msg.msg_id)
                    logging.info(
                        f'{self.pub_port} : Msg {msg.msg_id} from {msg.id_sender} delivered: {msg.msg}, resp_q : {self.responses.qsize()}')
            else:
                if msg.ttl > 0 and msg.next_receiver == self.pub_port:
                    msg.next_receiver = find_next_node(self.connections, self.pub_port, msg.id_receiver)
                    self.netModule.send_msg(code_msg(msg))

        if msg.msg_code == 0xAA:
            if msg.ttl > 0:
                temp_cons = msg.msg.split(';')  # change to int
                for i in range(len(temp_cons) - 1):
                    if int(temp_cons[i]) not in self.connections:
                        self.connections[int(temp_cons[i])] = [int(temp_cons[i + 1])]
                    else:
                        if int(temp_cons[i + 1]) not in self.connections[int(temp_cons[i])]:
                            self.connections[int(temp_cons[i])].append(int(temp_cons[i + 1]))
                msg.msg = f'{msg.msg};{self.pub_port}'
                self.netModule.send_msg(code_msg(msg))

    def send_msg(self):
        if not self.qtask.empty():
            task = self.qtask.get()
            while self.connections == {}:
                self.localize_other_nodes()
            next_node = find_next_node(self.connections, self.pub_port, task.destination)
            msg_to_send = code_new_msg(0x0, self.pub_port, task.destination, next_node, task.msg_id, task.msg)
            self.netModule.send_msg(msg_to_send)

    def timeout(self):
        while True:
            message = self.netModule.receive_msg()
            if message != {}:
                msg = decode_msg(message)
                if msg == -1:
                    continue
                self.process_msg(msg)
                self.no_msg_in_row = 0
            else:
                self.no_msg_in_row = self.no_msg_in_row + 1
                self.send_msg()

    def localize_other_nodes(self):
        time.sleep(1)
        broadcast_msg = code_new_msg(0xAA, self.pub_port, 0, 0, self.pub_port, str(self.pub_port))
        self.netModule.send_msg(broadcast_msg)
        self.last_localization_time = time.time()

        # To Do:
        # searching for new nodes periodically
        # removing nodes
        # check what happened if dest not exist in connections
        # add transfer speed and distance as a parameter to search route
