''' Calculates voltages on the transformer LV
Used for determining appropriate transformer tap range
'''
import powerfactory as pf
import pandas as pd
import importlib
import search
importlib.reload(search)
from search import *
import heapq

class LCFSFrontier(Frontier):
    def __init__(self):
        self.container = []
        self.visited = set()
        self.expanded = set()

    def add(self, path):
        """Adds a new path to the frontier. A path is a sequence (tuple) of
        Arc objects. You should override this method.

        """
        if path[-1].head not in self.visited:
                self.container.append(path)
        #heapq.heapify(self.container)
        if path[-1].tail not in self.expanded:
            if path[-1].tail:
                self.expanded.add(path[-1].tail)

    def __iter__(self):

        while len(self.container) > 0:
            heap = []
            for x,item in enumerate(self.container):
                heap.append((sum(arc.cost for arc in item),x))
            #print(heap)
            heapq.heapify(heap)
            index = heap[0][1]
            if heap[0][0] > 50:
                Globals.app.PrintPlain(heap[0][0])
                return None
            #print(index)
            #print(self.container[0][0].cost)
            if self.container[index][-1].head in self.visited:
                #don't yield it and prune by popping it
                self.container.pop(index)

            else:
                #found a non visited path, add the node to the visited list
                self.visited.add(self.container[index][-1].head)
                yield self.container.pop(index)



class DFSFrontier(Frontier):
    """Implements a frontier container appropriate for depth-first
    search."""

    def __init__(self):
        """The constructor takes no argument. It initialises the
        container to an empty list."""
        self.container = []


    def add(self, path):
        #Add the path to the frontier container.
        self.container.append(path)


    def __iter__(self):
        #Pop (return and remove) the path from the end of the frontier
        #(DFS stack).
        while len(self.container) > 0:
            yield self.container.pop()

class BFSFrontier(Frontier):
    """Implements a frontier container appropriate for breadth-first
    search."""

    def __init__(self):
        """The constructor takes no argument. It initialises the
        container to an empty list."""
        self.container = []


    def add(self, path):
        #Add the path to the frontier container.
        self.container.append(path)


    def __iter__(self):
        #Pop (return and remove) the path from the end of the frontier
        #(BFS queue).
        while len(self.container) > 0:
            yield self.container.pop(0)

class NetGraph(Graph):
    def __init__(self, nodelist):
        #print(self.map_str)
        self.starting_list = []
        self.nodelist = nodelist
        self.zone = nodelist[0].cpZone

    def starting_nodes(self):
        """Finds the positions of all the agents and returns them as tuples
        to the list of
        starting_nodes"""
        yield self.nodelist[0]

    def is_goal(self, node, last_arc):
        #Globals.app.PrintPlain(node)
        #obj = cubicle.obj_id
        #Globals.app.PrintPlain(node)
        return last_arc.GetClassName() == "ElmCoup" \
               and last_arc.loc_name[:3] == self.zone.loc_name[:3]

        #print(self.mapwidth)
        #print(self.mapheight)
        #print(self.barriers)
    def outgoing_arcs(self, node):
        cubs = node.GetConnectedCubicles()
        for cub in cubs:
            #Globals.app.PrintPlain(cub)
            label, head = self.check_valid_cubicle(cub)
            if head is not False:
                tail = node
                yield Arc(tail, head, label, 1)

    def check_valid_cubicle(self, cub):
        #Globals.app.PrintPlain(cub)
        bus_index = cub.obj_bus
        conn_element = cub.obj_id
        if bus_index == 1:
            remote_cub = conn_element.GetCubicle(0)
        else:
            remote_cub = conn_element.GetCubicle(1)
        if remote_cub:
            if remote_cub.IsClosed():
                node = remote_cub.GetParent()
                if not node.cpZone:
                    return conn_element, node
                elif node.cpZone == self.zone:
                    return conn_element, node
        return "", False

class Globals():
    app = pf.GetApplication()

def print_actions(path):
    """Given a path (a sequence of Arc objects), prints the actions
    (arc labels) that need to be taken and the total cost of those
    actions. The path is usually a solution (a path from the starting
    node to a goal node."""

    if path:
        Globals.app.PrintPlain(path)
        Globals.app.PrintPlain("Actions:")
        Globals.app.PrintPlain(",\n".join("  {}".format(arc.label) for arc in path[1:]) + ".")
        Globals.app.PrintPlain(f"Total cost: {sum(arc.cost for arc in path)}")
    else:
        Globals.app.PrintPlain("There is no solution!")

def get_zones():
    """Gets the zone objects from the project"""
    zonefld = Globals.app.GetDataFolder("ElmZone")
    zones = zonefld.GetContents()
    #for zone in zones:
        #Globals.app.PrintPlain(zone)
    return zones

def get_parent_switch(zone):
    """Gets the parent switch in a zone"""
    #Get all the objects in the zone
    objs = zone.GetAll()
    #Get all terms
    zone_terms = []
    for item in objs:
        if item.GetClassName() == "ElmTerm":
            zone_terms.append(item)
    #Globals.app.PrintPlain(zone_terms)
    if len(zone_terms) > 0:
        graph = NetGraph(zone_terms)
        #Globals.app.PrintPlain(graph.starting_list)
        #Globals.app.PrintPlain("Outgoing arcs (available actions) at starting states:")
        # for s in sorted(graph.starting_nodes(), key= lambda x: x.loc_name):
        #    Globals.app.PrintPlain(s)
        #    for arc in graph.outgoing_arcs(s):
        #        Globals.app.PrintPlain("  " + str(arc))

        solutions = generic_search(graph, LCFSFrontier())
        solution = next(solutions, None)
        print_actions(solution)
        if solution:
            return solution[-1]
    else:
        return None

def find_target_cub(path, zone):
    tail, head, switch, cost = path
    Globals.app.PrintPlain(switch)
    #Globals.app.PrintPlain(switch)
    #Globals.app.PrintPlain(tail)
    #Globals.app.PrintPlain(head)
    #Globals.app.PrintPlain(cost)
    #get the cubicles from the switch to find which one to create the feeder on
    #check switch matches zone name
    if switch == "no action":
        return None

    if zone.loc_name[:3] == switch.loc_name[:3]:

        cub1 = switch.GetCubicle(0)
        cub2 = switch.GetCubicle(1)

        if cub1.GetParent().cpSubstat:
            #Globals.app.PrintPlain("Found cub at head")
            return cub1
        elif cub2.GetParent().cpSubstat:
            #Globals.app.PrintPlain("Found cub at tail")
            return cub2
    else:
        return None

def main():
    '''The main function'''
    Globals.app.ClearOutputWindow()
    zones = get_zones()
    feedfld = Globals.app.GetDataFolder("ElmFeeder")
    for zone in zones:
        Globals.app.PrintPlain(f"Searching for head switch of {zone}")
        path = get_parent_switch(zone)
        if path:
            tail, head, switch, cost = path
            cub = find_target_cub(path, zone)
            Globals.app.PrintPlain(cub)
            if cub:
                net = switch.GetParent()
                feeder = feedfld.CreateObject("ElmFeeder", zone.loc_name)
                feeder.obj_id = cub
                feeder.icolor = zone.icolor
                feeder.i_scale = 4 #manual scaling
                feeder.scale0 = zone.curscale
                zone.Delete()

if __name__ == '__main__':
    main()
