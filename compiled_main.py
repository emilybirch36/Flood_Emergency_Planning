import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString, Polygon
import rasterio
from rasterio import mask
import json
from rtree import index
import networkx as nx
from plotter import Plotter


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


# Defining the radius for searching for the highest point
def defining_radius_and_speed():
    while True:
        try:
            fit = int(input('Please enter your fitness level in a scale from 1 to 10 '
                            '(will affect the maximum walking distance):\n'))
            if fit >= 6:
                radius = 5000
                walking_speed = 5000 / 60
            elif fit >= 5:
                radius = 4000
                walking_speed = 4000 / 60
            else:
                radius = 3000
                walking_speed = 3500 / 60

            print('Estimated walking speed:', round(walking_speed, 2), 'm/min\nSearch radius:', radius, 'm')
            return radius, walking_speed

        except ValueError:
            print('Invalid input. Input is not a number.')


# Task 1 and task 6
# Prompting for user location while handling possible invalid input
def user_input():
    while True:
        user_loc = input('Please enter your location as BNG coordinates (easting and northing separated by a comma):\n')
        user_loc = user_loc.split(',')
        try:
            if len(user_loc) != 2:
                print('Invalid input. Please only enter one easting coordinate and one northing coordinate.')
            else:
                user_loc = Point(float(user_loc[0]), float(user_loc[1]))
                # Checking coordinates
                print('Your coordinates are:', user_loc.x, user_loc.y)
                conf = input("Type 'y' to confirm:\n")
                if conf.lower() == 'y':
                    print('Coordinates confirmed.')
                    break
        except ValueError:
            print('Invalid input. Input is not a coordinate.')

    # Defining the bounding box vertices against which checking the user location
    data = {'point': ['bottom_left', 'bottom_right', 'top_right', 'top_left'],
            'easting_coordinate': [430000, 465000, 465000, 430000],
            'northing_coordinate': [80000, 80000, 95000, 95000]}

    # Creating a dataframe and its polygon
    df = pd.DataFrame(data)
    box_poly = Polygon(df[['easting_coordinate', 'northing_coordinate']].values)

    # Checking the user location
    # First attempt (for task 1): checking the bounding box
    if box_poly.contains(user_loc) or box_poly.touches(user_loc):
        print('You are in the bounding box.')
    else:
        # Second attempt (for task 6): checking with the shapefile
        shape = gpd.read_file('shape/isle_of_wight.shp')
        if shape.contains(user_loc).iloc[0] or shape.touches(user_loc).iloc[0]:
            print('You are not in the bounding box but on the island.')
        else:
            print('Invalid location: outside boundaries, quitting.')
            quit()

    return user_loc


