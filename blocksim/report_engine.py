
from blocksim.models import node as Node

class ReportEngine:
    
    def __int__(self, nodes:list(Node)):
        self.nodes = nodes

    def get_global_txn_report(self):
        pass

    def get_global_block_report(self):
        pass

    def _get_peer_txn_report(self):
        pass

    def _get_peer_block_report(self):
        pass

    def _get_average_txn_dist_latency(self):
        pass

    def _get_average_txn_proc_time(self):
        pass

    def _get_average_block_dist_latency(self):
        pass

    def _get_average_finality_time(self):
        pass

