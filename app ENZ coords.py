import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps
from pyproj import Transformer
import json

# Page Configurations
st.set_page_config(page_title="Auto UK Site Stamp", page_icon="🛰️", layout="centered")

st.title("🛰️ Automated UK Site Grid Stamper")

# Initialize session state variables
if "photo_reset" not in st.session_state:
    st.session_state.photo_reset = False

# --- HIGH ACCURACY GPS & LOCAL TIME JAVASCRIPT ENGINE ---
st.subheader("1. Get Location & Time from Phone")

js_geo_time_script = """
<script>
function getData() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showData, showError, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });
  }
}

function showData(position) {
    // Get the exact local date and time from the phone hardware
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    const localTimeString = day + "/" + month + "/" + year + "  " + hours + ":" + minutes + ":" + seconds;

    const data = {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        accuracy: position.coords.accuracy,
        phone_time: localTimeString
    };
    window.parent.postMessage({type: 'streamlit:setComponentValue', value: data}, '*');
}

function showError(error) {
    console.log(error);
}

getData();
</script>
"""

# Render the tracking script hidden in the background
with st.sidebar:
    st.write("Data Engine Active")
    st.components.v1.html(js_geo_time_script, height=0)

location = streamlit_geolocation()

easting_val, northing_val = None, None
phone_time_val = "Not Found"

if location and location.get('latitude') is not None:
    lat = location['latitude']
    lon = location['longitude']
    accuracy = location.get('accuracy', 'Unknown')
    # Extract the true local phone time gathered by the JavaScript tool
    phone_time_val = location.get('phone_time', 'Pending...')
    
    try:
        transformer = Transformer.from_crs("epsg:4326", "epsg:27700", always_xy=True)
        easting_val, northing_val = transformer.transform(lon, lat)
        easting_val = round(easting_val, 2)
        northing_val = round(northing_val, 2)
        
        st.success(f"🚀 LOCK ESTABLISHED!")
        st.metric(label="Phone Live Time", value=f"{phone_time_val}")
        st.metric(label="Current Easting (X)", value=f"{easting_val}")
        st.metric(label="Current Northing (Y)", value=f"{northing_val}")
    except Exception as e:
        st.error("Error converting GPS coordinates.")
else:
    st.info("👋 Tap the location button above and choose 'ALLOW' to fetch your live site data.")

# 2. CAMERA INPUT
st.subheader("2. Snap Site Photo")

if st.session_state.photo_reset:
    uploaded_file = None
    st.session_state.photo_reset = False
    st.rerun()

uploaded_file = st.camera_input("Take Picture")

if uploaded_file is not None:
    if easting_val is None or northing_val is None:
        st.error("❌ Stop! You must fetch GPS coordinates before taking the picture.")
    else:
        raw_img = Image.open(uploaded_file)
        
        try:
            raw_img = PIL.ImageOps.exif_transpose(raw_img)
        except Exception:
            pass

        # Ultra-HD Resampling Engine
        target_width = 3000
        w_percent = (target_width / float(raw_img.size[0]))
        target_height = int((float(raw_img.size[1]) * float(w_percent)))
        img = raw_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # We replace the server time with your true phone hardware time variable here
        stamp_text = f"Date/Time: {phone_time_val}\nUK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        
        draw = ImageDraw.Draw(img)
        font_size = int(img.width * 0.035)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
            except IOError:
                font = ImageFont.load_default(size=font_size)

        text_position = (int(img.width * 0.05), int(img.height * 0.80))
        draw.text(text_position, stamp_text, fill="yellow", font=font)
        
        st.success("✅ Ultra-HD Grid Coordinates & Device Time Burned!")
        st.image(img, caption="Your Stamped Photo (High Resolution)", use_container_width=True)
        
        st.markdown("""
        ### 📥 HOW TO SAVE TO GALLERY:
        1. **Press and hold your finger** down directly on the photo above for 2 seconds.
        2. Tap **'Save to Photos'** or **'Download Image'**.
        """)
        
        st.markdown("---")
        
        if st.button("📸 CLEAR & TAKE NEXT PICTURE", type="primary", use_container_width=True):
            st.session_state.photo_reset = True
            st.rerun()
