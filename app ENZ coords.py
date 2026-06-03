import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps
from pyproj import Transformer

# Page Configurations
st.set_page_config(page_title="Auto UK Site Stamp", page_icon="🛰️", layout="centered")

st.title("🛰️ Automated UK Site Grid Stamper")

# Initialize session state variable to handle resetting the camera
if "photo_reset" not in st.session_state:
    st.session_state.photo_reset = False

# 1. LIVE HARDWARE GPS FETCH BUTTON
st.subheader("1. Get Location from Phone GPS")
location = streamlit_geolocation()

easting_val, northing_val = None, None

if location and location.get('latitude') is not None:
    lat = location['latitude']
    lon = location['longitude']
    accuracy = location.get('accuracy', 'Unknown')
    
    try:
        transformer = Transformer.from_crs("epsg:4326", "epsg:27700", always_xy=True)
        easting_val, northing_val = transformer.transform(lon, lat)
        easting_val = round(easting_val, 2)
        northing_val = round(northing_val, 2)
        
        st.success(f"📍 GPS Locked! Accuracy: ±{accuracy}m")
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
        
        # Ensure correct image rotation based on phone orientation metadata
        try:
            raw_img = PIL.ImageOps.exif_transpose(raw_img)
        except Exception:
            pass

        # --- ADVANCED ULTRA-SHARP HD RESAMPLING ENGINE ---
        # We manually blow up the canvas to a massive width (e.g., 3000px) using high-quality LANCZOS interpolation
        # This increases the pixel density dramatically so the font engine has sharp sub-pixels to draw on.
        target_width = 3000
        w_percent = (target_width / float(raw_img.size[0]))
        target_height = int((float(raw_img.size[1]) * float(w_percent)))
        
        # High-Fidelity upscale
        img = raw_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        stamp_text = f"UK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        
        draw = ImageDraw.Draw(img)
        
        # Dynamic font scaling based on our new 3000px crisp baseline
        font_size = int(img.width * 0.035)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
            except IOError:
                font = ImageFont.load_default(size=font_size)

        # Set position relative to the new high-res canvas sizes
        text_position = (int(img.width * 0.05), int(img.height * 0.86))
        
        # Draw text at maximum anti-aliasing quality
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
