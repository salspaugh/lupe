import pygraphviz as pgv
import lupe.statemachines.tokens

NEGLIGIBLE = "Negligible"

GRAPH_ATTRS = {
    "directed": True,
    "rankdir": "LR",
}

NODE_ATTRS = {
    "color": "",
    "style": "",
    "shape": "circle",
    "height": ".8",
    "fontname": "Bitstream Vera Sans",
    "fontsize": 8
}

EDGE_ATTRS = {
    "fontsize": 16,
    "fontname": "Bitstream Vera Sans"
}

def make_diagram(graph, threshold, output):
    plot = pgv.AGraph(**GRAPH_ATTRS)
    
    seen = set()
    has_incoming = set()
    has_outgoing = set()

    # Add nodes.
    for src in graph.iterkeys():
        seen.add(src)
        add_node(plot, src)

    # Add edges.
    for (src, dsts) in graph.iteritems():
        for (dst, weight) in dsts.iteritems():
            if weight < threshold: continue
            if not dst in seen:
                seen.add(dst)
                add_node(plot, src, start=start, end=end)
            if not src == dst:
                has_incoming.add(dst)
                has_outgoing.add(src)
            add_edge(plot, src, dst, weight)

    # Make sure all edges have an incoming and outgoing edge.
    for node in seen:
        if node not in has_incoming:
            srcs = {}
            for (src, dsts) in graph.iteritems():
                for (dst, weight) in dsts.iteritems():
                    if dst == node and not src == dst:
                        srcs[src] = weight
            if len(srcs) > 0:
                s = sorted(srcs.items(), key=lambda x: x[1], reverse=True)[0][0]
                add_edge(plot, s, node, NEGLIGIBLE)
        if node not in has_outgoing:
            dsts = graph[node]
            dsts = sorted(dsts.items(), key=lambda x: x[1], reverse=True)
            dsts = filter(lambda x: x[0] != node, dsts)
            d = dsts[0][0]
            add_edge(plot, node, d, NEGLIGIBLE)

    plot.draw(output, prog="dot") 

def add_node(graph, node):
    color = NODE_ATTRS["color"]
    style = NODE_ATTRS["style"] 
    if node == lupe.statemachines.tokens.START_TOKEN:
        color = '#74c476' # green
        style = "filled"
    if node == lupe.statemachines.tokens.END_TOKEN:
        color = '#ef6548' # red
        style = "filled"
    graph.add_node(n=node, 
        style=style,
        color=color,    
        shape=NODE_ATTRS["shape"],
        height=NODE_ATTRS["height"],
        fontname=EDGE_ATTRS["fontname"], 
        fontsize=NODE_ATTRS["fontsize"])

def add_edge(graph, src, dst, weight):
    if weight == NEGLIGIBLE:
        graph.add_edge(src, dst, label=weight,
        fontname=EDGE_ATTRS["fontname"], 
        fontsize=EDGE_ATTRS["fontsize"],
        style="dotted")
    else:
        graph.add_edge(src, dst, label="%.2f" % weight, 
        fontname=EDGE_ATTRS["fontname"], 
        fontsize=EDGE_ATTRS["fontsize"],
        style="setlinewidth("+str(float(weight)*5)+")")
