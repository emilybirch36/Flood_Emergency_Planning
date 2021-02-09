# Task 4
import geopandas as gpd
from shapely.geometry import LineString
import networkx as nx


class Roadlink:
    def __init__(self, fid, node_a, node_b, length, alt_diff):
        self.fid = fid
        self.node_a = node_a
        self.node_b = node_b
        self.length = length
        self.alt_diff = alt_diff

    # Calculating the time required to travel the roadlink.
    # The function identifies three different values (to be used in the network).
    # For climbing roadlinks, different 'time penalties' are used depending on the fitness level typed by the user.
    # For descending roadlinks, Langmuir's integration to Naismith's rule was used

    def time_weight(self, length, speed, alt_diff):
        base = length / speed
        slope = alt_diff / length * 100

        # Climbing time weight
        if speed == 5000 / 60:
            with_slope_asc = base + abs(alt_diff / 10)
        elif speed == 4000 / 60:
            with_slope_asc = base + 1.25 * abs(alt_diff / 10)
        else:
            with_slope_asc = base + 1.5 * abs(alt_diff / 10)

        # Descending time weight
        if 5 < abs(slope) < 12:
            with_slope_des = base - abs(alt_diff / 30)
            if with_slope_des < 0:
                with_slope_des = 0.001
        elif abs(slope) > 12:
            with_slope_des = base + abs(alt_diff / 30)
        else:
            with_slope_des = base

        return base, with_slope_asc, with_slope_des

    # Alternative 1 (Naismith's rule without Langmuir's integration)

    # def time_weight(self, length, speed, alt_diff):
    #     base = length / speed
    #
    #     # Climbing time weight
    #     if speed == 5000 / 60:
    #         with_slope_asc = base + abs(alt_diff / 10)
    #     elif speed == 4000 / 60:
    #         with_slope_asc = base + 1.25 * abs(alt_diff / 10)
    #     else:
    #         with_slope_asc = base + 1.5 * abs(alt_diff / 10)
    #
    #     with_slope_des = base
    #
    #     return base, with_slope_asc, with_slope_des

    # Alternative code 2 (producing the same paths of the image
    # in the assignment instructions for the test point)

    # def time_weight(self, length, speed, alt_diff):
    #     base = length / speed
    #     if speed == 5000 / 60:
    #         with_slope_asc = abs(base + alt_diff / 10)
    #     elif speed == 4000 / 60:
    #         with_slope_asc = abs(base + 1.25 * (alt_diff / 10))
    #     else:
    #         with_slope_asc = abs(base + 1.5 * (alt_diff / 10))
    #
    #     with_slope_des = base
    #
    #     return base, with_slope_asc, with_slope_des


# Task 4
# Identifying the shortest and fastest routes between the two identified nodes
# Task 4
# Identifying the shortest and fastest routes between the two identified nodes
def paths(itn, raster, speed, nearest_to_user, nearest_to_dest):

    print('Fastest path search in progress..\n')

    def link_alt_diff():
        # Retrieving point 1 altitude
        p1_xy = itn['roadnodes'][attr['start']]['coords'][0], itn['roadnodes'][attr['start']]['coords'][1]
        p1_row, p1_col = raster.index(p1_xy[0], p1_xy[1])
        p1_alt = elevation_data[p1_row, p1_col]
        # Retrieving point 2 altitude
        p2_xy = itn['roadnodes'][attr['end']]['coords'][0], itn['roadnodes'][attr['end']]['coords'][1]
        p2_row, p2_col = raster.index(p2_xy[0], p2_xy[1])
        p2_alt = elevation_data[p2_row, p2_col]
        # Calculating the difference in altitude
        diff = p2_alt - p1_alt

        return diff

    elevation_data = raster.read(1)

    # Retrieving data for each node and adding it to a Roadlink object list
    roadlink_list = []
    for osgb, attr in itn['roadlinks'].items():
        alt_diff = link_alt_diff()
        # Adding data
        roadlink_list.append(Roadlink(osgb, attr['start'], attr['end'], attr['length'], alt_diff))

    # Initializing a directed graph
    graph = nx.DiGraph()
    # Adding to the graph two edges for each roadlink for allowing different weights:
    # if walking uphill from A to B the time counting the slope is added, otherwise the base time is used
    for link in roadlink_list:
        base, with_slope_asc, with_slope_des = link.time_weight(link.length, speed, link.alt_diff)
        if link.alt_diff > 0:
            graph.add_edge(link.node_a, link.node_b, fid=link.fid, length=link.length, time=with_slope_asc)
            graph.add_edge(link.node_b, link.node_a, fid=link.fid, length=link.length, time=with_slope_des)
        elif link.alt_diff == 0:
            graph.add_edge(link.node_a, link.node_b, fid=link.fid, length=link.length, time=base)
            graph.add_edge(link.node_b, link.node_a, fid=link.fid, length=link.length, time=base)
        else:
            graph.add_edge(link.node_a, link.node_b, fid=link.fid, length=link.length, time=with_slope_des)
            graph.add_edge(link.node_b, link.node_a, fid=link.fid, length=link.length, time=with_slope_asc)

    # Identifying the shortest route
    short_path = nx.dijkstra_path(graph, source=nearest_to_user[0], target=nearest_to_dest[0], weight='length')
    # Identifying shortest route's length
    short_path_distance = nx.dijkstra_path_length(graph, source=nearest_to_user[0],
                                                  target=nearest_to_dest[0], weight='length')

    roads = itn['roadlinks']
    # Creating its geoDataFrame to be plotted
    links = []
    geom = []
    short_path_time = 0

    first_node = short_path[0]
    for node in short_path[1:]:
        link_fid = graph.edges[first_node, node]['fid']
        links.append(link_fid)
        link_time = graph.edges[first_node, node]['time']
        short_path_time += link_time
        geom.append(LineString(roads[link_fid]['coords']))
        first_node = node

    short_path_gpd = gpd.GeoDataFrame({'fid': links, 'geometry': geom})

    # Identifying the fastest route
    fast_path = nx.dijkstra_path(graph, source=nearest_to_user[0], target=nearest_to_dest[0], weight='time')
    # Identifying fastest route's travel time
    fast_path_time = nx.dijkstra_path_length(graph, source=nearest_to_user[0], target=nearest_to_dest[0], weight='time')

    # Creating its geoDataFrame to be plotted
    links = []
    geom = []
    fast_path_distance = 0

    first_node = fast_path[0]
    for node in fast_path[1:]:
        link_fid = graph.edges[first_node, node]['fid']
        links.append(link_fid)
        link_dist = graph.edges[first_node, node]['length']
        fast_path_distance += link_dist
        geom.append(LineString(roads[link_fid]['coords']))
        first_node = node

    fast_path_gpd = gpd.GeoDataFrame({'fid': links, 'geometry': geom})

    return short_path_gpd, (short_path_distance, short_path_time), fast_path_gpd, (fast_path_distance, fast_path_time)
