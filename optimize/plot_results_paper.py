import pickle
from time import gmtime, strftime
import osmnx as ox
import logging
from datetime import datetime
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

def draw_edges(graph):
    edges_fugitive = []

    # for i_r, route_time in enumerate(fugitive_routes):
    #     route = list(route_time.values())
    #     for i, node in enumerate(route):
    #         if i ==0:
    #             continue
    #         else:
    #             edges_fugitive1 = [(route[i], route[i-1])]
    #             edges_fugitive2 = [(route[i-1], route[i])]
    #             edges_fugitive.extend(tuple(edges_fugitive1))
    #             edges_fugitive.extend(tuple(edges_fugitive2))

    edge_colormap = ['lightgray'] * len(graph.edges())
    edge_weightmap = [1] * len(graph.edges())
    for index, edge in enumerate(graph.edges()):
        if edge in edges_fugitive:
            edge_colormap[index] = 'tab:orange'
            edge_weightmap[index] = 2

    return edge_colormap, edge_weightmap


def draw_nodes(G, fugitive_start, escape_nodes, police_start, police_end):
    node_size = []
    node_color = []
    for node in G.nodes:
        if node in police_end:
            node_size.append(120)
            node_color.append('tab:blue')
        elif node in escape_nodes:
            node_size.append(20)
            node_color.append('tab:red')
        # elif node in police_start:
        #     node_size.append(60)
        #     node_color.append('tab:cyan')
        # elif node in police_start:
        #     node_size.append(60)
        #     node_color.append('#51a9ff')
        elif node == fugitive_start:
            node_size.append(40)
            node_color.append('tab:orange')
        else:
            node_size.append(0)
            node_color.append('lightgray')
    return node_size, node_color


# def show_graph(G, escape_nodes, fugitive_start, save=False):
#     # filepath=f"graphs/FLEE/Graph_FLEE.graph.graphml"
#     # G = ox.load_graphml(filepath=filepath)
#
#     edge_colormap, edge_weightmap = draw_edges(G)
#     node_size, node_color = draw_nodes(G, fugitive_start, escape_nodes, police_start, police_end)
#
#     fig, ax = ox.plot_graph(
#         G, bgcolor="white", node_color=node_color, node_size=node_size, edge_linewidth=edge_weightmap,
#         edge_color=edge_colormap,
#     )
#     if save:
#         ax.savefig(f'graphs/{city}.png')


