import binascii
from datetime import datetime
import json
import random
from ast import literal_eval as make_tuple
from typing import List, overload
import numpy as np
import scipy.stats


try:
    from Crypto.Hash import keccak

    def keccak_256(value):
        return keccak.new(digest_bits=256, data=value).digest()
except ImportError:
    import sha3 as _sha3

    def keccak_256(value):
        return _sha3.keccak_256(value).digest()

@overload
def get_latency_delay(env, origin: str, destination: str, n=1):
    distribution = env.delays['LATENCIES'][origin][destination]
    # Convert latency in ms to seconds
    latencies = [
        latency/1000 for latency in get_random_values(distribution, n)]
    if len(latencies) == 1:
        return round(latencies[0], 4)
    else:
        return latencies


def get_latency_delay(origin: str, destination: str):
    key = f"{origin}_{destination}"
    latency:float = sim_data["latencies"].get(key)
    if latency is None:
        key = f"{destination}_{origin}"
        latency = sim_data["latencies"].get(key)
    latency = latency / 1000
    return round(latency, 4)

@overload
def get_received_delay(env, message_size: float, origin: str, destination: str, n=1):
    """
    It calculates and returns a delay when receiving/downloading a message with a certain size (`message_size`)

    :param message_size: message size in megabytes (MB)
    :param origin: the location of the origin node
    :param destination: the location of the destination node
    :param n: the number of delays returned

    If `n` is 1 it returns a `float`, if `n > 1` returns an array of `n` floats.
    """
    distribution = env.delays['THROUGHPUT_RECEIVED'][origin][destination]
    delay = _calc_throughput(distribution, message_size, n)
    if delay < 0:
        raise RuntimeError(
            f'Negative received delay ({delay}) to origin {origin} and destination {destination}')
    else:
        return delay


def get_received_delay(message_size: float, origin: str, destination: str):
    return get_sent_or_received_delay(message_size, origin, destination)


@overload
def get_sent_delay(env, message_size: float, origin: str, destination: str, n=1):
    """
    It calculates and returns a delay when sending/uploading a message with a certain size (`message_size`)

    :param message_size: message size in megabytes (MB)
    :param origin: the location of the origin node
    :param destination: the location of the destination node
    :param n: the number of delays returned

    If `n` is 1 it returns a `float`, if `n > 1` returns an array of `n` floats.
    """
    distribution = env.delays['THROUGHPUT_SENT'][origin][destination]
    delay = _calc_throughput(distribution, message_size, n)
    if delay < 0:
        raise RuntimeError(
            f'Negative sent delay ({delay}) to origin {origin} and destination {destination}')
    else:
        return delay


def get_sent_delay(message_size: float, origin: str, destination: str):
    return get_sent_or_received_delay(message_size, origin, destination)

def get_sent_or_received_delay(message_size: float, origin:str, destination:str):
    key = f"{origin}_{destination}"
    throughput = sim_data["throughputs"].get(key)
    if throughput is None:
        key = f"{destination}_{origin}"
        throughput = sim_data["throughputs"].get(key)
    delay = (message_size * 8) / throughput
    return round(delay, 3)
    

def _calc_throughput(distribution: dict, message_size: float, n):
    rand_throughputs = get_random_values(distribution, n)
    delays = []
    for throughput in rand_throughputs:
        delay = (message_size * 8) / throughput
        delays.append(delay)
    if len(delays) == 1:
        return round(delays[0], 3)
    else:
        return delays


def time(env):
    return datetime.utcfromtimestamp(env.now).strftime('%m-%d %H:%M:%S')


def kB_to_MB(value):
    return value / 1000


def get_random_values(distribution: dict, n=1):
    """Receives a `distribution` and outputs `n` random values
    Distribution format: { \'name\': str, \'parameters\': tuple }"""
    dist = getattr(scipy.stats, distribution['name'])
    param = make_tuple(distribution['parameters'])
    c = dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)
    return c


def decode_hex(s):
    if isinstance(s, str):
        return bytes.fromhex(s)
    if isinstance(s, (bytes, bytearray)):
        return binascii.unhexlify(s)
    raise TypeError('Value must be an instance of str or bytes')


def encode_hex(b):
    if isinstance(b, str):
        b = bytes(b, 'utf-8')
    if isinstance(b, (bytes, bytearray)):
        return str(binascii.hexlify(b), 'utf-8')
    raise TypeError('Value must be an instance of str or bytes')


def is_numeric(x):
    return isinstance(x, int)


def encode_int32(v):
    return v.to_bytes(32, byteorder='big')



rng = np.random.default_rng()
sim_data = {}

def _read_json_file(file_location:str):
        with open(file_location) as f:
            return json.load(f)


def initialize_node_values(folder_path:str="/home/rockson/blocksim_dipper/blocksim/out"):
    node_properties = dict(_read_json_file(f"{folder_path}/node_properties.json"))
    loc_names = list(_read_json_file(f"{folder_path}/loc_names.json"))
    latencies = dict(_read_json_file(f"{folder_path}/latencies.json"))
    throughputs = dict(_read_json_file(f"{folder_path}/throughputs.json"))
    solutions = dict(_read_json_file(f"{folder_path}/solution.json"))

    sim_data["node_properties"] = node_properties
    sim_data["loc_names"] = loc_names
    sim_data["latencies"] = latencies
    sim_data["throughputs"] = throughputs
    sim_data["solutions"] = solutions

    sim_data["number_of_nodes"] = len(sim_data["node_properties"])
    sim_data["dim"] = get_average_number_of_neighbours(sim_data["number_of_nodes"])
    sim_data["lb"] = [0] * sim_data["dim"] # Lower bound
    sim_data["ub"] = [sim_data["number_of_nodes"] - 1] * sim_data["dim"] # Upper bound
    sim_data["current_node_id"] = 0
    return sim_data

def get_average_number_of_neighbours(num_nodes:int) -> int:
        n = num_nodes
        M = ((n - 1) / n) * np.log2(n)
        return int(np.ceil(M))

def get_node_by_id(node_id:int):
    node = sim_data["node_properties"].get(node_id)
    return node

def get_nodes(node_ids:list):
    nodes = []
    for node_id in node_ids:
        node = get_node_by_id(node_id)
        nodes.append(node)
    return nodes

def get_optimum_neighbours(current_node_id:int, nodes_dict:dict):
    solution = sim_data["solutions"]
    neigh_id_list = solution[str(current_node_id)]
    neighbours = []
    for i in neigh_id_list:
        node = nodes_dict.get(i)
        if node is not None:
            neighbours.append(nodes_dict[i])
    return neighbours


def get_random_neighbours(num:int, current_node_id:int, nodes_dict:dict):
    sim_data["current_node_id"] = current_node_id
    a = np.random.randint(0, sim_data["number_of_nodes"], num)
    a = _check_and_fix_solution(a)
    neighbours = []
    for i in a:
        node = nodes_dict.get(i)
        if node is not None:
            neighbours.append(nodes_dict[i])
    return neighbours

def _check_and_fix_solution(solution:np.ndarray):
    
    solution = solution.astype(int)
    solution = solution.clip(sim_data["lb"][:len(solution)], sim_data["ub"][:len(solution)]) 
    b = set(solution)

    if b.__contains__(sim_data["current_node_id"]):
        b.remove(sim_data["current_node_id"])

    while ((len(solution) - len(b)) > 0):
        b.add(np.random.randint(0, sim_data["number_of_nodes"], 1)[0])
        if b.__contains__(sim_data["current_node_id"]):
            b.remove(sim_data["current_node_id"])
    return np.array(list(b))
