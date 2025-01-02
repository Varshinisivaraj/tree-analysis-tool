import streamlit as st
import cv2
import requests
from PIL import Image
from io import BytesIO
import tempfile
from math import sqrt, pow
from dotenv import load_dotenv
import os
import uuid

# Load environment variables
load_dotenv()

def capture_image():
    st.write("Launching camera...")
    cap = cv2.VideoCapture(0)
    temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name

    if not cap.isOpened():
        st.error("Unable to access the camera.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to grab frame.")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, caption="Live Feed", channels="RGB")

        # Generate a unique key to avoid DuplicateWidgetID error
        unique_key = str(uuid.uuid4())

        if st.button("Capture Full Tree Image", key=unique_key):
            cv2.imwrite(temp_image_path, frame)
            st.success(f"Image saved at {temp_image_path}")
            st.session_state.tree_image_path = temp_image_path  # Save the image path to session state
            break

    cap.release()

def validate_image(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        st.write(f"Image dimensions: {width}x{height}")
        if height < 500:  # Example condition
            st.warning("The image is too small. Please capture again.")
            return False
    return True

def calculate_tree_height(distance, angle):
    height = distance * sqrt(1 + pow(angle, 2))  # Simplified height calculation
    st.write(f"Calculated tree height: {height:.2f} units")
    return height

def identify_tree(image_path):
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

    # Check if the tree image has already been captured
    if 'tree_image_path' not in st.session_state:
        st.header("Step 1: Capture Full Tree Image")
        capture_button = st.button("Capture Full Tree Image", key="capture_tree_image_button")

        if capture_button:
            capture_image()

        st.warning("Please capture the tree image before proceeding.")

    else:
        tree_image_path = st.session_state.tree_image_path
        if validate_image(tree_image_path):
            st.header("Step 2: Enter Distance and Angle for Tree Height Calculation")
            distance = st.number_input("Enter distance from the tree (units):", min_value=0.1, step=0.1)
            angle = st.number_input("Enter angle to the top of the tree (degrees):", min_value=0.1, step=0.1)

            if st.button("Calculate Tree Height", key="calculate_height_button"):
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
