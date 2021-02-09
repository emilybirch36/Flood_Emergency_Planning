# Task 1 and task 6
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon


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
