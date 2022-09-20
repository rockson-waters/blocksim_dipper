from math import ceil
from blocksim.models import node as Node


class ReportEngine:
    
    def __init__(self, nodes:list, env_data=None):
        self.nodes = nodes
        # Select any node since all peers have the same chain
        self.any_node:Node.Node = self.nodes[0]
        self.blocks = self.any_node.blocks_in_chain

        self.proc_times = []
        self.all_txns = []
        self.block_num_hash = {}

        if env_data is not None:
            self.env_data = env_data
            self.tx_prop = self.env_data['tx_propagation'] # simulation output
            self.block_prop = self.env_data['block_propagation'] # simulation output

        self.block_props = {} # extracted from simulation output, per peer

        self._get_block_number_and_hash(self.blocks)
        self._get_blocks_prop_times(self.nodes, self.block_prop)
        self._get_block_receive_times(self.nodes, self.block_prop)
        self._get_network_wide_latency(self.block_num_hash)

    def _get_block_number_and_hash(self, blocks):
        i = 0
        for block in blocks:
            self.block_num_hash[i] = block.header.hash[:8]
            i += 1

    def _get_block_receive_times(self, nodes:list, block_prop:dict):
        block_receive_time_all_node = {}
        blocks_and_times = {}

        for node in nodes:
            address = node.address
            keys = block_prop.keys()
            blocks_and_times = {}

            # Key has format sender_receiver
            for key in keys:
                split = str.split(key, "_")
                if ((split[1] == address) and (len(block_prop[key]) > 0) ):
                    for k,v in block_prop[key].items():
                        if type(v) is tuple:
                            blocks_and_times[k] = v[0] + v[1]

            block_receive_time_all_node[address] = blocks_and_times
        return block_receive_time_all_node


    def _get_blocks_prop_times(self, nodes:list, block_prop:dict):
        block_props_all_node = {}
        blocks_and_times = {}

        for node in nodes:
            address = node.address
            keys = block_prop.keys()
            blocks_and_times = {}

            # Key has format sender_receiver
            for key in keys:
                split = str.split(key, "_")
                if ((split[1] == address) and (len(block_prop[key]) > 0) ):
                    for k,v in block_prop[key].items():
                        if type(v) is tuple:
                            blocks_and_times[k] = v[1]

            block_props_all_node[address] = blocks_and_times
        self.block_props = block_props_all_node





    def get_global_txn_report(self):
        pass

    def get_global_block_report(self):
        data = {}
        chain_num = {} # Stores block number against its hash
        for node in self.nodes:
            head = node.chain.head
            chain_list = []
            num_blocks = 0

            # Retrieve all blocks for the current node
            for i in range(head.header.number):
                b = node.chain.get_block_by_number(i)
                node.blocks_in_chain.append(b)
                chain_num[i] = b.header.hash[:8]
                chain_list.append(str(b.header))
                num_blocks += 1

            chain_list.append(str(head.header))
            key = f'{node.address}_chain'
            data[key] = {
                'head_block_hash': f'{head.header.hash[:8]} #{head.header.number}',
                'number_of_blocks': num_blocks,
                'chain_list': chain_list
            }
        return data

    def _get_peer_txn_report(self):
        pass

    def _get_peer_block_report(self):
        pass

    def _get_average_txn_dist_latency(self):
        
        txn_prop = self.tx_prop

    def _get_average_txn_proc_time(self):
        
        blocks = self.any_node.blocks_in_chain
        for block in blocks:
            if block.transactions is not None:
                for txn in block.transactions:
                    self.all_txns.append(txn)
                    self.proc_times.append(txn.proc_time - txn.gen_time)
        average_processing_time = sum(self.proc_times) / len(self.proc_times)
        return (average_processing_time)

    def get_transaction_throughput(self, sim_duration:float):
        throughput = len(self.all_txns) / sim_duration
        return throughput

    def get_transactions_processing_ratio(self, total_gen_txns=40000):
        total_proc_txn = len(self.all_txns)
        ratio = total_proc_txn / total_gen_txns
        return ratio

    def _get_network_wide_latency(self, block_num_hash:dict, alpha=0.8):
        """Calculates the average block distribution time

        Args:
            alpha (float, optional): the percentage of peers which must have the block. Defaults to 0.8.
        """
        latencies = {}
        node_time = {} # to store all peers and corresponding time in which they received a specified block
        latency = 0.0
        target_num_nodes = ceil(alpha * len(self.nodes)) - 1 # Exclude the node which mined the block
        block_probs = self.block_props
        nodes = self.nodes
        i = 0

        for num, hash in block_num_hash.items():
            for node in nodes:
                props = block_probs[node.address] # dictionary of block_hash and prop time
                if (props.get(hash) is not None):
                    node_time[i] = props[hash] # store entries using integers to makes it easy to select the value corresponding to the target_num_nodes variable
                    i += 1

            
            if len(node_time) > 0:
                j = 0
                s = sorted(node_time.items(), key=lambda x:x[1])
                t = dict(s)
                for x in t.values():
                    if (j == (target_num_nodes - 1)):
                        latency = x
                    j += 1
                latencies.update({hash: latency})
            
            i = 0
            node_time = {}



    def _get_average_finality_time(self):
        pass

