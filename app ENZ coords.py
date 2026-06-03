import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import re
from pyproj import Transformer

# App Page Configurations
st.set_page_config(page_title="UK Site Stamp", page_icon="🏗️", layout="centered")

st.title("🏗️ UK Site Grid Photo Stamper")
st.write("Take a photo on-site or type coordinates to burn Easting & Northing directly onto the image.")

# Conversion logic: WGS84 (lat/lon) -> OSGB36 (UK National Grid)
def convert_to_osgb36(lat, lon):
    try:
        transformer = Transformer.from_crs("epsg:4326", "epsg:27700", always_xy=True)
        easting, northing = transformer.transform(lon, lat)
        return round(easting, 2), round(northing, 2)
    except Exception:
        return None, None

# Main coordinate input options
mode = st.radio("Choose Input Method:", ("Type Coordinates Manually", "Use Mobile Camera (No Metadata)"))

easting_val, northing_val = None, None

if mode == "Type Coordinates Manually":
    col1, col2 = st.columns(2)
    with col1:
        easting_input = st.text_input("Enter Easting (6 digits):", placeholder="e.g., 532145")
    with col2:
        northing_input = st.text_input("Enter Northing (6 digits):", placeholder="e.g., 180432")
    
    if easting_input and northing_input:
        try:
            easting_val = float(re.sub(r'[^\d.]', '', easting_input))
            northing_val = float(re.sub(r'[^\d.]', '', northing_input))
        except ValueError:
            st.error("Please enter numbers only.")

elif mode == "Use Mobile Camera (No Metadata)":
    st.info("💡 Note: Standard web browsers strip GPS metadata from live uploads. Please provide your manual grid inputs below to overlay onto your photo.")
    col1, col2 = st.columns(2)
    with col1:
        easting_input = st.text_input("Site Easting for stamp:", placeholder="532145")
    with col2:
        northing_input = st.text_input("Site Northing for stamp:", placeholder="180432")
        
    if easting_input and northing_input:
        easting_val = float(easting_input)
        northing_val = float(northing_input)

# Image Upload / Camera Input UI
uploaded_file = st.camera_input("Snap a Photo") if mode == "Use Mobile Camera (No Metadata)" else st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    if easting_val is None or northing_val is None:
        st.warning("⚠️ Please input your Easting and Northing values above before processing the image.")
    else:
        # Open the image
        img = Image.open(uploaded_file)
        
        # Setup Text Overlay parameters
        stamp_text = f"UK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        
        # Dynamic font scaling based on photo width
        draw = ImageDraw.Draw(img)
        font_size = int(img.width * 0.035)
        try:
            font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size) # Common linux server font
        except IOError:
            font = ImageFont.load_default()

        # Position (Bottom Left)
        text_position = (int(img.width * 0.05), int(img.height * 0.82))
        
        # Drawing text drop shadow for visibility over light/dark backgrounds
        draw.text((text_position[0]+3, text_position[1]+3), stamp_text, fill="black", font=font)
        draw.text(text_position, stamp_text, fill="yellow", font=font)
        
        # Display results
        st.success("✅ Coordinates Burned Successfully!")
        st.image(img, caption="Stamped Output Preview", use_container_width=True)
        
        # Provide Download Button for the phone gallery
        img.save("temp_output.jpg", format="JPEG")
        with open("temp_output.jpg", "rb") as file:
            st.download_button(
                label="📥 Save Stamped Image to Phone",
                data=file,
                file_name=f"Stamped_E{int(easting_val)}_N{int(northing_val)}.jpg",
                mime="image/jpeg"
            )