import numpy as np
from sklearn.cluster import SpectralClustering
import cv2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import colorsys
from sklearn.neighbors import KNeighborsClassifier

from sklearn.metrics import pairwise_distances_argmin


def grid(image, grid_size=(10, 10)):
    h, w, _ = image.shape
    cell_h = h // grid_size[0]
    cell_w = w // grid_size[1]

    mosaic = np.zeros_like(image)

    for row in range(grid_size[0]):
        for col in range(grid_size[1]):
            y1, y2 = row * cell_h, (row + 1) * cell_h
            x1, x2 = col * cell_w, (col + 1) * cell_w

            cell = image[y1:y2, x1:x2]
            mean_color = cell.mean(axis=(0, 1)).astype(int)

            # Fill the mosaic cell with the mean color
            mosaic[y1:y2, x1:x2] = mean_color

    cv2.imwrite('new_mosaic.jpg', mosaic)
    return mosaic

class ClusterFuck:
    def __init__(self, image):
        self.image = image
        self.hsv_image = None
        self.hsv_values = []

        self.labels = None

    def to_hsv(self):
        self.hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.hsv_values = self.hsv_image.reshape(-1, 3)  # flatten to Nx3

    def fit(self):
        n_clusters = 5
        spectral = SpectralClustering(
            n_clusters=n_clusters,
            affinity='nearest_neighbors',  # or 'rbf'
            n_neighbors=10,  # used only for 'nearest_neighbors'
            assign_labels='kmeans',  # how labels are assigned
            random_state=42
        )
        spectral.fit(self.hsv_values)
        self.labels = spectral.labels_

    def display(self):
        h, s, v = self.hsv_values[:, 0], self.hsv_values[:, 1], self.hsv_values[:, 2]

        fig = plt.figure(figsize=(15, 5))

        rgb_values = [colorsys.hsv_to_rgb(h/179, s/255, v/255) for h, s, v in self.hsv_values]

        ax1 = fig.add_subplot(1, 3, 1, projection='3d')
        ax1.scatter(h, s, v,c=rgb_values)
        ax1.set_xlabel('Hue')
        ax1.set_ylabel('Saturation')
        ax1.set_zlabel('Value/Brightness')
        ax1.set_title("3D HSV Space")

        rgb_values = [colorsys.hsv_to_rgb(h / 179, s / 255, 1) for h, s, _ in self.hsv_values]

        ax2 = fig.add_subplot(1, 3, 2)
        ax2.scatter(h, s, color=rgb_values)
        ax2.set_xlabel('Hue')
        ax2.set_ylabel('Saturation')
        ax2.set_title("2D Hue and Saturation Space")

        rgb_values = [colorsys.hsv_to_rgb(h / 179, 1, v / 255) for h, _, v in self.hsv_values]

        ax3 = fig.add_subplot(1, 3, 3)
        ax3.scatter(h, s, color=rgb_values)
        ax3.set_xlabel('Hue')
        ax3.set_ylabel('Value/Brightness')
        ax3.set_title("2D Hue and Value/Brightness Space")

        plt.tight_layout()
        plt.show()


# --- Run ---
image = cv2.imread("cat.jpeg")

mosaic = grid(image, (100, 100))

cf = ClusterFuck(mosaic)
cf.to_hsv()
cf.fit()
cf.display()

hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

centroids = np.array([
    cf.hsv_values[cf.labels == k].mean(axis=0)
    for k in np.unique(cf.labels)
])

all_pixels = hsv_image.reshape(-1, 3)

labels = pairwise_distances_argmin(all_pixels, centroids)

id_colors = np.array([
    (255, 0, 0),
    (255, 0, 255),
    (0, 0, 255),
    (0, 255, 255),
    (0, 255, 0)
])

# Create segmented image
new_image = id_colors[labels].reshape(hsv_image.shape).astype(np.uint8)

new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)

cv2.imwrite("ne_image.jpeg", new_image)

cv2.imshow("image", new_image)
cv2.waitKey(0)
cv2.destroyAllWindows()