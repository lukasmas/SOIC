from multiprocessing import Process
import json

from Node import *
from Supervisor import *


def print_soic():
    print('Welcome in SOIC, work are in progress...')  # Pres


def read_config():
    with open('connections.json') as json_file:
        data = json.load(json_file)
        return data['connections']


def parse_configuration(config, base_port=5000):
    print("Parsing nodes connections:")
    configuration_list = []
    port = base_port
    for c in config:
        index = 0
        sub_list = []
        for sub in c:
            if sub == 1:
                sub_list.append(base_port + index)
            index = index + 1
        print(f'pub: {port}, sub: {sub_list}')
        configuration_list.append((port, sub_list, Queue()))
        port = port + 1
    return configuration_list


def run_single_node(pub, sub, tasks, responses):
    node = Node(sub, pub, tasks, responses)
    node.run()


if __name__ == '__main__':
    print_soic()
    raw_configuration = read_config()
    configuration = parse_configuration(raw_configuration)
    msg_count = 3
    supervisor = Supervisor(msg_count, len(configuration))
    processes = []

    for c in configuration:
        supervisor.generate_task(c[0], c[2])
        p = Process(target=run_single_node, args=(c[0], c[1], c[2], supervisor.response_queue))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    print()
    print()
    supervisor.get_results()
