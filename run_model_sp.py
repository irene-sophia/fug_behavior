import logging
import pickle
import random
import time

import networkx as nx
import osmnx as ox

from basic_logger import get_module_logger
from plot_results import plot_routes
from pydsol.core.experiment import SingleReplication
from pydsol.core.simulator import DEVSSimulatorFloat
from model_sp import FugitiveModel

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s (%(name)s - %(filename)s: line %(lineno)s)')

logger = get_module_logger(__name__, level=logging.INFO)

def manhattan_graph(N):
    G = nx.grid_2d_graph(N, N)

    # set x and y
    i = 0
    locations = {}
    for u, v in G.nodes():
        locations[(u, v)] = {"x": u, "y": v}
        i += 1
    nx.set_node_attributes(G, locations)

    # set travel time (unidistant)
    travel_time = 1
    nx.set_edge_attributes(G, travel_time, "travel_time")

    pos = dict((n, n) for n in G.nodes())
    labels = dict(((i, j), i * N + j) for i, j in G.nodes())  #
    labels_inv = dict((i * N + j, (i, j)) for i, j in G.nodes())

    return G, labels, labels_inv, pos



if __name__ == '__main__':
    mode = 'shortest_path'
    seed = 112
    random.seed(seed)
    noise = 0.02

    # graph_type = 'grid'
    #
    # for manhattan_diameter in [10, 30]:
    #
    #     if manhattan_diameter == 10:
    #         fugitive_starts = [(4, 4), (4, 5), (4, 6),
    #                            (5, 4), (5, 5), (5, 4), (5, 5),
    #                            (6, 4), (6, 5), (6, 6),
    #                            ]
    #         run_length = manhattan_diameter
    #     elif manhattan_diameter == 30:
    #         fugitive_starts = [(14, 14), (14, 15), (14, 16),
    #                            (15, 14), (15, 15), (15, 14), (15, 15),
    #                            (16, 14), (16, 15), (16, 16),
    #                            ]
    #         run_length = manhattan_diameter
    #
    #     graph, labels, labels_inv, pos = manhattan_graph(manhattan_diameter)
    #
    #     # escape nodes: all boundary nodes
    #     escape_nodes = [node for node in graph.nodes() if graph.degree[node] != 4]
    #
    #     for instance in range(10):
    #         fugitive_start = fugitive_starts[instance]
    #
    #         route_fugitive = []
    #         while len(route_fugitive) < 100:
    #             for escape_node in escape_nodes:
    #                 try:
    #                     path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time')
    #                     # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
    #                     route_fugitive.append(path)
    #                 except:
    #                     continue
    #
    #         route_fugitive = route_fugitive[:100]
    #
    #         simulator = DEVSSimulatorFloat("sim")
    #         model = FugitiveModel(simulator=simulator,
    #                               input_params={'seed': seed,
    #                                             'graph': graph,
    #                                             'start_fugitive': fugitive_start,
    #                                             'route_fugitive': route_fugitive,
    #                                             'num_fugitive_routes': len(route_fugitive),
    #                                             'jitter': noise,
    #                                             'escape_nodes': escape_nodes,
    #                                             },
    #                               seed=seed)
    #
    #         replication = SingleReplication(str(0), 0.0, 0.0, run_length)
    #         # experiment = Experiment("test", simulator, sim_model, 0.0, 0.0, 700, nr_replications=5)
    #         simulator.initialize(model, replication)
    #         simulator.start()
    #         # Python wacht niet todat de simulatie voorbij is, vandaar deze while loop
    #         while simulator.simulator_time < run_length:
    #             time.sleep(0.01)
    #
    #         routes = model.get_output_statistics()
    #
    #         with open(f'data/results_routes_sp_{graph_type}_N{manhattan_diameter}_instance{instance}.pkl', 'wb') as f:
    #             pickle.dump(routes, f)
    #
    #         # plot_routes(city, mode, jitter)
    #
    #         model.reset_model()

    graph_type = 'city'
    run_length = 1800

    for city in ['Utrecht', 'Winterswijk', 'Manhattan']:
    # for city in ['Manhattan']:
        with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
            escape_nodes = pickle.load(f)

        with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
            fugitive_start = pickle.load(f)

        for instance in range(10):
            graph = ox.load_graphml(filepath=f"graphs/{city}.graph.graphml")

            route_fugitive = []
            while len(route_fugitive) < 100:
                for escape_node in escape_nodes:
                    try:
                        path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time')
                        # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
                        route_fugitive.append(path)
                    except:
                        continue
            route_fugitive = route_fugitive[:100]

            simulator = DEVSSimulatorFloat("sim")
            model = FugitiveModel(simulator=simulator,
                                  input_params={'seed': seed,
                                                'graph': graph,
                                                'start_fugitive': fugitive_start,
                                                'route_fugitive': route_fugitive,
                                                'num_fugitive_routes': len(route_fugitive),
                                                'jitter': noise,
                                                'escape_nodes': escape_nodes,
                                                },
                                  seed=seed)

            replication = SingleReplication(str(0), 0.0, 0.0, run_length)
            # experiment = Experiment("test", simulator, sim_model, 0.0, 0.0, 700, nr_replications=5)
            simulator.initialize(model, replication)
            simulator.start()
            # Python wacht niet todat de simulatie voorbij is, vandaar deze while loop
            while simulator.simulator_time < run_length:
                time.sleep(0.01)

            routes = model.get_output_statistics()

            with open(f'data/results_routes_sp_{graph_type}_{city}_instance{instance}.pkl', 'wb') as f:
                pickle.dump(routes, f)

            # plot_routes(city, mode, jitter)

            model.reset_model()


    # for city in ['Utrecht', 'Winterswijk', 'Manhattan']:
    #     run_length = 1800  # 30 minutes
    # # for city in ['Amsterdam']:
    # # for city in ['Manhattan']:
    #     with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
    #         escape_nodes = pickle.load(f)
    #
    #     with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
    #         fugitive_start = pickle.load(f)
    #
    #     graph = ox.load_graphml(filepath=f"graphs/{city}_prepped.graph.graphml")
    #
    #     travel_time_dict = {}
    #     for u, v, data in graph.edges(data=True):
    #         if 'travel_time_adj' in data.keys():
    #             travel_time_dict[(u, v, 0)] = float(data['travel_time_adj'])
    #         else:
    #             travel_time_dict[(u, v, 0)] = float(data['travel_time'])
    #     nx.set_edge_attributes(graph, travel_time_dict, "travel_time_adj")
    #
    #     for jitter in [0.02, 0.05]:
    #         # import fug routes
    #         with open(f'data/escape_routes_{city}.pkl', 'rb') as f:
    #             route_fugitive = pickle.load(f)
    #
    #         simulator = DEVSSimulatorFloat("sim")
    #         model = FugitiveModel(simulator=simulator,
    #                               input_params={'seed': seed,
    #                                             'graph': graph,
    #                                             'start_fugitive': fugitive_start,
    #                                             'route_fugitive': route_fugitive,
    #                                             'num_fugitive_routes': len(route_fugitive),
    #                                             'jitter': jitter,
    #                                             'escape_nodes': escape_nodes,
    #                                             },
    #                               seed=seed)
    #
    #         replication = SingleReplication(str(0), 0.0, 0.0, run_length)
    #         # experiment = Experiment("test", simulator, sim_model, 0.0, 0.0, 700, nr_replications=5)
    #         simulator.initialize(model, replication)
    #         simulator.start()
    #         # Python wacht niet todat de simulatie voorbij is, vandaar deze while loop
    #         while simulator.simulator_time < run_length:
    #             time.sleep(0.01)
    #
    #         routes = model.get_output_statistics()
    #
    #         with open(f'data/results_routes_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(routes, f)
    #
    #         # plot_routes(city, mode, jitter)
    #
    #         model.reset_model()
