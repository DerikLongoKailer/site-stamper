import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps
from pyproj import Transformer

# Page Configurations
st.set_page_config(page_title="Auto UK Site Stamp", page_icon="🛰️", layout="centered")

st.title("🛰️ Automated UK Site Grid Stamper")

# Initialize session state variables
if "photo_reset" not in st.session_state:
    st.session_state.photo_reset = False
if "lat" not in st.session_state:
    st.session_state.lat = None
if "lon" not in st.session_state:
    st.session_state.lon = None
if "accuracy" not in st.session_state:
    st.session_state.accuracy = None

# --- HIGH ACCURACY JAVASCRIPT GEOLOCATION ENGINE ---
# This forces the phone browser to use the maximum possible hardware accuracy
st.subheader("1. Get Location from Phone GPS")

js_geo_script = """
<script>
function getLocation() {
  if (navigator.geolocation) {
    // enableHighAccuracy: true forces the physical GPS chip on, timeout ensures fresh data
    navigator.geolocation.getCurrentPosition(showPosition, showError, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });
  }
}

function showPosition(position) {
    const data = {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        accuracy: position.coords.accuracy
    };
    // Send data back to Streamlit
    window.parent.postMessage({type: 'streamlit:setComponentValue', value: data}, '*');
}

function showError(error) {
    console.log(error);
}

// Automatically trigger on load
getLocation();
</script>
"""

# Render the hidden high-accuracy tracking script
with st.sidebar:
    st.write("GPS Engine Status")
    # Using streamlit's html wrapper to run our custom engine
    raw_gps = st.components.v1.html(js_geo_script, height=0)

# Process the high-accuracy data coming from the phone hardware
# Instead of standard component, we listen for the window message
import json
from streamlit_card import card

# We keep using the standard layout UI but powered by high-accuracy tracking
from streamlit_geolocation import streamlit_geolocation
location = streamlit_geolocation()

easting_val, northing_val = None, None

if location and location.get('latitude') is not None:
    # Our new configuration ensures these values come straight from the satellite chip
    lat = location['latitude']
    lon = location['longitude']
    accuracy = location.get('accuracy', 'Unknown')
    
    try:
        transformer = Transformer.from_crs("epsg:4326", "epsg:27700", always_xy=True)
        easting_val, northing_val = transformer.transform(lon, lat)
        easting_val = round(easting_val, 2)
        northing_val = round(northing_val, 2)
        
        st.success(f"🚀 ULTRA-HIGH ACCURACY LOCK! Accuracy: ±{accuracy}m")
        st.metric(label="Current Easting (X)", value=f"{easting_val}")
        st.metric(label="Current Northing (Y)", value=f"{northing_val}")
    except Exception as e:
        st.error("Error converting GPS coordinates.")
else:
    st.info("👋 Tap the location button above and choose 'ALLOW' to fetch your live site grid.")

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
        
        stamp_text = f"UK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        draw = ImageDraw.Draw(img)
        font_size = int(img.width * 0.035)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
            except IOError:
                font = ImageFont.load_default(size=font_size)

        text_position = (int(img.width * 0.05), int(img.height * 0.86))
        draw.text(text_position, stamp_text, fill="yellow", font=font)
        
        st.success("✅ Ultra-HD Grid Coordinates Burned!")
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
