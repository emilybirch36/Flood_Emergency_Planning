# Task 3
import json
from rtree import index


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
