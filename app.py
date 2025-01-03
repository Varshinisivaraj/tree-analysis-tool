import streamlit as st
import requests
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
        self.image_path = None

    def run(self):
        st.title("Tree Image Analysis Tool")

        # Step 1: Capture Image with Camera
        uploaded_image = st.camera_input("Capture Tree Image")

        if uploaded_image is not None:
            self.image_path = os.path.join("temp", f"{uploaded_image.name}")
            with open(self.image_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

            # Step 2: Display the captured image
            st.image(self.image_path, caption="Captured Tree Image", use_column_width=True)

            # Step 3: Identify Tree
            st.header("Step 3: Identify Tree")
            plant_name, wiki_url = TreeIdentification.identify_tree(self.image_path)

            if plant_name:
                st.success(f"Identified Tree: {plant_name}")
                st.write(f"Wikipedia URL: {wiki_url}")

                # Step 4: Fetch Wikipedia Details
                st.header("Step 4: Fetch Wikipedia Details")
                wiki_details = WikipediaDetails.fetch_wikipedia_details(wiki_url)
                st.text(wiki_details)
            else:
                st.error("Tree identification failed.")


if __name__ == "__main__":
    app = TreeApp()
    app.run()
