import time
import os
from json import dumps as dump_json
from blocksim.report_engine import ReportEngine
from blocksim.utils import get_optimum_neighbours, get_random_neighbours, initialize_node_values, update_random_neighbours
from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.transaction_factory import TransactionFactory
from blocksim.models.network import Network

RNS = True
AV_NEIGHBOURS = 7

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


def run_model():
    now = int(time.time())  # Current time
    duration = 3600*3  # seconds

    input_data = initialize_node_values()

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

    miners = {
        'Ohio': {
            'how_many': 0,
            'mega_hashrate_range': "(20, 40)"
        },
        'Tokyo': {
            'how_many': 2,
            'mega_hashrate_range': "(20, 40)"
        }
    }
    non_miners = {
        'Tokyo': {
            'how_many': 1
        },
        'Ireland': {
            'how_many': 1
        }
    }

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
    transaction_factory.broadcast(100, 400, 15, nodes_dict)

    xyz = time.time()
    world.start_simulation()
    print(time.time() - xyz)
    
    # report_node_chain(world, list(nodes_dict.values()))
    reports = ReportEngine(list(nodes_dict.values()), world.env.data)
    reports.get_txn_report(duration)
    reports._get_average_finality_time()
    reports._get_network_wide_latency()
    # print(nodes_dict)
    # write_report(world)
    xyz = 1


if __name__ == '__main__':
    run_model()
