import pickle
import numpy as np
import osmnx as ox

from ema_workbench import MultiprocessingEvaluator, SequentialEvaluator
from ema_workbench import RealParameter, ScalarOutcome, Constant, Model
from ema_workbench.em_framework.optimization import ArchiveLogger, SingleObjectiveBorgWithArchive

from optimize.sort_and_filter import sort_and_filter_pol_fug_city as sort_and_filter_nodes
from optimize.unit_ranges import unit_ranges

import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)


def FIP_model(route_fugitive_labeled=None, run_length=None, tau_uv=None, labels_full_sorted=None, labels_sorted=None,
              labels_sorted_inv=None,
              **kwargs):
    pi_uv = {}
    z_r = {}
    pi_nodes = []

    for u, value in enumerate(list(kwargs.values())):
        associated_node = labels_sorted_inv[int(u)][int(np.floor(value))]
        pi_nodes.append(labels_full_sorted[associated_node])

    for i_r, _ in enumerate(route_fugitive_labeled):
        z_r[i_r] = 0

    for i_r, r in enumerate(route_fugitive_labeled):  # for each route
        if any([node in pi_nodes for node in r.values()]):
            for u, pi in enumerate(pi_nodes):  # for each police unit
                for time_at_node_fugitive, node_fugitive in r.items():  # for each node in the fugitive route
                    if node_fugitive == pi:  # if the fugitive node is the same as the target node of the police unit
                        if time_at_node_fugitive > tau_uv[u, node_fugitive]:  # and the police unit can reach that node
                            z_r[i_r] = 1  # intercepted

    return [float(sum(z_r.values()))]


def get_intercepted_routes(route_fugitive_labeled, tau_uv, labels_full_sorted, labels_sorted_inv, results_positions):
    z_r = {}
    pi_nodes = []

    for u, value in enumerate(results_positions):
        associated_node = labels_sorted_inv[int(u)][int(np.floor(value))]
        pi_nodes.append(labels_full_sorted[associated_node])

    for i_r, _ in enumerate(route_fugitive_labeled):
        z_r[i_r] = 0

    for i_r, r in enumerate(route_fugitive_labeled):  # for each route
        if any([node in pi_nodes for node in r.values()]):
            for u, pi in enumerate(pi_nodes):  # for each police unit
                for time_at_node_fugitive, node_fugitive in r.items():  # for each node in the fugitive route
                    if node_fugitive == pi:  # if the fugitive node is the same as the target node of the police unit
                        if time_at_node_fugitive > tau_uv[u, node_fugitive]:  # and the police unit can reach that node
                            z_r[i_r] = 1  # intercepted

    # print(sum(z_r.values())/500)

    # for r in range(len(route_fugitive_labeled)):
    #     z_r[r] = sum(sum(sum(pi_uv[u, v] * phi_rt[r, t, v] * tau_uv[u, t, v] for v in labels_full_sorted.values()) for u in range(U)) for t in range(run_length))

    return z_r


def optimize(city, mode, jitter, results_routes, police_stations, delays, run_length):
    filepath = f"graphs/{city}.graph.graphml"
    G = ox.load_graphml(filepath=filepath)

    with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
        escape_nodes = pickle.load(f)

    with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
        fugitive_start = pickle.load(f)

    if city != 'Winterswijk':
        with open(f'data/cameras_{city}.pkl', 'rb') as f:
            cameras = pickle.load(f)
    elif city == 'Winterswijk':
        cameras = []

    # sort indices on distance to start_fugitive
    labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted = sort_and_filter_nodes(G,
                                                                                                 fugitive_start,
                                                                                                 results_routes,
                                                                                                 police_stations,
                                                                                                 run_length)

    route_fugitive_labeled = []
    for r in results_routes:
        r_labeled = {x: labels_full_sorted[y] for x, y in r.items()}
        route_fugitive_labeled.append(r_labeled)

    tau_uv = unit_ranges(start_units=police_stations, delays=delays, U=len(police_stations), G=G, L=run_length,
                         labels_full_sorted=labels_full_sorted)

    problem_name = f'{city}_{mode}_jitter{jitter}'

    upper_bounds = []
    for u in range(len(police_stations)):
        if len(labels_perunit_sorted[u]) <= 1:
            upper_bounds.append(0.999)
        else:
            upper_bounds.append(len(labels_perunit_sorted[u]) - 0.001)  # different for each unit

    model = Model("FIPEMA", function=FIP_model)

    model.levers = [RealParameter(f"pi_{u}", 0, upper_bounds[u]) for u in range(len(police_stations))]

    model.constants = model.constants = [
        Constant("route_fugitive_labeled", route_fugitive_labeled),
        Constant("run_length", run_length),
        Constant("tau_uv", tau_uv),
        Constant("labels_full_sorted", labels_full_sorted),
        Constant("labels_sorted", labels_perunit_sorted),
        Constant("labels_sorted_inv", labels_perunit_inv_sorted)
    ]

    model.outcomes = [
        ScalarOutcome("pct_intercepted", kind=ScalarOutcome.MAXIMIZE)
    ]

    highest_perf = 0
    with MultiprocessingEvaluator(model) as evaluator:
        for _ in range(5):
            convergence_metrics = [
                ArchiveLogger(
                    f"./results/optimization/",
                    [l.name for l in model.levers],
                    [o.name for o in model.outcomes if o.kind != o.INFO],
                    base_filename=f"archives_{city}_{mode}_{jitter}.tar.gz"
                ),
            ]

            result = evaluator.optimize(
                algorithm=SingleObjectiveBorgWithArchive,
                nfe=20000,
                searchover="levers",
                convergence=convergence_metrics,
                convergence_freq=100
            )

            result = result.iloc[0]
            if result['pct_intercepted'] > highest_perf:
                results = result

    results_positions = []
    results_positions_labeled = []
    for u, start in enumerate(police_stations):
        results_positions.append(results[f'pi_{u}'])
        results_positions_labeled.append(labels_perunit_inv_sorted[u][int(np.floor(results[f'pi_{u}']))])
    # print(results_positions)

    routes_intercepted = get_intercepted_routes(route_fugitive_labeled,
                                                tau_uv,
                                                labels_full_sorted,
                                                labels_perunit_inv_sorted,
                                                results_positions
                                                )
    # print(routes_intercepted)

    return results, routes_intercepted, results_positions_labeled


