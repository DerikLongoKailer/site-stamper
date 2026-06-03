Python
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer
import base64
from io import BytesIO

# Page Configurations
st.set_page_config(page_title="Auto UK Site Stamp", page_icon="🛰️", layout="centered")

st.title("🛰️ Automated UK Site Grid Stamper")

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
uploaded_file = st.camera_input("Take Picture")

if uploaded_file is not None:
    if easting_val is None or northing_val is None:
        st.error("❌ Stop! You must fetch GPS coordinates before taking the picture.")
    else:
        img = Image.open(uploaded_file)
        
        stamp_text = f"UK Grid (OSGB36)\nE: {easting_val}\nN: {northing_val}"
        
        draw = ImageDraw.Draw(img)
        font_size = int(img.width * 0.135)
        try:
            font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Position (Bottom Left Corner)
        text_position = (int(img.width * 0.05), int(img.height * 0.82))
        
        # DRAW ONLY MAIN TEXT (Shadow text completely removed here)
        draw.text(text_position, stamp_text, fill="yellow", font=font)
        
        st.success("✅ Grid Coordinates Burned Into Image!")
        st.image(img, caption="Stamped Preview", use_container_width=True)
        
        # 3. THE SEMI-AUTOMATIC DOWNLOAD TRIGGER
        # This converts the file to web-data and tricks the phone browser into downloading it instantly
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        filename = f"OSGB_E{int(easting_val)}_N{int(northing_val)}.jpg"
        
        # Injecting an automatic browser download prompt injection
        components_code = f"""
            <script>
            var a = window.parent.document.createElement('a');
            a.href = 'data:image/jpeg;base64,{img_str}';
            a.download = '{filename}';
            window.parent.document.body.appendChild(a);
            a.click();
            window.parent.document.body.removeChild(a);
            </script>
        """
        st.components.v1.html(components_code, height=0)
        st.info("📥 Check your phone's Notification Bar, Downloads folder, or Gallery for the saved image!