def plot_routes(city, mode, jitter):
    filepath = f"graphs/{city}.graph.graphml"
    G = ox.load_graphml(filepath=filepath)

    with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
        escape_nodes = pickle.load(f)
    with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
        fugitive_start = pickle.load(f)

    # get police routes
    with open(f'data/optimization/start_police_{city}.pkl', 'rb') as f:
        police_start = pickle.load(f)
    if mode == 'hot+cool':
        with open(f'results/optimization/results_positions_{mode}_{city}.pkl', 'rb') as f:
            police_end = pickle.load(f)
    else:
        with open(f'results/optimization/results_positions_{mode}_{city}_jitter{jitter}.pkl', 'rb') as f:
            police_end = pickle.load(f)
    # police_routes = []
    # for u, pol in enumerate(police_start):
    #     path = ox.shortest_path(G, police_start[u], police_end[u])
    #     police_routes.append(path)
    police_routes = [ox.shortest_path(G, police_start[u], police_end[u]) for u, _ in enumerate(police_start)]

    if mode == 'hot+cool':
        results_routes = []
        with open(f'data/results_routes_hot_{city}_jitter{0.05}.pkl', 'rb') as f:
            results_routes_hot = pickle.load(f)
            results_routes += results_routes_hot
        with open(f'data/results_routes_hot_{city}_jitter{0.1}.pkl', 'rb') as f:
            results_routes_hot = pickle.load(f)
            results_routes += results_routes_hot
        with open(f'data/results_routes_cool_{city}_jitter{0.02}.pkl', 'rb') as f:
            results_routes_cool = pickle.load(f)
            results_routes += results_routes_cool
        with open(f'data/results_routes_cool_{city}_jitter{0.05}.pkl', 'rb') as f:
            results_routes_cool = pickle.load(f)
            results_routes += results_routes_cool
    else:
        with open(f'data/results_routes_{mode}_{city}_jitter{jitter}.pkl', 'rb') as f:
            results_routes = pickle.load(f)
    results_routes = [list(route.values()) for route in results_routes]
    # results_routes += police_routes

    if mode == 'hot+cool':
        with open(f'results/optimization/results_intercepted_routes_{mode}_{city}.pkl', 'rb') as f:
            intercepted_routes = pickle.load(f)
    else:
        with open(f'results/optimization/results_intercepted_routes_{mode}_{city}_jitter{jitter}.pkl', 'rb') as f:
            intercepted_routes = pickle.load(f)

    route_colors = ['tab:green' if val == 1 else 'tab:red' if val == 0 else ValueError for val in intercepted_routes.values()]
    # route_colors += ['tab:blue' for pol in police_routes]
    route_alphas = [0.05 for fug in intercepted_routes]
    # route_alphas += [1 for pol in police_routes]
    route_linewidths = [1 for fug in intercepted_routes]
    # route_linewidths += [2 for pol in police_routes]

    if city != 'Winterswijk':
        with open(f'data/cameras_{city}.pkl', 'rb') as f:
            cameras = pickle.load(f)
    elif city == 'Winterswijk':
        cameras = []

    # nx.draw_networkx_edges(G,edgelist=path_edges,edge_color='r',width=10)
    node_size, node_color = draw_nodes(G, fugitive_start, escape_nodes, police_start, police_end)
    edge_colormap, edge_weightmap = draw_edges(G)
    edge_weightmap = [0.3] * len(G.edges())


    fig, ax = ox.plot_graph_routes(G, results_routes,
                                   route_linewidths=route_linewidths, route_alphas=route_alphas, route_colors=route_colors,
                                   edge_linewidth=edge_weightmap, edge_color=edge_colormap,
                                   node_color=node_color, node_size=node_size, node_zorder=2,
                                   bgcolor="white",
                                   orig_dest_size=30,
                                   show=False,
                                   # orig_dest_node_color=['tab:orange', 'tab:red']*len(results_routes),
                                   )

    fig.savefig(f'results/0404_optimization_positions_{city}_{mode}_{jitter}.png', bbox_inches='tight', dpi=300)


if __name__ == '__main__':

    # mode = 'hot+cool'
    # # for city in ['Winterswijk']:
    # for city in ['Manhattan', 'Winterswijk', 'Utrecht']:
    #     for jitter in [0.05]:
    #         plot_routes(city, mode, jitter)
    #         print(strftime("%H:%M:%S", gmtime()), 'done: ', mode, city, jitter)

    mode = 'cool'
    # for city in ['Winterswijk']:
    for city in ['Manhattan', 'Winterswijk', 'Utrecht']:
        for jitter in [0.02, 0.05]:
            plot_routes(city, mode, jitter)
            print(datetime.now().strftime("%H:%M:%S"), 'done: ', mode, city, jitter)


    # mode = 'hot'
    # # for city in ['Manhattan']:
    # # for city in ['Winterswijk']:
    # for city in ['Manhattan', 'Winterswijk', 'Utrecht']:
    #     for jitter in [0.05, 0.1]:
    #         plot_routes(city, mode, jitter)
    #         print(datetime.now().strftime("%H:%M:%S"), 'done: ', mode, city, jitter)



    # mode = 'hot+cool'
    # for city in ['Manhattan', 'Utrecht', 'Winterswijk']:
    # # for city in ['Winterswijk']:
    #     for jitter in [0.05]:
    #         plot_routes(city, mode, jitter)
    #         print(datetime.now().strftime("%H:%M:%S"), 'done: ', mode, city, jitter)