if __name__ == '__main__':
    run_length = 1800

    # mode = 'cool'
    # for city in ['Utrecht', 'Winterswijk']:
    # # for city in ['Winterswijk']:
    #     for jitter in [0.02, 0.05]:
    #         filepath = f"graphs/{city}.graph.graphml"
    #         G = ox.load_graphml(filepath=filepath)
    #
    #         with open(f'data/optimization/start_police_{city}.pkl', 'rb') as f:
    #             police_stations = pickle.load(f)
    #
    #         with open(f'data/optimization/delays_police_{city}.pkl', 'rb') as f:
    #             delays = pickle.load(f)
    #
    #         # import results
    #         with open(f'data/results_routes_{mode}_{city}_jitter{jitter}.pkl', 'rb') as f:
    #             results_routes = pickle.load(f)
    #
    #         results, intercepted_routes, results_positions = optimize(city, mode, jitter, results_routes, police_stations, delays, run_length)
    #
    #         with open(f'results/optimization/results_optimization_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(results, f)
    #
    #         with open(f'results/optimization/results_intercepted_routes_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(intercepted_routes, f)
    #
    #         with open(f'results/optimization/results_positions_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(results_positions, f)
    #
    #         print(mode, city, jitter)
    #         # pct_intercepted = results['pct_intercepted']
    #         #
    #         # results_positions = []
    #         # for u, start in enumerate(police_stations):
    #         #     results_positions.append(results[f'pi_{u}'])

    # mode = 'hot'
    # for city in ['Winterswijk', 'Manhattan', 'Utrecht']:
    #     for jitter in [0.05, 0.1]:
    #         filepath = f"graphs/{city}.graph.graphml"
    #         G = ox.load_graphml(filepath=filepath)
    #
    #         with open(f'data/optimization/start_police_{city}.pkl', 'rb') as f:
    #             police_stations = pickle.load(f)
    #
    #         with open(f'data/optimization/delays_police_{city}.pkl', 'rb') as f:
    #             delays = pickle.load(f)
    #
    #         # import results
    #         with open(f'data/results_routes_{mode}_{city}_jitter{jitter}.pkl', 'rb') as f:
    #             results_routes = pickle.load(f)
    #
    #         results, intercepted_routes, results_positions = optimize(city, mode, jitter, results_routes, police_stations, delays, run_length)
    #
    #         with open(f'results/optimization/results_optimization_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(results, f)
    #
    #         with open(f'results/optimization/results_intercepted_routes_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(intercepted_routes, f)
    #
    #         with open(f'results/optimization/results_positions_{mode}_{city}_jitter{jitter}.pkl', 'wb') as f:
    #             pickle.dump(results_positions, f)
    #         print(mode, city, jitter)

    mode = 'hot+cool'
    jitter = ''
    for city in ['Winterswijk', 'Manhattan', 'Utrecht']:
        results_routes = []
        filepath = f"graphs/{city}.graph.graphml"
        G = ox.load_graphml(filepath=filepath)

        with open(f'data/optimization/start_police_{city}.pkl', 'rb') as f:
            police_stations = pickle.load(f)

        with open(f'data/optimization/delays_police_{city}.pkl', 'rb') as f:
            delays = pickle.load(f)

        # import results
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

        results, intercepted_routes, results_positions = optimize(city, mode, jitter, results_routes, police_stations, delays, run_length)

        with open(f'results/optimization/results_optimization_{mode}_{city}.pkl', 'wb') as f:
            pickle.dump(results, f)

        with open(f'results/optimization/results_intercepted_routes_{mode}_{city}.pkl', 'wb') as f:
            pickle.dump(intercepted_routes, f)

        with open(f'results/optimization/results_positions_{mode}_{city}.pkl', 'wb') as f:
            pickle.dump(results_positions, f)

        print(mode, city, jitter)
    #
    #
    #
    #
    #
