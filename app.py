import streamlit as st
import cv2
import tempfile
from PIL import Image
from math import sqrt, pow
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

# Initialize session state for image capture
if "image_captured" not in st.session_state:
    st.session_state.image_captured = False
if "image_path" not in st.session_state:
    st.session_state.image_path = None

def capture_image():
    """Launch the camera to capture an image."""
    st.write("Launching camera...")
    cap = cv2.VideoCapture(0)
    temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name

    if not cap.isOpened():
        st.error("Unable to access the camera.")
        return None

    while not st.session_state.image_captured:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to grab frame.")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, caption="Live Feed", channels="RGB")

        # Display capture button
        if st.button("Capture Full Tree Image"):
            cv2.imwrite(temp_image_path, frame)
            st.session_state.image_captured = True
            st.session_state.image_path = temp_image_path
            st.success("Image captured successfully!")
            break

    cap.release()

def validate_image(image_path):
    """Validate the captured image for required conditions."""
    with Image.open(image_path) as img:
        width, height = img.size
        st.write(f"Image dimensions: {width}x{height}")
        if height < 500:  # Example condition
            st.warning("The image is too small. Please capture again.")
            return False
    return True

def calculate_tree_height(distance, angle):
    """Calculate tree height using distance and angle."""
    height = distance * sqrt(1 + pow(angle, 2))
    st.write(f"Calculated tree height: {height:.2f} units")
    return height

def identify_tree(image_path):
    """Identify the tree using an external API."""
    api_key = os.getenv("PLANT_ID_API_KEY")
    api_url = "https://api.plant.id/v2/identify"

    with open(image_path, 'rb') as image_file:
        files = {'images': image_file}
        data = {'organs': ['bark']}

        response = requests.post(
            api_url, 
            headers={'Authorization': f'Bearer {api_key}'}, 
            files=files,
            data=data
        )

    if response.status_code == 200:
        result = response.json()
        suggestions = result.get('suggestions', [])
        if suggestions:
            return suggestions[0]['plant_name'], suggestions[0]['plant_details']['wiki_url']
        else:
            st.error("No matching tree found.")
    else:
        st.error(f"API Error: {response.status_code}")

    return None, None

def fetch_wikipedia_details(wiki_url):
    """Fetch details from the provided Wikipedia URL."""
    if wiki_url:
        response = requests.get(wiki_url)
        if response.status_code == 200:
            st.success("Wikipedia page fetched successfully.")
            return response.text[:500]  # Display first 500 characters
        else:
            st.error("Failed to fetch Wikipedia details.")
    return ""

def main():
    st.title("Tree Image Analysis Tool")

    if not st.session_state.image_captured:
        st.header("Step 1: Capture Full Tree Image")
        capture_image()

    if st.session_state.image_captured:
        tree_image_path = st.session_state.image_path

        if validate_image(tree_image_path):
            st.header("Step 2: Enter Distance and Angle for Tree Height Calculation")
            distance = st.number_input("Enter distance from the tree (units):", min_value=0.1, step=0.1)
            angle = st.number_input("Enter angle to the top of the tree (degrees):", min_value=0.1, step=0.1)

            if st.button("Calculate Tree Height"):
                tree_height = calculate_tree_height(distance, angle)

            st.header("Step 3: Identify Tree")
            plant_name, wiki_url = identify_tree(tree_image_path)

            if plant_name:
                st.success(f"Identified Tree: {plant_name}")
                st.write(f"Wikipedia URL: {wiki_url}")

                st.header("Step 4: Fetch Wikipedia Details")
                wiki_details = fetch_wikipedia_details(wiki_url)
                st.text(wiki_details)
            else:
                st.error("Tree identification failed.")
        else:
            st.warning("Please recapture the image to meet conditions.")

if __name__ == "__main__":
    main()