# Task 2
# Searching for the highest point withing the defined radius from the user location
def highest_point(location, radius):
    print('Highest point search in progress..\n')
    buffer = location.buffer(radius)
    # Reading elevation data file to get the raster which defines the bounding box
    raster = rasterio.open('elevation/SZ.asc')
    elevation_data = raster.read(1)
    # Searching for the raster bounds and creating its polygon
    elevation_bounds = raster.bounds
    elevation_poly = Polygon([(elevation_bounds[0], elevation_bounds[1]),
                              (elevation_bounds[2], elevation_bounds[1]),
                              (elevation_bounds[2], elevation_bounds[3]),
                              (elevation_bounds[0], elevation_bounds[3])])
    # Identifying user's location altitude
    user_row, user_col = raster.index(location.x, location.y)
    user_altitude = elevation_data[user_row, user_col]
    # Finding the intersection between the user location buffer and the elevation polygon
    mask_polygon = buffer.intersection(elevation_poly)
    # Identifying local area's highest altitude
    local_altitude_array, out_transform = rasterio.mask.mask(dataset=raster, shapes=[mask_polygon],
                                                             crop=True, filled=False)
    max_altitude = np.max(local_altitude_array)
    # Determining the pixel of the highest point
    loc = np.where(local_altitude_array == max_altitude)
    row_highest_point = loc[1][0]
    col_highest_point = loc[2][0]
    # Convert the row and the column into BNG coordinates
    x, y = rasterio.transform.xy(out_transform, row_highest_point, col_highest_point)
    # Creating a Point class instance for the destination
    dest = Point(x, y)
    print('Current altitude:', int(user_altitude), 'm')
    print('Maximum altitude in the searched area:', int(max_altitude), 'm')
    # Increasing the search radius if some conditions are met
    if max_altitude < 70:
        print('The maximum altitude in the searched area is below the recommended threshold (70 m).')
        if radius < 5000:
            radius += 1000
            print('Increasing the search radius by 1000 m. Search radius:', radius, 'm.')
            dest, raster, local_altitude_array, out_transform, radius, (user_altitude, max_altitude) = highest_point(
                location, radius)
            return dest, raster, local_altitude_array, out_transform, radius, (user_altitude, max_altitude)
        else:
            inc = input("5000 m search radius reached. Would you like to increase it anyway?"
                        " Type 'y' to proceed or any other input to resume the current search:\n")
            if inc.lower() == 'y':
                radius += 500
                print('Increasing the search radius by 500 m. Search radius:', radius, 'm.')
                dest, raster, local_altitude_array, out_transform, radius, (user_altitude, max_altitude) = \
                    highest_point(location, radius)
                return dest, raster, local_altitude_array, out_transform, radius, (user_altitude, max_altitude)
            else:
                print('Current search resumed.')

    return dest, raster, local_altitude_array, out_transform, radius, (user_altitude, max_altitude)


# Task 3
# Identifying the nearest ITN node to the user and the nearest to the destination
def itn_nodes_parser(user, dest):
    # Opening the ITN data as a dictionary
    with open('itn/solent_itn.json') as file:
        itn_dict = json.load(file)
    # Creating an index and adding each node's data to the index
    idx = index.Index()
    for i, node in enumerate(itn_dict['roadnodes'].items()):
        idx.insert(i, (node[1]['coords'][0], node[1]['coords'][1]), obj=node[0])
    # # Assigning the two variables to empty strings to deal with a PEP8 notification
    nearest_to_user = ''
    nearest_to_dest = ''
    # Identifying the nearest node to the user and destination
    for i in idx.nearest((user.x, user.y), 1, objects='raw'):
        nearest_to_user = i, itn_dict['roadnodes'][i]['coords']
    for i in idx.nearest((dest.x, dest.y), 1, objects='raw'):
        nearest_to_dest = i, itn_dict['roadnodes'][i]['coords']
    # Avoiding empty paths from trying to be plotted
    if nearest_to_user == nearest_to_dest:
        print('No paths available for the searched area, quitting.')
        quit()

    # Creating the connections between the user and destination's locations
    # and their respective nearest nodes (to be plotted)
    user_to_node = LineString([(user.x, user.y), (nearest_to_user[1][0], nearest_to_user[1][1])])
    node_to_dest = LineString([(nearest_to_dest[1][0], nearest_to_dest[1][1]), (dest.x, dest.y)])

    return itn_dict, nearest_to_user, nearest_to_dest, user_to_node, node_to_dest


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


# Task 5
# Plotting the map and the identified paths (in plotter.py)


def main():
    # Calling task 1 and task 6
    user_location = user_input()

    radius, walking_speed = defining_radius_and_speed()

    # Calling task 2
    destination, raster, local_array, out_trans, radius, altitudes = highest_point(user_location, radius)

    # Calling task 3
    itn_data, nearest_to_user, nearest_to_destination, user_to_node, node_to_dest = \
        itn_nodes_parser(user_location, destination)

    # Calling task 4
    short_path_gpd, short_path_data, fast_path_gpd, fast_path_data = \
        paths(itn_data, raster, walking_speed, nearest_to_user, nearest_to_destination)

    print('Path found! Your safe place is at:', destination.x, destination.y)
    print('Loading map..')

    # Calling task 5
    plotter = Plotter(user_location, destination, altitudes, local_array, out_trans, radius,
                      fast_path_gpd, fast_path_data, short_path_gpd, short_path_data, user_to_node, node_to_dest)
    plotter.background_map()


if __name__ == "__main__":
    main()
