import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

# Page Configurations
st.set_page_config(page_title="Auto UK Site Stamp", page_icon="🛰️", layout="centered")

st.title("🛰️ Automated UK Site Grid Stamper")
st.write("Click 'Fetch Phone GPS' first, then snap your photo!")

# 1. LIVE HARDWARE GPS FETCH BUTTON
st.subheader("1. Get Location from Phone GPS")
location = streamlit_geolocation()

easting_val, northing_val = None, None

# If the phone provides GPS data, immediately convert it to OSGB36
if location and location.get('latitude') is not None:
    lat = location['latitude']
    lon = location['longitude']
    accuracy = location.get('accuracy', 'Unknown')
    
    # Convert WGS84 (lat/lon) -> OSGB36 (UK National Grid)
    try:
        transformer = Transformer.from_crs("epsg:4326", "epsg:27700", always_xy=True)
        easting_val, northing_val = transformer.transform(lon, lat)
        easting_val = round(easting_val, 2)
        northing_val = round(northing_val, 2)
        
        # Display the live tracked coordinates to the user
        st.success(f"📍 GPS Locked! Accuracy: ±{accuracy}m")
        st.metric(label="Current Easting (X)", value=f"{easting_val}")
        st.metric(label="Current Northing (Y)", value=f"{northing_val}")
    except Exception as e:
        st.error("Error converting GPS coordinates to British National Grid.")
else:
    st.info("👋 Tap the small location button above. Your phone will ask: 'Allow web app to access your location?' Tap ALLOW.")

# 2. CAMERA INPUT
st.subheader("2. Snap Site Photo")
uploaded_file = st.camera_input("Take Picture")

if uploaded_file is not None:
    if easting_val is None or northing_val is None:
        st.error("❌ Stop! You must tap the 'Fetch Phone GPS' button above and allow location tracking before taking the picture.")
    else:
        # Open the freshly snapped photo
        img = Image.open(uploaded_file)
        
        # Format the text overlay string
        stamp_text = f"UK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        
        # Smart text scaling based on picture size
        draw = ImageDraw.Draw(img)
        font_size = int(img.width * 0.085)
        try:
            font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Position (Bottom Left Corner)
        text_position = (int(img.width * 0.05), int(img.height * 0.82))
        
        # Draw text drop shadow (black) and main text (white)
        draw.text((text_position[0]+3, text_position[1]+3), stamp_text, fill="black", font=font)
        draw.text(text_position, stamp_text, fill="white", font=font)
        
        st.success("✅ Grid Coordinates Burned Into Image!")
        st.image(img, caption="Stamped Preview", use_container_width=True)
        
        # 3. SAVE DIRECTLY TO GALLERY BUTTON
        img.save("site_stamp_output.jpg", format="JPEG")
        with open("site_stamp_output.jpg", "rb") as file:
            st.download_button(
                label="📥 Save Stamped Photo to Gallery",
                data=file,
                file_name=f"OSGB_E{int(easting_val)}_N{int(northing_val)}.jpg",
                mime="image/jpeg"
            )
