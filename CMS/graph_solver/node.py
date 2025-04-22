"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
class Node:
    def __init__(self, name: str, capacity: int, is_outer = False):
        self.name = name
        self.near_nodes = []
        self.is_outer = is_outer
        self.capacity = capacity
        self.current_occupancy = 0
    
    def add_connection(self, node: 'Node') -> None:
        """Add a bidirectional connection between nodes"""
        if node not in self.near_nodes:
            self.near_nodes.append(node)
            node.near_nodes.append(self)
    
    def get_occupancy_rate(self) -> float:
        """Return the current occupancy rate as a percentage"""
        return (self.current_occupancy / self.capacity * 100) if self.capacity > 0 else 100
    
    def is_viable_route(self) -> bool:
        """Check if the node is viable for emergency routing"""
        return self.get_occupancy_rate() <= 70
    
    def __repr__(self) -> str:
        return f"Node({self.name}, {self.current_occupancy}/{self.capacity}, is_outer={self.is_outer}, connected={[node.name for node in self.near_nodes]})"