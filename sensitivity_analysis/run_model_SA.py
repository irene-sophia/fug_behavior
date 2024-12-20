import logging
import pickle
import random
import time

import networkx as nx
import osmnx as ox

from basic_logger import get_module_logger
# from plot_results import plot_routes
from pydsol.core.experiment import SingleReplication
from pydsol.core.simulator import DEVSSimulatorFloat
from model_cool import FugitiveModel

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s (%(name)s - %(filename)s: line %(lineno)s)')

logger = get_module_logger(__name__, level=logging.INFO)

if __name__ == '__main__':
    mode = 'cool'

    run_length = 1800  # 30 minutes

    vary_param = 'camera'

    for mode in ['cool', 'hot']:
        for city in ['Manhattan', 'Utrecht', 'Winterswijk']:
            for vary_param in ['camera', 'bridge', 'tunnel', 'trafficlight', 'roundabout']:
                if vary_param == 'camera' and mode == 'cool':
                    # param_values = [10, 15, 20, 25, 30, 35, 40, 50, 55, 60]
                    param_values = [20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
                elif vary_param == 'camera' and mode == 'hot':
                    param_values = [0]
                elif vary_param == 'trafficlight' and mode == 'cool':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
                elif vary_param == 'trafficlight' and mode == 'hot':
                    # param_values = [10, 15, 20, 25, 30, 35, 40]
                    param_values = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
                elif vary_param == 'bridge':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                elif vary_param == 'tunnel':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
                elif vary_param == 'roundabout':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

                for param_value in param_values:
                    seed = 112
                    random.seed(seed)

                    with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
                        escape_nodes = pickle.load(f)

                    with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
                        fugitive_start = pickle.load(f)

                    graph = ox.load_graphml(filepath=f"graphs/sensitivity_analysis/{city}_{mode}_{vary_param}_{param_value}.graph.graphml")

                    travel_time_dict = {}
                    for u, v, data in graph.edges(data=True):
                        if 'travel_time_adj' in data.keys():
                            travel_time_dict[(u, v, 0)] = float(data['travel_time_adj'])
                        else:
                            travel_time_dict[(u, v, 0)] = float(data['travel_time'])
                    nx.set_edge_attributes(graph, travel_time_dict, "travel_time_adj")

                    if mode == 'hot':
                        # jitters = [0.05, 0.1]
                        jitters = [0]
                        jitters = [0.05]
                    elif mode == 'cool':
                        # jitters = [0.02, 0.05]
                        jitters = [0]
                        jitters = [0.02]
                    for jitter in jitters:
                        # import fug routes
                        with open(f'data/sensitivity_analysis/escape_routes_{city}_{mode}_{vary_param}_{param_value}.pkl', 'rb') as f:
                            route_fugitive = pickle.load(f)

                        simulator = DEVSSimulatorFloat("sim")
                        model = FugitiveModel(simulator=simulator,
                                              input_params={'seed': seed,
                                                            'graph': graph,
                                                            'start_fugitive': fugitive_start,
                                                            'route_fugitive': route_fugitive,
                                                            'num_fugitive_routes': len(route_fugitive),
                                                            'jitter': jitter,
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

                        with open(f'data/sensitivity_analysis/results_routes_{city}_{mode}_{vary_param}_{param_value}_jitter{jitter}.pkl', 'wb') as f:
                            pickle.dump(routes, f)

                        # plot_routes(city, mode, jitter)

                        model.reset_model()
