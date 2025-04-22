"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
from collections import deque
from ..room import Room
from ..utils import logger
from typing import List, Set, Dict, Optional, Tuple
from .node import Node

def find_best_paths(start_node: Node, outer_nodes: Set[Node]) -> Dict[Node, Tuple[List[Node], bool]]:
    """
    Find the shortest paths from start_node to all outer nodes using BFS.
    Returns a dictionary mapping each outer node to (path, is_high_occupancy_path).
    """
    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    paths: Dict[Node, Tuple[List[Node], bool]] = {}
    high_occupancy_paths: Dict[Node, List[Node]] = {}
    
    while queue and (len(paths) + len(high_occupancy_paths)) < len(outer_nodes):
        current_node, current_path = queue.popleft()
        
        # If we found an outer node
        if current_node in outer_nodes:
            path_has_high_occupancy = any(
                not node.is_viable_route() 
                for node in current_path[1:-1]  # Exclude start and end nodes
            )
            
            if path_has_high_occupancy:
                if current_node not in paths:  # Only store if we don't have a better path
                    high_occupancy_paths[current_node] = current_path
            else:
                paths[current_node] = (current_path, False)
                if current_node in high_occupancy_paths:
                    del high_occupancy_paths[current_node]
            continue
        
        # Explore neighbors
        for neighbor in current_node.near_nodes:
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = current_path + [neighbor]
                queue.append((neighbor, new_path))
    
    # If we have no viable paths, use high occupancy paths
    if not paths and high_occupancy_paths:
        return {node: (path, True) for node, path in high_occupancy_paths.items()}
    
    return paths

def get_optimal_path(start_node: Node, outer_nodes: Set[Node]) -> Tuple[Optional[List[Node]], bool]:
    """
    Find the shortest viable path to any outer node.
    Returns (path, is_high_occupancy_path). Returns (None, False) if no path found.
    """
    paths = find_best_paths(start_node, outer_nodes)
    if not paths:
        return None, False
    
    # First try to find the shortest path among viable routes
    viable_paths = [(path, high_occ) for path, high_occ in paths.values() if not high_occ]
    if viable_paths:
        return min(viable_paths, key=lambda x: len(x[0]))
    
    # If no viable paths exist, use the shortest high-occupancy path
    return min(paths.values(), key=lambda x: len(x[0]))

def rooms_to_nodes(rooms: dict[str, Room]):
    nodes: dict[str, Node] = {}


    for room_id in rooms:
        room: Room = rooms[room_id]
        nodes[room_id] = Node(room.room_name, room.room_capacity, room.is_exit)
    
    for room_id in nodes:
        room: Room = rooms[room_id]
        for conn_id in room.connected_roomids:
            nodes[room_id].add_connection(nodes[conn_id])
    
    logger.debug(f"Nodes: {nodes}")
    
    return nodes