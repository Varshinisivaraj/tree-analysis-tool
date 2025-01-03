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


class CameraHandler:
    def __init__(self):
        """Initialize session state variables."""
        if "camera_active" not in st.session_state:
            st.session_state.camera_active = False
        if "image_path" not in st.session_state:
            st.session_state.image_path = None

    def start_camera(self):
        """Start the camera feed."""
        st.session_state.camera_active = True

    def capture_image(self):
        """Capture image when the camera is active."""
        if st.session_state.camera_active:
            st.write("Launching camera...")
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                st.error("Unable to access the camera.")
                st.session_state.camera_active = False
                return None

            ret, frame = cap.read()
            if not ret:
                st.error("Failed to grab frame.")
                st.session_state.camera_active = False
                return None

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, caption="Live Feed", channels="RGB")

            if st.button("Capture Image", key="capture_button"):
                temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
                cv2.imwrite(temp_image_path, frame)
                st.success(f"Image saved at {temp_image_path}")
                st.session_state.image_path = temp_image_path
                st.session_state.camera_active = False  # Stop camera feed
                cap.release()
                return temp_image_path

            cap.release()

        return None


class TreeIdentification:
    @staticmethod
    def identify_tree(image_path):
        """Identify tree using Plant.id API."""
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


class WikipediaDetails:
    @staticmethod
    def fetch_wikipedia_details(wiki_url):
        """Fetch details from Wikipedia."""
        if wiki_url:
            response = requests.get(wiki_url)
            if response.status_code == 200:
                st.success("Wikipedia page fetched successfully.")
                return response.text[:500]  # Display first 500 characters
            else:
                st.error("Failed to fetch Wikipedia details.")
        return ""


class TreeApp:
    def __init__(self):
        self.camera_handler = CameraHandler()

    def run(self):
        # Initialize session state variables
        if "image_path" not in st.session_state:
            st.session_state.image_path = None

        st.title("Tree Image Analysis Tool")

        # Step 1: Start Camera
        if st.button("Start Camera", key="start_camera"):
            self.camera_handler.start_camera()

        # Step 2: Capture Image
        image_path = self.camera_handler.capture_image()

        # Step 3: Proceed if image is captured
        if image_path:
            st.session_state.image_path = image_path
            st.success("Image captured successfully!")
            st.image(Image.open(image_path), caption="Captured Tree Image", use_column_width=True)

            # Step 4: Identify Tree
            st.header("Step 4: Identify Tree")
            plant_name, wiki_url = TreeIdentification.identify_tree(image_path)

            if plant_name:
                st.success(f"Identified Tree: {plant_name}")
                st.write(f"Wikipedia URL: {wiki_url}")

                # Step 5: Fetch Wikipedia Details
                st.header("Step 5: Fetch Wikipedia Details")
                wiki_details = WikipediaDetails.fetch_wikipedia_details(wiki_url)
                st.text(wiki_details)
            else:
                st.error("Tree identification failed.")


if __name__ == "__main__":
    app = TreeApp()
    app.run()
