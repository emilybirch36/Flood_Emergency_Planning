# Task 2
import numpy as np
from shapely.geometry import Point, Polygon
import rasterio
from rasterio import mask

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
            radius += 500
            print('Increasing the search radius by 500 m. Search radius:', radius, 'm.')
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
