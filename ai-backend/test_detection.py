import cv2
from detect_and_upload import handle_disease_classification

# Load test image
frame = cv2.imread("test.jpg")

if frame is None:
    print("Error: test.jpg was not found or could not be opened.")
    exit()

# Optional bbox for crop test
bbox = (20, 20, 200, 200)

handle_disease_classification(
    frame=frame,
    disease_name="Tomato Early Blight",
    confidence=0.92,
    gps_lat=32.0123,
    gps_lng=36.1234,
    bbox=bbox
)