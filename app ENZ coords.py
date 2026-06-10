import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps
from pyproj import Transformer
from datetime import datetime
import zoneinfo
import io

# Page Configurations
st.set_page_config(page_title="Auto UK Site Stamp", page_icon="🛰️", layout="centered")

st.title("🛰️ Automated UK Site Grid Stamper")

# Initialize session state variables
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# 1. LIVE HARDWARE GPS FETCH BUTTON
st.subheader("1. Get Location from Phone GPS")

# Using the standard reliable plugin solo to eliminate the "Pending..." lock
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
        
        st.success(f"🚀 LOCK ESTABLISHED! Accuracy: ±{accuracy}m")
        st.metric(label="Current Easting (X)", value=f"{easting_val}")
        st.metric(label="Current Northing (Y)", value=f"{northing_val}")
    except Exception as e:
        st.error("Error converting GPS coordinates.")
else:
    st.info("👋 Tap the location button above and choose 'ALLOW' to fetch your live site grid.")

# 2. CAMERA/FILE INPUT
st.subheader("2. Snap Site Photo")

# Unique key strategy used to reset the native file uploader widget cleanly
uploaded_file = st.file_uploader(
    "Tap below to take a Native High-Res Photo or upload from Gallery", 
    type=["jpg", "jpeg", "png"],
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    if easting_val is None or northing_val is None:
        st.error("❌ Stop! You must fetch GPS coordinates before taking the picture.")
    else:
        raw_img = Image.open(uploaded_file)
        
        # --- GUARANTEED UK LOCAL TIME ENGINE ---
        uk_tz = zoneinfo.ZoneInfo("Europe/London")
        current_time_str = datetime.now(uk_tz).strftime("%d/%m/%Y  %H:%M:%S")
        
        try:
            raw_img = PIL.ImageOps.exif_transpose(raw_img)
        except Exception:
            pass

        # High-Quality Resampling Engine (Downscaling safely if the phone image is larger than 3000px width)
        target_width = 3000
        if raw_img.width > target_width:
            w_percent = (target_width / float(raw_img.size[0]))
            target_height = int((float(raw_img.size[1]) * float(w_percent)))
            img = raw_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            img = raw_img.copy() # Keep native max details if smaller than 3000px
        
        # Combine the fixed timezone stamp and coordinates
        stamp_text = f"Date/Time: {current_time_str}\nUK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        
        draw = ImageDraw.Draw(img)
        font_size = int(img.width * 0.035)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
            except IOError:
                font = ImageFont.load_default(size=font_size)

        # Dynamic text positioning relative to the high-res dimensions
        text_position = (int(img.width * 0.05), int(img.height * 0.80))
        draw.text(text_position, stamp_text, fill="yellow", font=font)
        
        st.success("✅ Ultra-HD Grid Coordinates & True UK Time Burned!")
        st.image(img, caption="Your Stamped Photo (High Resolution)", use_container_width=True)
        
        # Download button alternative for cleaner image saving on modern browsers
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        
        st.download_button(
            label="📥 DOWNLOAD STAMPED PHOTO TO GALLERY",
            data=buffered.getvalue(),
            file_name=f"SiteStamp_{easting_val}_{northing_val}.jpg",
            mime="image/jpeg",
            use_container_width=True,
            type="secondary"
        )
        
        st.markdown("---")
        
        if st.button("📸 CLEAR & TAKE NEXT PICTURE", type="primary", use_container_width=True):
            st.session_state.uploader_key += 1
            st.rerun()
