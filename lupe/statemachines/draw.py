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
    nodes = set()
    incoming = set()
    for src in graph.iterkeys():
        nodes.add(src)
        add_node(plot, src)
    for (src, dsts) in graph.iteritems():
        for (dst, weight) in dsts.iteritems():
            if weight < threshold: continue
            if not dst in nodes:
                add_node(plot, dst)
                incoming.add(dst)
            add_edge(plot, src, dst, weight)
    for (src, dsts) in graph.iteritems():
        for (dst, weight) in dsts.iteritems():
            if dst not in incoming:
                srcs = { source: weight for source in graph if dst in graph[source] }
                s = sorted(srcs.items(), key=lambda x: x[1], reverse=True)[0][0]
                add_edge(plot, s, dst, NEGLIGIBLE)
                incoming.add(dst)
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
