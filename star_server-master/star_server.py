# star_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import imghdr
from star_pipeline import process_star_image

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
UPLOAD_FOLDER_NAME = "uploads"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}  # only accept these types
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size

# -----------------------------------------------------------------------------
# Initialize Flask app
# -----------------------------------------------------------------------------
app = Flask(__name__)

# Enable CORS so an Android client (emulator/device) can POST without CORS errors.
CORS(app)

# Compute an absolute path for uploads folder (next to this script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, UPLOAD_FOLDER_NAME)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Enforce a maximum upload size
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def allowed_file_type(stream) -> bool:
    """
    Check the actual file type (using Python's imghdr) instead of trusting the extension.
    """
    stream.seek(0)  # ensure we're at the start
    header = stream.read(512)
    stream.seek(0)
    fmt = imghdr.what(None, h=header)
    return fmt in ALLOWED_IMAGE_EXTENSIONS

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/upload", methods=["POST"])
def upload_star_image():
    """
    Expects a multipart/form-data POST with form‐field name "image".
    Returns JSON: { "stars": [ { "name":"...", "x":.., "y":.. }, ... ] }
    """
    # 1) Validate that the request contains 'image' in files
    if "image" not in request.files:
        return jsonify({"error": "No 'image' field in request"}), 400

    image_file = request.files["image"]

    # 2) Ensure a file was actually selected
    if image_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # 3) Check file type (by reading header, not trusting extension)
    if not allowed_file_type(image_file.stream):
        return jsonify({"error": "Unsupported image type"}), 400

    # 4) Save the file with a unique name
    try:
        # Generate a random UUID name with the same extension
        ext = imghdr.what(None, h=image_file.stream.read(512))
        image_file.stream.seek(0)
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(filepath)
    except Exception as e:
        app.logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
        return jsonify({"error": "Failed to save image"}), 500

    # 5) Process the image through your pipeline
    try:
        # process_star_image should return a list of dicts: [{ "name":..., "x":.., "y":.. }, ...]
        results = process_star_image(filepath)
        return jsonify({"stars": results}), 200
    except Exception as e:
        # Log the full stack trace on the server side
        app.logger.error(f"Error in process_star_image: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# Optional health check route
# -----------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

# -----------------------------------------------------------------------------
# Run the App
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # For development only; do not use debug=True in production.
    app.run(host="0.0.0.0", port=5000, debug=True)
