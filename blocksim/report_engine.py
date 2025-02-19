import json
from math import ceil

import numpy
from blocksim.models import node as Node
from csv import writer


class ReportEngine:
    
    def __init__(self, nodes:list, env_data=None):
        self.nodes = nodes
        self.any_node:Node.Node = self.nodes[0]
        self.blocks = self.any_node.blocks_in_chain

        for n in nodes:
            # pick out the node with the longest chain
            if n.chain.head.header.number > self.any_node.chain.head.header.number:
                self.any_node = n
                self.blocks = self.any_node.blocks_in_chain

        self.proc_times = []
        self.all_txns = []
        self.block_num_hash = {}

        if env_data is not None:
            self.env_data = env_data
            self.tx_prop = self.env_data['tx_propagation'] # simulation output
            self.block_prop = self.env_data['block_propagation'] # simulation output

        self.block_props = {} # extracted from simulation output, per peer
        self.block_receive_times = {}

        self._get_block_number_and_hash(self.blocks)
        self._get_blocks_prop_times(self.nodes, self.block_prop)
        self._get_block_receive_times(self.nodes, self.block_prop)
        self._get_network_wide_latency()
        self._get_average_finality_time()

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
                split = [f"{split[0]}_{split[1]}", f"{split[2]}_{split[3]}"]
                if ((split[1] == address) and (len(block_prop[key]) > 0) ):
                    for k,v in block_prop[key].items():
                        if blocks_and_times.get(k) is None:
                            if type(v) is tuple:
                                for b in v:
                                    is_float_val = type(b) is numpy.float64
                                    if is_float_val:
                                        blocks_and_times[k] = v[1] + v[0]
                                    else:
                                        c = b
                                        a = c[0]
                                        is_float_val = type(a) is numpy.float64
                                        while is_float_val is False:
                                            c = a
                                            a = a[0]
                                            is_float_val = type(a) is numpy.float64
                                        blocks_and_times[k] = c[1] + c[0]
                                        break
            block_receive_time_all_node[address] = blocks_and_times
        self.block_receive_times = block_receive_time_all_node


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
                split = [f"{split[0]}_{split[1]}", f"{split[2]}_{split[3]}"]
                if ((split[1] == address) and (len(block_prop[key]) > 0) ):
                    for k,v in block_prop[key].items():
                        if blocks_and_times.get(k) is None:
                            if type(v) is tuple:
                                for b in v:
                                    is_float_val = type(b) is numpy.float64
                                    if is_float_val:
                                        blocks_and_times[k] = v[1]
                                    else:
                                        c = b
                                        a = c[0]
                                        is_float_val = type(a) is numpy.float64
                                        while is_float_val is False:
                                            c = a
                                            a = a[0]
                                            is_float_val = type(a) is numpy.float64
                                        blocks_and_times[k] = c[1]
                                        break


                                # blocks_and_times[k] = v[1]
                                # if (type(blocks_and_times[k]) is numpy.ndarray):
                                #     a = v[0]
                                #     blocks_and_times[k] = a[1]  
            
            
            # for k,v in blocks_and_times.items():
            #     if (type(blocks_and_times[k]) is numpy.ndarray):
            #                         a = v[0]
            #                         blocks_and_times[k] = a[1]
            #     if (blocks_and_times[k] > 9999):
            #         blocks_and_times.pop(k)

            block_props_all_node[address] = blocks_and_times
        self.block_props = block_props_all_node





    # def get_global_txn_report(self):
    #     pass

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

    def get_txn_report(self, sim_duration:float):
        av_txn_latency = self._get_average_txn_proc_time()
        txn_throughput = self.get_transaction_throughput(sim_duration)
        txn_proc_ratio = self.get_transactions_processing_ratio()
        tx_metrics = {}
        tx_metrics["av_txn_latency"] = av_txn_latency
        tx_metrics["txn_throughput"] = txn_throughput
        tx_metrics["txn_proc_ratio"] = txn_proc_ratio

        with open("reports/av_txn_latency.csv", "a") as csvfile:
            my_wirter = writer(csvfile, delimiter=",")
            my_wirter.writerow([av_txn_latency])
        
        with open("reports/txn_throughput.csv", "a") as csvfile:
            my_wirter = writer(csvfile, delimiter=",")
            my_wirter.writerow([txn_throughput])
        
        with open("reports/txn_proc_ratio.csv", "a") as csvfile:
            my_wirter = writer(csvfile, delimiter=",")
            my_wirter.writerow([txn_proc_ratio])

        # with open(f"reports/txn.json", 'w') as f:
        #     f.write(json.dumps(tx_metrics))

    def _get_average_txn_proc_time(self):
        
        blocks = self.any_node.blocks_in_chain
        for block in blocks:
            if block.transactions is not None:
                for txn in block.transactions:
                    self.all_txns.append(txn)
                    self.proc_times.append(txn.proc_time - txn.gen_time)
        # average_processing_time = sum(self.proc_times) / len(self.proc_times)
        average_processing_time = numpy.average(self.proc_times)
        return (average_processing_time)

    def get_transaction_throughput(self, sim_duration:float):
        throughput = len(self.all_txns) / sim_duration
        return throughput

    def get_transactions_processing_ratio(self, total_gen_txns=40000):
        total_proc_txn = len(self.all_txns)
        ratio = total_proc_txn / total_gen_txns
        return ratio

    def _get_block_creation_time(self, block_hash:str):
        # hash = block_hash
        for block in self.blocks:
            if (block_hash == block.header.hash[:8]):
                return block.header.timestamp

    def _get_network_wide_latency(self, alpha=0.8):
        """Calculates the average block distribution time

        Args:
            block_num_hash (dict): a dictionary containing hashes of all blocks
            alpha (float, optional): alpha (float, optional): the percentage of peers which must have the block. Defaults to 0.8.
        """
        latencies = {}
        node_time = {} # to store all peers and corresponding time in which they received a specified block
        latency = 0.0
        target_num_nodes = ceil(alpha * len(self.nodes)) - 1 # Exclude the node which mined the block
        block_probs = self.block_props
        block_receive_time = self.block_receive_times
        block_creation_time = 0.0
        nodes = self.nodes
        i = 0

        for num, hash in self.block_num_hash.items():
            block_creation_time = self._get_block_creation_time(hash)
            for node in nodes:
                rec_time = block_receive_time[node.address] # dictionary of block_hash and prop time
                if (rec_time.get(hash) is not None):
                    node_time[i] = rec_time[hash] # store entries using integers to makes it easy to select the value corresponding to the target_num_nodes variable
                    i += 1

            
            if len(node_time) > 0:
                j = 0
                s = sorted(node_time.items(), key=lambda x:x[1])
                t = dict(s)
                latency = t[len(t) - 1]
                target_num_nodes = ceil(alpha * len(t)) - 1 # Exclude the node which mined the block
                for x in t.values():
                    if (j == (target_num_nodes - 1)):
                        latency = x - block_creation_time
                    j += 1
                latencies.update({num: latency})
            
            i = 0
            node_time = {}
        av_net_lat = numpy.average(list(latencies.values()))
        with open("reports/latencies.csv", "a") as csvfile:
            my_wirter = writer(csvfile, delimiter=",")
            my_wirter.writerow([av_net_lat])
            # my_wirter.writerows(latencies.items())
        return latencies



    def _get_average_finality_time(self, delta=6):
        # time difference between the creation of a block and six consecutive blocks
        t1 = 0.0
        t2 = 0.0
        finality_time = 0.0
        i1 = 1   # we exclude the genesis block
        i2 = i1 + delta
        hash1 = ""
        hash2 = ""
        block_hashes = self.block_num_hash
        finality_times = {}

        chain_length = len(self.blocks)
        while i2 < chain_length:
            hash1 = block_hashes[i1]
            hash2 = block_hashes[i2]
            t1 = self._get_block_creation_time(hash1)
            t2 = self._get_block_creation_time(hash2)
            finality_time = t2 - t1
            finality_times[i1] = finality_time
            
            i1 += 1
            i2 = i1 + delta
        av_av_fin_time = numpy.average(list(finality_times.values()))
        with open("reports/finality.csv", "a") as csvfile:
            my_wirter = writer(csvfile, delimiter=",")
            my_wirter.writerow([av_av_fin_time])
            # my_wirter.writerows(finality_times.items())
        return finality_times




