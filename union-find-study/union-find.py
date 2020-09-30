# Python Program for union-find algorithm to detect cycle in a undirected graph
# we have one egde for any two vertex i.e 1-2 is either 1-2 or 2-1 but not both

from collections import defaultdict


# This class represents a undirected graph using adjacency list representation
class Graph:
    def __init__(self, nodes):
        self.nodes = nodes
        self.graph = defaultdict(list)

    def addEdge(self, u, v):
        self.graph[u].append(v)

    def find_parent(self, parent, i):
        """find the subset of an element i"""
        if parent[i] == -1:
            return i
        if parent[i] != -1:
            return self.find_parent(parent, parent[i])

    def union(self, parent, x, y):
        """union of two subsets"""
        x_set = self.find_parent(parent, x)
        y_set = self.find_parent(parent, y)
        parent[x_set] = y_set

    def isCyclic(self):
        # Allocate memory to track subsets of nodes, starting with the
        # maximum possible number of subsets; single node sets
        parent = [-1] * (self.nodes)

        # Iterate through all edges of graph, find subset of both
        # nodes of every edge, if both subsets are same, then
        # there is cycle in graph.
        for i in self.graph:
            for j in self.graph[i]:
                print(f"c {j}")
                x = self.find_parent(parent, i)
                print(f"x {x}")
                y = self.find_parent(parent, j)
                print(f"y {y}")
                if x == y:
                    return True
                self.union(parent, x, y)


# Create a graph given in the above diagram
g = Graph(3)
g.addEdge(0, 1)
g.addEdge(1, 2)
g.addEdge(2, 0)

if g.isCyclic():
    print("Graph contains cycle")
else:
    print("Graph does not contain cycle")

# This code is contributed by Neelam Yadav
