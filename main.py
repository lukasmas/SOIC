from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager
import json

from Node import *
from Supervisor import *
from NetworkModule import *
import time
from StatisticsCollector import *


@dataclass
class Queues:
    tasks: Queue
    net_module_q: Queue
    responses: Queue
    stats: Queue


def print_soic():
    print('Welcome in SOIC, work are in progress...')  # Pres


def read_config():
    with open('connections.json') as json_file:
        data = json.load(json_file)
        return data['connections']


def generate_connections(last_id):
    nodes = last_id - 5000
    count = randrange(1, int(nodes / 2))
    subs = []
    for i in range(count):
        sub = randrange(5000, last_id)
        while sub in subs:
            sub = randrange(5000, last_id)
        subs.append(sub)
    return subs


def add_node(node_id, stats_queue):
    q = Queue()
    new_id = node_id + 1
    supervisor.generate_task(new_id, q)
    subs = generate_connections(node_id)
    supervisor.netModules[new_id] = Queue()
    queues = Queues(q, supervisor.netModules[new_id], supervisor.response_queue, stats_queue)
    new_p = Process(target=run_single_node,
                    args=(new_id, subs, queues))
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


def run_single_node(pub, sub, queues):
    net_module = NetworkModule(sub, pub, queues.net_module_q, queues.stats)
    node = Node(pub, net_module, queues.tasks, queues.responses, queues.stats)
    node.run()


if __name__ == '__main__':
    print_soic()
    raw_configuration = read_config()
    configuration = parse_configuration(raw_configuration)
    last_node_id = configuration[-1][0]
    msg_count = 10
    supervisor = Supervisor(msg_count, len(configuration))
    stats_queue = Queue()
    BaseManager.register('Statistics', Statistics)
    manager = BaseManager()
    manager.start()
    statistics = manager.Statistics()
    statistics_collector = StatisticsCollector(stats_queue)
    processes = []

    print('Running with default configuration...')

    for c in configuration:
        pub = c[0]
        sub = c[1]
        que = c[2]
        supervisor.generate_task(pub, que)
        supervisor.netModules[pub] = Queue()
        statistics_collector.add_stats(pub)
        queues = Queues(que, supervisor.netModules[pub], supervisor.response_queue, stats_queue)
        p = Process(target=run_single_node,
                    args=(pub, sub, queues))
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
            subs = add_node(last_node_id, stats_queue)
            last_node_id = last_node_id + 1
            statistics_collector.add_stats(last_node_id)
            supervisor.node_count = supervisor.node_count + 1
            notif = NetModuleMsg("add", last_node_id)
            for n in supervisor.netModules:
                if n in subs:
                    supervisor.netModules[n].put(notif)

        if opt == 2:
            print("Choose nodeId: ")

            node = None
            found = False
            try:
                node = int(input())
                for n in supervisor.queue_list:
                    if n[0] == node:
                        found = True
                if not found:
                    print("Node is not in the list!")
                    break
                notif = NetModuleMsg("delete", node)
                for n in supervisor.netModules:
                    supervisor.netModules[n].put(notif)
            except:
                print("Wrong")
                continue

        if opt == 3:
            supervisor.generate_new_tasks()
            print("New tasks added!")

        if opt == 4:
            is_all_empty = True
            q_size = 0
            for q in supervisor.queue_list:
                if not q[1].empty():
                    q_size = q_size + q[1].qsize()
                    is_all_empty = False

            if is_all_empty:
                print("Finishing the simulation ... ")
                statistics_collector.update_stats()
                supervisor.get_results()
                print()
                statistics_collector.print_stats()
                for p in processes:
                    # p.join()
                    p.kill()
                break
            if not is_all_empty:
                print(f'not all tasks are done, left task: {q_size} ')

    print()
    print()

# statystyki i uszkdzanie ramki
