import time

from Message import *
import logging
from Supervisor import RawMsg
from StatisticsCollector import SentStatistics


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
    def __init__(self, pub_port, network_module, queue, responses, stats_queue):
        logging.basicConfig(filename='simulation.log', encoding='utf-8', level=logging.DEBUG)
        self.no_msg_in_row = 0
        self.no_msg_threshold = 10
        self.msg_list = []
        self.qtask = queue
        self.responses = responses
        self.connections = dict()
        self.prev_connections = dict()
        self.pub_port = pub_port
        self.last_localization_time = None
        self.new_search_period = 60
        self.pause_for_searching = 5
        self.resend_time = 10
        self.netModule = network_module
        self.localization_done = False
        self.last_broadcast_msg = None
        self.sent_statistics = SentStatistics()
        self.msg_sent = []
        self.stats_q = stats_queue
        logging.info(
            f'Node created! id : {self.pub_port}, queue : {queue.qsize()}')

    def run(self):
        time.sleep(1)
        self.localize_other_nodes()
        self.timeout()

    def process_msg(self, msg):
        if msg.msg_code == 0x0:
            logging.warning(f'{self.pub_port}: new : {self.connections}, old : {self.prev_connections}')
            if msg.id_receiver == self.pub_port:
                if msg.msg_id not in self.msg_list:
                    self.msg_list.append(msg.msg_id)
                    self.responses.put(msg.msg_id)
                    logging.info(
                        f'{self.pub_port} : Msg {msg.msg_id} from {msg.id_sender} delivered: {msg.msg}, resp_q : {self.responses.qsize()}')
                    next = find_next_node(self.connections, self.pub_port, msg.id_sender)
                    msg_conf = Message(0x1, msg.msg_id, msg.id_receiver, msg.id_sender, next, msg.msg, 10, 0)
                    self.netModule.send_msg(code_msg(msg_conf))
                    self.sent_statistics.sent = self.sent_statistics.sent + 1
            else:
                if msg.ttl > 0 and msg.next_receiver == self.pub_port or msg.next_receiver == 0:
                    if msg.id_receiver not in self.connections.keys():
                        print(f'{self.pub_port}: brak id w con {msg.id_receiver}')
                        msg.next_receiver = 0
                    else:
                        msg.next_receiver = find_next_node(self.connections, self.pub_port, msg.id_receiver)
                    self.sent_statistics.forwarded = self.sent_statistics.forwarded + 1
                    self.netModule.send_msg(code_msg(msg))

        if msg.msg_code == 0x1:
            if msg.id_receiver == self.pub_port:
                for m in self.msg_sent:
                    if msg.msg_id == m['msg'].msg_id:
                        self.msg_sent.remove(m)
                        logging.info(f'{self.pub_port}: msg without conf {len(self.msg_sent)} ')
            else:
                if msg.ttl > 0 and msg.next_receiver == self.pub_port or msg.next_receiver == 0:
                    if msg.id_receiver not in self.connections.keys():
                        print(f'{self.pub_port}: brak id w con {msg.id_receiver}')
                        msg.next_receiver = 0
                    else:
                        msg.next_receiver = find_next_node(self.connections, self.pub_port, msg.id_receiver)
                    self.sent_statistics.forwarded = self.sent_statistics.forwarded + 1
                    self.netModule.send_msg(code_msg(msg))

        if msg.msg_code == 0xAA:
            self.last_broadcast_msg = time.time()
            if msg.ttl > 0:
                temp_cons = msg.msg.split(';')  # change to int
                for i in range(len(temp_cons) - 1):
                    if int(temp_cons[i]) not in self.connections:
                        self.connections[int(temp_cons[i])] = [int(temp_cons[i + 1])]
                    else:
                        if int(temp_cons[i + 1]) not in self.connections[int(temp_cons[i])]:
                            self.connections[int(temp_cons[i])].append(int(temp_cons[i + 1]))
                msg.msg = f'{msg.msg};{self.pub_port}'
                self.sent_statistics.broadcast = self.sent_statistics.broadcast + 1
                self.netModule.send_msg(code_msg(msg))

    def send_msg(self):
        if not self.qtask.empty():
            self.sent_statistics.sent = self.sent_statistics.sent + 1
            task = self.qtask.get()
            while self.connections == {}:
                self.localize_other_nodes()
            next_node = 0
            if task.destination not in self.connections.keys():
                print(f'{self.pub_port}: brak id w con {task.destination}')
            else:
                next_node = find_next_node(self.connections, self.pub_port, task.destination)
            self.msg_sent.append({'msg': RawMsg(task.msg_id, task.destination, task.msg), 'time': time.time()})
            msg_to_send = code_new_msg(0x0, self.pub_port, task.destination, next_node, task.msg_id, task.msg)
            self.netModule.send_msg(msg_to_send)

    def timeout(self):
        while True:
            self.stats_q.put([self.pub_port, self.sent_statistics])
            if self.last_localization_time is not None and time.time() - self.last_localization_time >= self.new_search_period:
                self.localize_other_nodes()
                continue
            if self.last_broadcast_msg is not None and time.time() - self.last_broadcast_msg >= self.pause_for_searching:
                self.localization_done = True
                self.last_localization_time = time.time()
            message = self.netModule.receive_msg()
            if message != {}:
                msg = decode_msg(message)
                if msg == -1:
                    continue
                self.process_msg(msg)
                self.no_msg_in_row = 0
            else:
                if self.localization_done:
                    # if self.pub_port == 5000:
                    #     nx.nx.draw(self.connections)
                    for m in self.msg_sent:
                        if time.time() - m['time'] >= self.resend_time:
                            self.qtask.put(m['msg'])
                            self.msg_sent.remove(m)
                    self.send_msg()

            # logging.info(f'{self.pub_port}: messages sent / forwarded {self.number_of_send} / {self.number_of_fwd}')
            logging.info(f'{self.pub_port}: msg without conf {len(self.msg_sent)} ')

    def localize_other_nodes(self):
        logging.info(f'{self.pub_port}: searching for nodes')
        self.prev_connections = self.connections
        self.connections = dict()
        self.localization_done = False
        broadcast_msg = code_new_msg(0xAA, self.pub_port, 0, 0, self.pub_port, str(self.pub_port))
        self.sent_statistics.broadcast = self.sent_statistics.broadcast + 1
        self.netModule.send_msg(broadcast_msg)

        # To Do:
        # searching for new nodes periodically
        # removing nodes
        # check what happened if dest_node not exist in connections
        # add transfer speed and distance as a parameter to search route ?
