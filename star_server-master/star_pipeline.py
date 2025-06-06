import cv2
from os import path
from StarFinder import plot_detected_stars
from main100 import find_stars, upload_and_solve, annotate_stars, FITS_OUTPUT, TXT_OUTPUT

def process_star_image(image_path):
    if not path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Failed to load image.")

    coords, stars_data = find_stars(img, as_pandas=False, method='hough')
    print(f"Detected {len(stars_data)} stars.")

    upload_and_solve(image_path, api_key="xxsgfjptzhctedzp")  # Use environment variable or config file in real setup

    annotated = annotate_stars(FITS_OUTPUT, stars_data, TXT_OUTPUT)

    return [{'x': int(x), 'y': int(y),"ra" : float(ra),"dec" : float(dec), 'name': name.split("(")[0]} for x, y, ra, dec, name in annotated]