import multiprocessing as mp
import json


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
        configuration_list.append((port, sub_list))
        port = port + 1
    return configuration_list


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_soic()
    raw_configuration = read_config()
    configuration = parse_configuration(raw_configuration)
    # subprocess.run("python Node.py --sub 5001")
    # subprocess.run("python Node.py --pub 5001")

    # multiprocess
