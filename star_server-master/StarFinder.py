import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
#from ImageLoader import load_image
from os import path


def __threshold_image(img, thresh=170, max_value=255):
    """
    Apply threshold for better blob detection (darkens the background and keeps the stars).
    """
    _, img_bin = cv2.threshold(img, thresh, max_value, cv2.THRESH_BINARY)
    return img_bin


# https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html#ga47849c3be0d0406ad3ca45db65a25d2d
# https://docs.opencv.org/4.x/da/d53/tutorial_py_houghcircles.html
def __get_hough_circles(img):
    img_bin = __threshold_image(img)
    img_blur = cv2.GaussianBlur(img_bin, (7, 7), 0)
    circles = cv2.HoughCircles(img_blur, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=300, param2=0.95, minRadius=1, maxRadius=6)
    return circles


def __find_hough(img, as_pandas=False):
    coords, stars_data = [], []
    circles = __get_hough_circles(img)
    if circles is not None:
        for x, y, r in circles[0]:
            x, y, r = round(x, 5), round(y, 5), round(r, 2)
            b = img[int(y), int(x)] / np.max(img)
            stars_data.append((x, y, r, b))
            coords.append([x, y])
    return __handle_data_return(coords, stars_data, as_pandas)


def __get_blobs(img):
    params = cv2.SimpleBlobDetector_Params()

    # Change thresholds
    params.minThreshold = 10;
    params.maxThreshold = 200;

    params.filterByArea = True
    params.minArea = 0.01
    params.maxArea = 300

    params.filterByCircularity = True
    params.minCircularity = 0.1

    # Filter by Convexity
    params.filterByConvexity = True
    params.minConvexity = 0.87

    params.blobColor = 255
    params.minRepeatability = 2

    # Filter by Inertia
    params.filterByInertia = True
    params.minInertiaRatio = 0.01

    detector = cv2.SimpleBlobDetector_create(params)

    img_bin = __threshold_image(img)
    kp = detector.detect(img_bin)
    return kp


def __find_blobs(img, as_pandas=False):
    keypoints = __get_blobs(img)
    coords, stars_data = [], []
    for kp in keypoints:
        x, y = kp.pt
        x, y = round(x, 5), round(y, 5)
        b = img[int(y), int(x)] / np.max(img)
        stars_data.append([x, y, round(kp.size, 2), b])
        coords.append([round(x, 5), round(y, 5)])
    return __handle_data_return(coords, stars_data, as_pandas)


def __handle_data_return(coords, stars_data, as_pandas):
    # empty coords_arr raises an error in pd.DataFrame
    stars_data_arr = np.array(stars_data) if len(stars_data) > 0 else stars_data
    coords_arr = np.array(coords) if len(coords) > 0 else coords
    if as_pandas:
        return coords_arr, pd.DataFrame(stars_data_arr, columns=['x', 'y', 'r', 'b'])
    return coords_arr, stars_data_arr


def find_stars(img, as_pandas=False, method='hough'):
    """
    :param method: 'blob' or 'hough' (default 'hough')
    """
    if method == 'blob':
        return __find_blobs(img, as_pandas)
    else:
        return __find_hough(img, as_pandas)


def save_as_text_file(stars_data: [np.ndarray, pd.DataFrame], filename: str, verbose: bool = False):
    """
    :param stars_data: Data returned from get_blobs_data.
    :param filename: Path to save file.
    :param verbose: True will notify if the file was successfully saved (default = False).
    """
    try:
        with open(filename, 'w') as _:
            np.savetxt(filename, stars_data, delimiter='\t', fmt='%f')
            if verbose:
                print(f"Saved file! location: {filename}")
    except Exception as e:
        print(e)


def plot_detected_stars(img, stars_data):
    fig, ax = plt.subplots(ncols=2, figsize=(10, 10))
    ax[0].imshow(img, cmap='gray')
    ax[1].imshow(__threshold_image(img), cmap='gray')
    for (x, y, r, b) in stars_data:
        ax[1].add_patch(plt.Circle((x, y), radius=r, edgecolor='g', facecolor='none'))
    ax[0].axis('off')
    ax[1].axis('off')
    plt.tight_layout()
    plt.show()



def main():
    # Replace with the path to your image file
    image_path =  r"C:\Users\User\Desktop\Python\project_new_space-master\photo\tycho.jpg"   # Example: "images/stars_sample.jpg"

    # Check if the image file exists
    if not path.exists(image_path):
        print(f"Image not found: {image_path}")
        return

    # Load the image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Failed to load image: {image_path}")
        return

    # Detect stars using Hough transform (you can also use method='blob')
    coords, stars_data = find_stars(img, as_pandas=False, method='hough')

    # Print the number of stars detected
    print(f"Detected {len(stars_data)} stars.")

    # Plot the original image and the thresholded image with star overlays
    plot_detected_stars(img, stars_data)

    # Optionally save the star data to a text file
    output_file = "stars_output.txt"
    save_as_text_file(stars_data, output_file, verbose=True)





if __name__ == "__main__":
    main()

