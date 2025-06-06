# project_new_space 
## The Server of StarTracker app
project_new_space is a server application built with FastAPI.<br /> It takes an image path of stars, performs the algorithm on the image, and returns a list of star IDs, names, and coordinates.

<img width="200" src="photo/צילום מסך 2023-06-05 133258.png">

## Algorithm:
There are two parts to the algorithm:
### Identifying world coordinates system (WCS) and converting pixel coordinates to world coordinates (RA, DEC).
The algorithm used to identify the stars is based on the Plate Solution algorithm, implemented by the Astrometry.net project (https://astrometry.net/).
The algorithm receives an image and coordinates of the stars in the image in pixel units and returns the coordinates of the stars in the image in degrees.
The algorithm is based on the following steps:
1. The algorithm receives an image the coordinates of the stars in the image achieved by DAOStarFinder from  photoutils python library.
2. The algorithm finds the WCS of the image using blind astrometric solving without initial guess based on image metadata (e.g., time, location, orientation, etc.).
3. Iteratively, the algorithm finds the transformation matrix between the stars in the image and the stars in the catalog.
4. Update the WCS guess and repeat step 3 until the error is less than some fixed threshold.

### Matching the stars in the image to the stars in the catalog.
1. Convert the pixel coordinates of the stars in the image to world coordinates (RA, DEC).
2. Extract the stars from the catalog that are within a distance of 2.0 arcmin from the points found in the previous step. This is implemented using the "find_region" function from the Simbad Python library.
3. Find the stars in the catalog that are closest to the stars in the image by utilizing the k-d tree algorithm for efficient search. This step is implemented by the function "match_coordinates_sky" from the astropy Python library.

### Libraries:

[<img src="photo/Astrometry.png" height="50px">](https://nova.astrometry.net/) &nbsp;&nbsp;&nbsp;
[<img src="photo/Logo_of_the_Astropy_Project.png" height="50px">](https://www.astropy.org/) &nbsp;&nbsp;&nbsp;
[<img src="photo/simbad_small.png" height="50px">](http://simbad.u-strasbg.fr/simbad/)

---

**Astrometry.net**: Astrometry.net is a powerful astrometric engine that can identify celestial objects in astronomical images.

**Astropy Project**: Astropy is a community-driven library for astronomy in Python, providing various utilities and tools for working with astronomical data.

**Simbad**: SIMBAD is an astronomical database that provides information on astronomical objects, including their coordinates, magnitudes, and spectra.

## Installation
1. clone this repository
2. Install the dependencies: pip install -r requirements.txt
3.  run the following command in the terminal to start the server:<br />
```uvicorn server:app --host <server network address> --port 8080 --reload``` <br />
**Note.** Verify that the phone and the server are connected to the same network (Wi-Fi, Ethernet, eg.)
