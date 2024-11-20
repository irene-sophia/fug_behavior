import networkx as nx
import numpy as np
import string
import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd
import pickle



if __name__ == '__main__':
    # city = 'Manhattan'
    # mode = 'hot'
    jitter = 0

    # vary_param = 'trafficlight'
    # param_values = [10, 15, 20, 25, 30, 35, 40]
    # default_value = 20

    for mode in ['cool', 'hot']:
        if mode == 'cool':
            jitter = 0.02
        elif mode == 'hot':
            jitter = 0.05
        # for city in ['Manhattan', 'Utrecht', 'Winterswijk']:
        for city in ['Utrecht']:
            for vary_param in ['camera', 'bridge', 'tunnel', 'trafficlight', 'roundabout']:
                if vary_param == 'camera' and mode == 'cool':
                    # param_values = [10, 15, 20, 25, 30, 35, 40, 50, 55, 60]
                    param_values = [20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
                    default_value = 30
                elif vary_param == 'camera' and mode == 'hot':
                    param_values = [0]
                    default_value = 0
                elif vary_param == 'trafficlight' and mode == 'cool':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
                    default_value = 10
                elif vary_param == 'trafficlight' and mode == 'hot':
                    # param_values = [10, 15, 20, 25, 30, 35, 40]
                    param_values = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
                    default_value = 20
                elif vary_param == 'bridge':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    default_value = 5
                elif vary_param == 'tunnel':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
                    default_value = 10
                elif vary_param == 'roundabout':
                    # param_values = [0, 5, 10, 15, 20, 25, 30]
                    param_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    default_value = 5

                with open(
                        f'../data/sensitivity_analysis/results_routes_{city}_{mode}_{vary_param}_{default_value}_jitter{jitter}.pkl',
                        'rb') as f:
                    default_routes = pickle.load(f)

                default_routes = [list(route.values()) for route in default_routes]
                default_set = set(tuple(row) for row in default_routes)
                default_nodes = set().union(*default_routes)


                shared_route_dict = {}
                num_nodes_dict = {}
                node_overlap_dict = {}
                for val in param_values:
                    with open(f'../data/sensitivity_analysis/results_routes_{city}_{mode}_{vary_param}_{val}_jitter{jitter}.pkl',
                              'rb') as f:
                        routes = pickle.load(f)
                    routes = [list(route.values()) for route in routes]

                    route_set = set(tuple(row) for row in routes)
                    shared_route_dict[val] = len(route_set.intersection(default_set))

                    route_set_ = set().union(*routes)
                    num_nodes_dict[val] = len(route_set_)
                    node_overlap_dict[val] = len(route_set_.intersection(default_nodes))


                fig, (ax0, ax1, ax2) = plt.subplots(nrows=1, ncols=3, sharex=True, figsize=(12, 4))
                colors = ['tab:orange' if val == default_value else 'tab:blue' for val in param_values]

                ax0.set_title('Route overlap', fontsize=10)
                ax0.bar(*zip(*shared_route_dict.items()), color=colors)

                ax1.set_title('Number of nodes', fontsize=10)
                ax1.bar(*zip(*num_nodes_dict.items()), color=colors)

                ax2.set_title('Node overlap', fontsize=10)
                ax2.bar(*zip(*node_overlap_dict.items()), color=colors)

                fig.suptitle(f'{city}, {vary_param}')
                fig.savefig(f'figs/{city}_{mode}_{vary_param}.png', bbox_inches='tight', dpi=300)
