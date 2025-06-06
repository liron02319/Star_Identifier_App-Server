import cv2
import numpy as np
import requests
import time
import sys
from os import path

from astropy.io import fits
from astropy.wcs import WCS
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import requests
import json

from StarFinder import __find_blobs, __find_hough, plot_detected_stars

API_KEY = 'xxsgfjptzhctedzp'  # Replace with your real API key!
FITS_OUTPUT = 'tycho.fits'
TXT_OUTPUT = 'stars_output.txt'

def find_stars(img, as_pandas=False, method='hough'):
    """
    :param method: 'blob' or 'hough' (default 'hough')
    """
    if method == 'blob':
        return __find_blobs(img, as_pandas)
    else:
        return __find_hough(img, as_pandas)




def detect_stars(image_path):

    # Load the image in grayscale
    image_path = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    coords, stars_data = find_stars(image_path, as_pandas=False, method='hough')

    print(f"Detected {len(stars_data)} stars.")
    return stars_data


def upload_and_solve(image_path, api_key):
    login_url = 'http://nova.astrometry.net/api/login'
    login_payload = {'request-json': json.dumps({'apikey': API_KEY})}
    login_response = requests.post(login_url, data=login_payload).json()

    if login_response['status'] != 'success':
        print("Login failed:", login_response)
        exit()

    session = login_response['session']
    print("Login success, session:", session)

    # Upload image
    upload_url = 'http://nova.astrometry.net/api/upload'  # HTTPS here too!
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'request-json': f'{{"session":"{session}"}}'}
        upload_resp = requests.post(upload_url, data=data, files=files)

    try:
        upload_response = upload_resp.json()
    except Exception:
        raise Exception(f"Upload failed: Could not parse JSON. Response: {upload_resp.text}")

    if upload_response.get('status') != 'success':
        raise Exception(f"Upload failed: {upload_response}")

    subid = upload_response['subid']
    print(f"Image uploaded. Submission ID: {subid}")

    # Poll submission for job ID
    status_url = f"http://nova.astrometry.net/api/submissions/{subid}"
    job_id = None
    print("Waiting for job ID...")
    for _ in range(60):  # wait max 5 minutes
        time.sleep(5)
        r = requests.get(status_url)
        try:
            status_resp = r.json()
        except Exception:
            print("Could not parse submission status JSON:", r.text)
            continue
        jobs = status_resp.get('jobs')
        if jobs and jobs[0]:
            job_id = jobs[0]
            break
    if not job_id:
        raise Exception("Timed out waiting for job ID.")

    print(f"Job ID: {job_id}")

    # Poll job for solving status
    job_status_url = f"http://nova.astrometry.net/api/jobs/{job_id}"
    print("Waiting for solving to complete...")
    for _ in range(120):  # wait max 10 minutes
        time.sleep(5)
        r = requests.get(job_status_url)
        try:
            job_resp = r.json()
        except Exception:
            print("Could not parse job status JSON:", r.text)
            continue
        status = job_resp.get('status')
        if status == 'success':
            print("Solving completed.")
            break
        elif status == 'failure':
            raise Exception("Solving failed.")
    else:
        raise Exception("Timed out waiting for solving to complete.")

    # Download FITS file
    fits_url = f"http://nova.astrometry.net/wcs_file/{job_id}"
    fits_resp = requests.get(fits_url)
    fits_resp.raise_for_status()
    with open(FITS_OUTPUT, 'wb') as f:
        f.write(fits_resp.content)
    print(f"Saved solved FITS file to {FITS_OUTPUT}")

def show_detected_stars_with_names(image_path, annotated_stars):
    img = cv2.imread(image_path)

    for (x, y, ra, dec, name) in annotated_stars:
        x, y = int(x), int(y)
        cv2.circle(img, (x, y), 10, (0, 255, 0), 2)
        cv2.putText(img, name, (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.imshow('Annotated Stars with Names', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def annotate_stars(fits_path, stars, output_txt):
    print("Converting pixel coordinates to sky coordinates and querying SIMBAD...")

    try:
        hdulist = fits.open(fits_path)
        w = WCS(hdulist[0].header)
        results = []

        custom_simbad = Simbad()
        custom_simbad.add_votable_fields('ids')  # Add 'ids' field

        for x, y, *_ in stars:
            ra, dec = w.wcs_pix2world(x, y, 0)
            coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
            simbad_result = custom_simbad.query_region(coord, radius='0d0m10s')

            if simbad_result:
                main_id = simbad_result[0]['MAIN_ID']
                catalog_ids = simbad_result[0]['IDS']
                name = f"{main_id} ({catalog_ids})"
            else:
                name = "Unknown"

            results.append((x, y, ra, dec, name))

        with open(output_txt, 'w') as f:
            for x, y, ra, dec, name in results:
                f.write(f"{x},{y} -> RA: {ra:.5f}, DEC: {dec:.5f}, Name: {name}\n")

        print(f"Saved annotated stars to {output_txt}")
        return results

    except Exception as e:
        print("Error during annotation:", e)
        return []

def show_detected_stars(image_path, centroids):
    img = cv2.imread(image_path)
    for (x, y) in centroids:
        cv2.circle(img, (x, y), 10, (0, 255, 0), 2)  # green circle radius=10, thickness=2

    cv2.imshow('Detected Stars', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



if __name__ == "__main__":
    #stars = detect_stars(IMAGE_PATH)
    #upload_and_solve(IMAGE_PATH, API_KEY)
  #  annotate_stars(FITS_OUTPUT, stars, TXT_OUTPUT)
    # Check if the image file exists
    image_path = r"C:\Users\User\Desktop\Python\project_new_space-master\photo\tycho.jpg"  # Example: "images/stars_sample.jpg"

    # Check if the image file exists
    if not path.exists(image_path):
        print(f"Image not found: {image_path}")


    # Load the image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Failed to load image: {image_path}")


    # Detect stars using Hough transform (you can also use method='blob')
    coords, stars_data = find_stars(img, as_pandas=False, method='hough')

    # Print the number of stars detected
    print(f"Detected {len(stars_data)} stars.")
    plot_detected_stars(img, stars_data)

    # stars = detect_stars(IMAGE_PATH)
    #print("ESSSSS")

    #show_detected_stars(IMAGE_PATH, stars)  # <-- add this line to visualize stars
    upload_and_solve(image_path, API_KEY)

    annotated = annotate_stars(FITS_OUTPUT, stars_data, TXT_OUTPUT)
    show_detected_stars_with_names(image_path, annotated)