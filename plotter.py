import rasterio
import numpy as np
import matplotlib.pyplot as plt
import rasterio.plot
from matplotlib import cm
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar


class Plotter:
    def __init__(self, user_loc, dest, altitudes, alt_array, trans_output, radius,
                 fast_path_gpd, fast_path_data, short_path_gpd, short_path_data, user_to_node, node_to_dest):
        self.user_location = user_loc
        self.destination = dest
        self.user_alt = altitudes[0]
        self.dest_alt = altitudes[1]
        self.altitude_array = alt_array
        self.transform_output = trans_output
        self.radius = radius
        self.fast_path_gpd = fast_path_gpd
        self.fast_path_data = fast_path_data
        self.short_path_gpd = short_path_gpd
        self.short_path_data = short_path_data
        self.user_to_node = user_to_node
        self.node_to_dest = node_to_dest

    def background_map(self):

        # Read the raster
        background = rasterio.open('background/raster-50k_2724246.tif')
        back_array = background.read(1)

        # Set colours
        palette = np.array([value for key, value in background.colormap(1).items()])
        background_image = palette[back_array]

        # Plot the map with correct width and height
        bounds = background.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

        # Set a plot
        fig, ax = plt.subplots()
        ax.imshow(background_image, extent=extent, zorder=0)

        # Zoom in on the map
        plt.xlim(self.user_location.x - self.radius, self.user_location.x + self.radius)
        plt.ylim(self.user_location.y - self.radius, self.user_location.y + self.radius)

        # Set the title
        ax.set_title(label='Isle of Wight:\nFlood Emergency Planning', fontdict={'fontsize': 20})

        # Show the elevation
        rasterio.plot.show(source=self.altitude_array, ax=ax, zorder=1,
                           transform=self.transform_output, alpha=0.4, cmap=plt.get_cmap('terrain'))

        # Draw elevation colour bar using task 2 buffer
        norm = cm.colors.Normalize(vmax=np.max(self.altitude_array), vmin=np.min(self.altitude_array))
        cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=plt.get_cmap('terrain')), ax=ax)
        cb.ax.set_ylabel(ylabel='Elevation(m)', size=10)

        # Assign the size of the colour bar
        cb.ax.tick_params(labelsize=10)

        # Plot the different paths
        if self.short_path_data[0] == self.fast_path_data[0] and self.short_path_data[1] == self.fast_path_data[1]:
            self.fast_path_gpd.plot(ax=ax, edgecolor='r', linewidth=2, zorder=2,
                                    label='Fastest path (Distance: ' + str(round(self.fast_path_data[0])) +
                                          ' m / Travel time: ' + str(round(self.fast_path_data[1])) + ' min)')

        else:
            self.fast_path_gpd.plot(ax=ax, edgecolor='r', linewidth=2, zorder=2,
                                    label='Fastest path (Distance: ' + str(round(self.fast_path_data[0])) +
                                          ' m / Travel time: ' + str(round(self.fast_path_data[1])) + ' min)')

            self.short_path_gpd.plot(ax=ax, edgecolor='b', linewidth=2, zorder=2,
                                     label='Shortest path (Distance: ' + str(round(self.short_path_data[0])) +
                                           ' m / Travel time: ' + str(round(self.short_path_data[1])) + ' min)')

        # Draw scale bar
        scale_bar = AnchoredSizeBar(ax.transData, size=1000,
                                    label='1 km', loc=4, frameon=False, pad=0.6,
                                    size_vertical=0.7, color='black')
        ax.add_artist(scale_bar)

        # Add North arrow to the plot
        x, y, arrow_length = 0.05, 0.95, 0.15
        ax.annotate('N', xy=(x, y), xytext=(x, y - arrow_length),
                    arrowprops=dict(facecolor='black', width=1, headwidth=7),
                    ha='center', va='center', fontsize=10,
                    xycoords=ax.transAxes)

        # Call the plots
        self.add_user_location()
        self.add_destination()
        self.connections()

        self.show()

    # Adds initial position of the user
    def add_user_location(self):
        plt.plot(self.user_location.x, self.user_location.y,
                 marker='*', color='w', markersize=10, markerfacecolor='gold', markeredgecolor='k',
                 label='You are here (Elev: ' + str(int(self.user_alt)) + ' m)')

    # Adds destination point
    def add_destination(self):
        plt.plot(self.destination.x, self.destination.y,
                 marker='^', color='w', markersize=10, markerfacecolor='forestgreen', markeredgecolor='k',
                 label='Safe place (Elev: ' + str(int(self.dest_alt)) + ' m)')

    def connections(self):
        plt.plot(self.user_to_node.xy[0], self.user_to_node.xy[1], 'k--',
                 self.node_to_dest.xy[0], self.node_to_dest.xy[1], 'k--', label='Off road / By sea')

    def show(self):
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(),
                   loc='upper center', bbox_to_anchor=(0.5, -0.05), fontsize='medium',
                   fancybox=True, shadow=True, ncol=5)

        plt.show()



