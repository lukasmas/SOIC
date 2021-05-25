from multiprocessing import Process
import json

from Node import *
from Supervisor import *
from NetworkModule import *
import time


def print_soic():
    print('Welcome in SOIC, work are in progress...')  # Pres


def read_config():
    with open('connections.json') as json_file:
        data = json.load(json_file)
        return data['connections']


def generate_connections(last_id):
    nodes = last_id - 5000
    count = randrange(int(nodes / 2))
    subs = []
    for i in range(count):
        sub = randrange(5000, last_id)
        while sub in subs:
            sub = randrange(5000, last_id)
        subs.append(sub)
    return subs


def add_node(node_id):
    q = Queue()
    new_id = node_id + 1
    supervisor.generate_task(new_id, q)
    subs = generate_connections(node_id)
    supervisor.netModules[new_id] = Queue()
    new_p = Process(target=run_single_node,
                    args=(new_id, subs, q, supervisor.response_queue, supervisor.netModules[new_id]))
    new_p.start()
    processes.append(new_p)
    print(
        f'Node created! id : {new_id}, subs: {subs} queue : {q.qsize()}')
    return subs


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


def run_single_node(pub, sub, tasks, responses, net_modules_q):
    net_module = NetworkModule(sub, pub, net_modules_q)
    node = Node(pub, net_module, tasks, responses)
    node.run()


if __name__ == '__main__':
    print_soic()
    raw_configuration = read_config()
    configuration = parse_configuration(raw_configuration)
    last_node_id = configuration[-1][0]
    msg_count = 10
    supervisor = Supervisor(msg_count, len(configuration))
    processes = []

    print('Running with default configuration...')

    for c in configuration:
        pub = c[0]
        sub = c[1]
        que = c[2]
        supervisor.generate_task(pub, que)
        supervisor.netModules[pub] = Queue()
        p = Process(target=run_single_node, args=(pub, sub, que, supervisor.response_queue, supervisor.netModules[pub]))
        p.start()
        processes.append(p)

    time.sleep(1)
    while True:
        print("1. Add node")
        print("2. Remove node")
        print("3. Generate new msg")
        print("4. Finish simulation")
        print("Choose option: ")

        opt = None
        try:
            opt = int(input())
        except:
            continue

        if opt == 1:
            subs = add_node(last_node_id)
            last_node_id = last_node_id + 1
            supervisor.node_count = supervisor.node_count + 1
            for n in supervisor.netModules:
                if n in subs:
                    supervisor.netModules[n].put(last_node_id)

        if opt == 3:
            supervisor.generate_new_tasks()
            print("New tasks added!")

        if opt == 4:
            is_all_empty = True
            for q in supervisor.queue_list:
                if not q[1].empty():
                    is_all_empty = False

            if is_all_empty:
                print("Finishing the simulation ... ")
                for p in processes:
                    # p.join()
                    p.kill()
                break
            if not is_all_empty:
                print('not all tasks are done')


    print()
    print()

    supervisor.get_results()

# statystyki i uszkdzanie ramki
