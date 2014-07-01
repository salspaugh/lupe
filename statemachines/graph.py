from fsm import State, FiniteStateMachine, get_graph
from json import load

THRESHOLD = 0.2  # Change to 0 if you want to show all edges
EDGE_FORMAT = "{:.2f}"

def create_fsm(label, datafilename, threshold=THRESHOLD):
    fsm = FiniteStateMachine('Query Relations')
    states = {
        "<start>": State('Start', initial=True),
        "Aggregate": State('Aggregate'),
        "Cache": State('Cache'),
        "Augment":  State('Augment'),
        "Filter": State('Filter'),
        "Read Metadata": State(r'Read\nMetadata'),
        "Input": State('Input'),
        "Join": State('Join'),
        "Macro": State('Macro'),
        "Meta": State('Meta'),
        "Miscellaneous": State('Misc'),
        "Output": State('Output'),
        "Project": State('Project'),
        "Rename": State('Rename'),
        "Reorder": State('Reorder'),
        "User-Defined": State(r'User\nDefined'),
        "Transform": State('Transform'),
        "Transpose": State('Transpose'),
        "Set": State('Set'),
        "Window": State('Window'),
        "<end>": State('End')
    }

    remaining_dsts = ['Aggregate', 'Cache', 'Augment', "Filter",
             "Input", "Join", 'Macro', 'Meta', "Miscellaneous", 'Output',
             "Project", 'Read Metadata', 'Rename', 'Reorder', 'User-Defined', "Transform",
             'Transpose', 'Set', 'Window']
    remaining_srcs = ['Aggregate', 'Cache', 'Augment', "Filter",
             "Input", "Join", 'Macro', 'Meta', "Miscellaneous", 'Output',
             "Project", 'Read Metadata', 'Rename', 'Reorder', 'User-Defined', "Transform",
             'Transpose', 'Set', 'Window']

    graph_data = read_graph_data(datafilename)

    title = graph_data["title"]
    title = State(title)
    
    edges = graph_data["edges"] 
    # Add edges that are heavier than the threshold.
    for (edge, weight) in edges:
        if weight < threshold: break
        weight = EDGE_FORMAT.format(weight)
        (src, dst) = edge
        if src in remaining_srcs and src != dst:
            remaining_srcs.remove(src)
        if dst in remaining_dsts and src != dst:
            remaining_dsts.remove(dst)
        states[src][(tuple(edge), weight)] = states[dst]

    # Make sure all nodes have at least one ingoing and outgoing edge.
    for (edge, weight) in edges:
        (src, dst) = edge
        found = False
        if src in remaining_srcs and src != dst:
            remaining_srcs.remove(src)
            found = True
        if dst in remaining_dsts and src != dst:
            remaining_dsts.remove(dst)
            found = True
        if found:
            weight = EDGE_FORMAT.format(float(weight))
            states[src][(tuple(edge), weight)] = states[dst]

    missing = []
    for state in remaining_dsts:
        missing.append(states[state].name)

    filename = "%s-%s.png" % (label, str(threshold))
    get_graph(fsm, title=title, missing=missing).draw(filename, prog='dot')

def read_graph_data(filename):
    with open(filename) as f:
        return load(f)
