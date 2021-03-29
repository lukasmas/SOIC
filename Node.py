import signal
import string
import struct
from dataclasses import dataclass
from random import randrange

import zmq
import time
import argparse
from enum import Enum


class NodeType(Enum):
    Subscriber = 1
    Publisher = 2
    Both = 3
    Null = 0


@dataclass
class Message:
    head: string
    msg_id: int
    id_sender: int
    id_receiver: int
    msg: string
    ttl: int
    check_sum: int


def code_new_msg(id_sender, id_receiver, id, msg):
    checksum = sum(map(ord, msg))
    ttl = 10
    head = b'okon'
    coded = struct.pack('4s h h h 110s h h', head, id, id_sender, id_receiver, str.encode(msg), ttl, checksum)
    return coded


def code_msg(msg):
    if msg.check_sum == sum(map(ord, msg.msg)):
        coded = struct.pack('4s h h h 110s h h', msg.head, msg.msg_id, msg.id_sender, msg.id_receiver,
                            str.encode(msg.msg), msg.ttl, msg.check_sum)
        return coded
    else:
        print(f'WRONG check sum old: {msg.check_sum} != new:  {sum(map(ord, msg.msg))}')


def decode_msg(coded_msg):
    decoded = struct.unpack('4s h h h 110s h h', coded_msg)
    msg = Message(decoded[0], decoded[1], decoded[2], decoded[3], decoded[4].decode("utf-8"), decoded[5], decoded[6])
    msg.ttl = msg.ttl - 1
    return msg


def prepare_parser():
    parser_prep = argparse.ArgumentParser()
    parser_prep.add_argument('-s', '--sub', nargs='+', type=int)
    parser_prep.add_argument('-p', '--pub', nargs='+', type=int)
    return parser_prep


class Node:
    def __init__(self, sub_list, pub_list):
        self.type = NodeType.Null
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sub_context = zmq.Context(2)
        pub_context = zmq.Context()
        self.pub_list = pub_list
        self.sub_list = sub_list
        if pub_list:
            self.type = NodeType.Publisher
            self.pub_socket = pub_context.socket(zmq.PUB)
            # for pub_point in pub_list:
            self.pub_socket.bind('tcp://*:' + str(pub_list))
        if self.sub_list:
            if self.type == NodeType.Publisher:
                self.type = NodeType.Both
            else:
                self.type = NodeType.Subscriber
            self.sub_socket = sub_context.socket(zmq.SUB)
            for sub_point in sub_list:
                self.sub_socket.connect('tcp://localhost:' + str(sub_point))
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, b'okon')
        self.msg_list = []
        print(f'Node type {self.type.name} created! id : {self.pub_list}, sub : {self.sub_list}')

    def run(self):
        if self.type == NodeType.Subscriber:
            self.listen_msg()
        if self.type == NodeType.Publisher:
            self.send_msg()
        if self.type == NodeType.Both:
            # n = randrange(2)
            # print(n)
            if self.pub_list == 5000:
                self.send_msg()
            else:
                self.listen_msg()

    def listen_msg(self):
        while True:
            message = self.sub_socket.recv_multipart()
            msg = decode_msg(message[0])
            if msg.id_receiver == self.pub_list:
                if msg.msg_id not in self.msg_list:
                    self.msg_list.append(msg.msg_id)
                    print(f'{self.pub_list} : Msg {msg.msg_id} from {msg.id_sender} delivered: {msg.msg}')

            else:
                if msg.ttl > 0:
                    print(
                        f'{self.pub_list} : Msg {msg.msg_id} from {msg.id_sender} forwarded to : {msg.id_receiver}, ttl: {msg.ttl}')
                    self.pub_socket.send(code_msg(msg))

    def send_msg(self):
        msg_counter = 0
        while True:
            msg_to_send = code_new_msg(self.pub_list, 5003, msg_counter, 'AAAAABBBBB')
            self.pub_socket.send(msg_to_send)
            msg_counter += 1
            time.sleep(3)


if __name__ == "__main__":
    parser = prepare_parser()
    args = vars(parser.parse_args())
    node = Node(args["sub"], args["pub"])
    node.run()
