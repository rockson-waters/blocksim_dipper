from pickle import FALSE
import time
import os
from json import dumps as dump_json
from blocksim.report_engine import ReportEngine
from blocksim.utils import get_optimum_neighbours, get_random_neighbours, initialize_node_values, update_random_neighbours
from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.transaction_factory import TransactionFactory
from blocksim.models.network import Network

RNS = False
AV_NEIGHBOURS = 9
NUMBER_OF_RUNS = 100
NETWORK_SIZE = 500

def write_report(world):
    path = 'output/report.json'
    if not os.path.exists(path):
        os.mkdir('output')
        with open(path, 'w') as f:
            pass
    with open(path, 'w') as f:
        f.write(dump_json(world.env.data))


def report_node_chain(world, nodes_list):
    for node in nodes_list:
        head = node.chain.head
        chain_list = []
        num_blocks = 0
        for i in range(head.header.number):
            b = node.chain.get_block_by_number(i)
            node.blocks_in_chain.append(b)
            chain_list.append(str(b.header))
            num_blocks += 1
        chain_list.append(str(head.header))
        key = f'{node.address}_chain'
        world.env.data[key] = {
            'head_block_hash': f'{head.header.hash[:8]} #{head.header.number}',
            'number_of_blocks': num_blocks,
            'chain_list': chain_list
        }


def run_model(run_id:int, algo:str, num_nodes:int):
    now = int(time.time())  # Current time
    duration = 3600*6  # seconds

    input_data = initialize_node_values(algo=algo, run_id=run_id, num=num_nodes)

    world = SimulationWorld(
        duration,
        now,
        'input-parameters/config.json',
        'input-parameters/latency.json',
        'input-parameters/throughput-received.json',
        'input-parameters/throughput-sent.json',
        'input-parameters/delays.json')

    # Create the network
    network = Network(world.env, 'NetworkXPTO')

    node_factory = NodeFactory(world, network)
    # Create all nodes
    # nodes_list = node_factory.create_nodes(miners, non_miners)
    nodes_dict = node_factory.create_nodes_from_read_data(input_data)
    # Start the network heartbeat
    world.env.process(network.start_heartbeat())
    # Full Connect all nodes

    neigh = []
    if RNS:
        solution = {}
        for node_id, node in nodes_dict.items():
           neigh, neigh_ids = get_random_neighbours(AV_NEIGHBOURS, node_id, nodes_dict)
           solution[node_id] = (neigh_ids, neigh)
        #    node.connect(neigh)
        for node_id, node in nodes_dict.items():
            neigh = update_random_neighbours(node_id, nodes_dict, solution)
            node.connect(neigh)
    else:
        for node_id, node in nodes_dict.items():
           neigh = get_optimum_neighbours(node_id, nodes_dict)
           node.connect(neigh)

        

    transaction_factory = TransactionFactory(world)
    transaction_factory.broadcast(10, 40, 15, nodes_dict)

    
    world.start_simulation()
    
    
    report_node_chain(world, list(nodes_dict.values()))
    reports = ReportEngine(list(nodes_dict.values()), world.env.data)
    reports.get_txn_report(duration)

    # print(nodes_dict)
    # write_report(world)
    xyz = 1


if __name__ == '__main__':
    xyz = time.time()
    algos = ["mst"]#, "RNS", "CL_PSO", "HPSO", "PPSO", "mst"]
    for algo in algos:
        if algo == "RNS":
            RNS = True
            # RNS generates its own neighbours, therefore, the value of algo needed to read solution files is 
            # irrelevant. BasePSO has been selected to avoid exceptions. Any other value could have been chosen
            algo = "BasePSO" 
        for n in range(0, NUMBER_OF_RUNS, 1):
            run_model(algo=algo, run_id=n, num_nodes=NETWORK_SIZE)
    print(time.time() - xyz)
