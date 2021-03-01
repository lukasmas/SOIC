import signal
import zmq
import time
import argparse
from enum import Enum


class NodeType(Enum):
    Subscriber = 1
    Publisher = 2
    Both = 3
    Null = 0


def prepare_parser():
    parser_prep = argparse.ArgumentParser()
    parser_prep.add_argument('-s', '--sub', nargs='+', type=int)
    parser_prep.add_argument('-p', '--pub', nargs='+', type=int)
    return parser_prep


class Node:
    def __init__(self, sub_list, pub_list):
        self.type = NodeType.Null
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        context = zmq.Context()
        self.pub_list = pub_list
        if sub_list and pub_list:
            self.type = NodeType.Both
            print('Not supported yet!')
            return
        if sub_list:
            self.type = NodeType.Subscriber
            self.socket = context.socket(zmq.SUB)
            for sub_point in sub_list:
                self.socket.connect('tcp://localhost:' + str(sub_point))
            self.socket.setsockopt(zmq.SUBSCRIBE, b'okon')
        if pub_list:
            self.type = NodeType.Publisher
            self.socket = context.socket(zmq.PUB)
            for pub_point in pub_list:
                self.socket.bind('tcp://*:' + str(pub_point))
        self.list = []
        print("Node type " + self.type.name + " created!")

    def run(self):
        if self.type == NodeType.Subscriber:
            self.listen_msg()
        if self.type == NodeType.Publisher:
            self.send_msg()

    def listen_msg(self):
        while True:
            message = self.socket.recv_multipart()
            print(f'Received: {message}')
            self.list.append(message)

    def send_msg(self):
        msg_counter = 0
        while True:
            self.socket.send(b'okon msg ' + str.encode(str(msg_counter)))
            msg_counter += 1
            time.sleep(3)


if __name__ == "__main__":
    parser = prepare_parser()
    args = vars(parser.parse_args())
    node = Node(args["sub"], args["pub"])
    node.run()
