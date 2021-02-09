from plotter import Plotter
from task_1 import user_input
from task_2_highest_point import highest_point
from task_3 import itn_nodes_parser
from task_4 import paths
from creativity_marks import defining_radius_and_speed


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

