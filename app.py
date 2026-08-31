import streamlit as st
import io
import base64
from PIL import Image
import rembg

# Page configuration
st.set_page_config(
    page_title="Orbrick Email Signature Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Orbrick Brand Guidelines (Purple and Orange Theme)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Premium gradient header */
.header-container {
    background: linear-gradient(135deg, #5A2B86 0%, #f08519 100%);
    color: white;
    padding: 2.5rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(90, 43, 134, 0.15);
    text-align: center;
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
}

.header-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-top: 0.5rem;
}

/* Card styling */
.premium-card {
    background-color: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(90, 43, 134, 0.05);
    border: 1px solid #f1f3f5;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.premium-card:hover {
    box-shadow: 0 8px 30px rgba(90, 43, 134, 0.1);
    transform: translateY(-2px);
}

.section-title {
    color: #5A2B86;
    font-weight: 700;
    margin-top: 0;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #f1f3f5;
    padding-bottom: 0.5rem;
}

/* Custom styled Streamlit buttons to match Orbrick Branding */
div.stButton > button {
    background-color: #5A2B86 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 10px rgba(90, 43, 134, 0.15) !important;
    width: 100% !important;
}

div.stButton > button:hover {
    background-color: #f08519 !important;
    box-shadow: 0 6px 15px rgba(240, 133, 25, 0.25) !important;
    transform: translateY(-1px) !important;
}

div.stDownloadButton > button {
    background-color: #5A2B86 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 10px rgba(90, 43, 134, 0.15) !important;
    width: 100% !important;
}

div.stDownloadButton > button:hover {
    background-color: #f08519 !important;
    box-shadow: 0 6px 15px rgba(240, 133, 25, 0.25) !important;
    transform: translateY(-1px) !important;
}

/* Expander custom styling */
.streamlit-expanderHeader {
    background-color: #fcfcfc !important;
    border: 1px solid #f1f3f5 !important;
    border-radius: 8px !important;
}

/* Text inputs on focus */
.stTextInput input:focus {
    border-color: #5A2B86 !important;
    box-shadow: 0 0 0 0.2rem rgba(90, 43, 134, 0.25) !important;
}
</style>
""", unsafe_allow_html=True)

# Custom header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">Orbrick Email Signature Generator</h1>
    <div class="header-subtitle">Automate background removal, sizing, and signature template formatting.</div>
</div>
""", unsafe_allow_html=True)

# Cache background removal to make adjustment sliders smooth and real-time
@st.cache_data(show_spinner="Removing image background...")
def get_no_bg_image(image_bytes):
    return rembg.remove(image_bytes)

def process_profile_image(no_bg_bytes, zoom, x_offset, y_offset, target_size=300, sharpen_percent=50):
    # Load image from bytes
    img = Image.open(io.BytesIO(no_bg_bytes))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
        
    # Get bounding box of foreground (non-transparent pixels)
    bbox = img.getbbox()
    if bbox is None:
        width, height = img.size
        center_x, center_y = width / 2, height / 2
        foreground_size = min(width, height)
    else:
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        center_x = left + width / 2
        center_y = top + height / 2
        foreground_size = max(width, height)
        
    # Compute size of cropping square. S = foreground_size * 1.15 / zoom
    # 1.15 is the default padding factor to give the headshot some breathing room.
    S = (foreground_size * 1.15) / zoom
    
    # Calculate crop center (apply offsets in intuitive directions)
    crop_center_x = center_x - x_offset
    crop_center_y = center_y - y_offset
    
    crop_left = crop_center_x - S / 2
    crop_top = crop_center_y - S / 2
    crop_right = crop_left + S
    crop_bottom = crop_top + S
    
    # Crop the image. PIL automatically pads with transparent pixels if we crop outside.
    cropped_img = img.crop((int(crop_left), int(crop_top), int(crop_right), int(crop_bottom)))
    
    # Resize to target size (300x300 for double density clarity)
    resized_img = cropped_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    # Apply sharpening filter if requested to enhance clarity
    if sharpen_percent > 0:
        from PIL import ImageFilter
        resized_img = resized_img.filter(
            ImageFilter.UnsharpMask(radius=1.0, percent=sharpen_percent, threshold=3)
        )
        
    return resized_img

def get_image_base64_uri(pil_img):
    buffered = io.BytesIO()
    pil_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# Sidebar input fields
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #5A2B86; margin-bottom: 5px;'>Profile Details</h2>
    <p style='color: #666; font-size: 0.9rem;'>Fill in your details below</p>
</div>
""", unsafe_allow_html=True)

name = st.sidebar.text_input("Full Name", value="Yashraj Sinh", placeholder="e.g. Yashraj Sinh")
title = st.sidebar.text_input("Job Title / Role", value="Senior Associate", placeholder="e.g. Senior Associate")
phone = st.sidebar.text_input("Mobile Number", value="+91 7470437629", placeholder="e.g. +91 7470437629")
linkedin_url = st.sidebar.text_input("LinkedIn Profile URL (Optional)", placeholder="e.g. https://www.linkedin.com/in/yashraj-sinh/")

st.sidebar.markdown("---")
st.sidebar.markdown("### Profile Photo")
uploaded_file = st.sidebar.file_uploader("Upload your profile photo", type=["png", "jpg", "jpeg"])

# Image removal toggle
remove_bg_toggle = st.sidebar.checkbox("Remove Background (Recommended)", value=True)

processed_img = None
photo_src = "https://orbrick.com/wp-content/uploads/2024/08/sigImage.png"

if uploaded_file is not None:
    # Read bytes
    image_bytes = uploaded_file.read()
    
    # Check if background removal is enabled
    if remove_bg_toggle:
        processed_bytes = get_no_bg_image(image_bytes)
    else:
        # Load and convert to RGBA
        original_img = Image.open(io.BytesIO(image_bytes))
        if original_img.mode != 'RGBA':
            original_img = original_img.convert('RGBA')
        buffered = io.BytesIO()
        original_img.save(buffered, format="PNG")
        processed_bytes = buffered.getvalue()
        
    # Get dimensions for slider bounds
    temp_img = Image.open(io.BytesIO(processed_bytes))
    width, height = temp_img.size
    
    with st.sidebar.expander("📷 Adjust Photo Position & Size", expanded=True):
        zoom = st.slider("Zoom / Scale", min_value=0.5, max_value=3.0, value=1.0, step=0.1, help="Zoom in or out on your face.")
        
        # Max limit is half of the image dimension
        max_x = int(width // 2)
        max_y = int(height // 2)
        
        x_offset = st.slider("Move Horizontal (left ↔ right)", min_value=-max_x, max_value=max_x, value=0, step=1, help="Move your photo horizontally.")
        y_offset = st.slider("Move Vertical (up ↕ down)", min_value=-max_y, max_value=max_y, value=0, step=1, help="Move your photo vertically.")
        
        st.markdown("---")
        sharpen_percent = st.slider(
            "Enhance Clarity / Sharpness", 
            min_value=0, 
            max_value=150, 
            value=50, 
            step=10, 
            help="Apply a sharpening filter to reduce blurriness and make details pop."
        )
        
    # Process image (outputs 300x300 double-density resolution for extreme clarity on high-DPI screens)
    processed_img = process_profile_image(processed_bytes, zoom, x_offset, y_offset, target_size=300, sharpen_percent=sharpen_percent)
    
    # Get base64 URI
    photo_src = get_image_base64_uri(processed_img)

# Default Orbrick template HTML (Clean Table Element only, avoiding full HTML wrapper bugs)
html_template = """<table style="font-family:Tahoma, sans-serif; background: transparent !important; margin: 0; padding: 0;" width="360" cellpadding="0" cellspacing="0">
	<tbody><tr>
		<td style="width:140px; padding:0; text-align:center; vertical-align:middle;" valign="middle" width="140">
			<img width="150" height="150" border="0" style="width:150px; height:150px; border:0; display:block; border-radius:0px;" src="[[PHOTO_SRC]]">
		</td>
		<td style="padding:0; padding-left:20px; vertical-align:top;" valign="top"> 
			<table style="font-family:Tahoma, sans-serif; background: transparent !important;" cellpadding="0" cellspacing="0" width="200">
				<tbody>
					<tr>
						<td style="font-family:Tahoma, sans-serif; color:#ed5a24; padding-bottom:6px; padding-top:0; padding-left:0; padding-right:0; vertical-align:top;" valign="top"><strong><span style="font-family:Tahoma, sans-serif; color:#5A2B86; font-size:14pt;">[[NAME]]</span></strong><br><span style="font-family:Tahoma, sans-serif; color:#f08519; font-size:10pt; line-height:18px;">[[TITLE]]</span> </td> 
					</tr> 
					<tr>
						<td style="font-family:Tahoma, sans-serif; color:#5A2B86; padding-bottom:6px; padding-top:0; padding-left:0; padding-right:0; line-height:18px; vertical-align:top;" valign="top">
							<span style="font-family:Tahoma, sans-serif; color:#5A2B86; font-size:10pt;"><b>M:</b> [[PHONE]]</span>
							<br />
						</td>
					</tr>
					<tr>
						<td style="font-family:Tahoma, sans-serif; color:#5A2B86;  padding-bottom:6px; padding-top:0; padding-left:0; padding-right:0; line-height:18px; vertical-align:top;" valign="top">
							<span style="font-family:Tahoma, sans-serif; color:#5A2B86; font-size:10pt;"><a href="http://www.orbrick.com" target="_blank" rel="noopener" style="text-decoration:none;"><img src="https://orbrick.com/wp-content/uploads/2024/08/Main-logoTransparent.png" width="180" /></a></span><br /><br />
						
							<span><a href="[[LINKEDIN_URL]]" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://orbrick.com/wp-content/uploads/2024/08/LinkedIn_logo_initials.png"></a></span>
							<span><a href="https://www.orbrick.com/blog" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://orbrick.com/wp-content/uploads/2024/08/rss-round-color-icon-2.png"></a></span>
							<span><a href="http://www.youtube.com/@TheOrbrickRoad" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://cdn1.iconfinder.com/data/icons/social-media-circle-6/1024/youtube-256.png"></a></span>
							<span><a href="https://instagram.com" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://cdn1.iconfinder.com/data/icons/social-media-circle-6/1024/instagram-256.png"></a></span><br />
						</td>
					</tr>
				</tbody>
			</table> 
		</td> 
	</tr>
</tbody>
</table>"""

# Construct the output HTML
linkedin = linkedin_url.strip()
if linkedin != "":
    if not (linkedin.startswith("http://") or linkedin.startswith("https://")):
        linkedin = "https://" + linkedin
else:
    linkedin = "https://www.linkedin.com/company/orbrick"

output_html = html_template.replace("[[PHOTO_SRC]]", photo_src)\
                             .replace("[[NAME]]", name)\
                             .replace("[[TITLE]]", title)\
                             .replace("[[PHONE]]", phone)\
                             .replace("[[LINKEDIN_URL]]", linkedin)

# Prepare complete HTML document format for standalone file downloads
download_html = f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
	<HEAD>
		<TITLE>Orbrick Email Signature</TITLE>
		<META content="text/html; charset=utf-8" http-equiv="Content-Type"></HEAD>
	<BODY style="font-size: 10pt; font-family: Tahoma, sans-serif; margin: 0; padding: 0;">
        {output_html}
	</BODY>
</HTML>"""

# Layout centered preview card
st.markdown('<div class="premium-card" style="text-align: center; max-width: 800px; margin: 0 auto 2rem auto;">', unsafe_allow_html=True)
st.markdown('<h3 class="section-title" style="text-align: center; color: #5A2B86;">✨ Your Email Signature Preview</h3>', unsafe_allow_html=True)

# Render raw HTML safely without Markdown engine interference using st.html
st.html(
    f'<div style="display: flex; justify-content: center; align-items: center; border: 1px dashed #d1d5db; padding: 25px; border-radius: 12px; background-color: white; box-sizing: border-box; margin-bottom: 1.5rem;">'
    f'{output_html}'
    f'</div>'
)

st.markdown("<p style='color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; text-align: center;'>💡 <b>Tip:</b> Click and drag to select the preview signature directly, copy it (Ctrl+C), and paste it directly into Outlook!</p>", unsafe_allow_html=True)

st.markdown("---")

# Download buttons row
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    st.download_button(
        label="💾 Download Signature HTML",
        data=download_html,
        file_name=f"orbrick_signature_{name.replace(' ', '_').lower()}.html",
        mime="text/html",
        help="Download the full HTML signature file to your computer."
    )
with btn_col2:
    if processed_img is not None:
        img_byte_arr = io.BytesIO()
        processed_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        st.download_button(
            label="📷 Download Processed Photo",
            data=img_byte_arr,
            file_name=f"photo_150x150_{name.replace(' ', '_').lower()}.png",
            mime="image/png",
            help="Download your transparent profile picture (300x300 double resolution for high-DPI screens)."
        )
    else:
        st.button("📷 Download Processed Photo (Upload required)", disabled=True)
        
# Raw HTML code toggle
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🛠️ View HTML Source Code"):
    st.code(output_html, language="html")
    
st.markdown('</div>', unsafe_allow_html=True)

# Layout centered instructions card below the preview
st.markdown('<div class="premium-card" style="max-width: 800px; margin: 0 auto 2rem auto;">', unsafe_allow_html=True)
st.markdown('<h3 class="section-title" style="text-align: center; color: #5A2B86;">📝 Installation Instructions</h3>', unsafe_allow_html=True)

inst_col1, inst_col2 = st.columns(2)

with inst_col1:
    st.markdown("""
    <div style="padding-right: 15px; border-right: 1px solid #f1f3f5; height: 100%;">
        <h4 style="color: #f08519; margin-top: 0; font-weight: 600;">Method 1: Direct Selection (Easiest)</h4>
        <ol style="padding-left: 1.2rem; line-height: 1.6; color: #444; font-size: 0.95rem;">
            <li><strong>Drag and select</strong> the email signature in the preview box above.</li>
            <li>Copy it (<strong>Ctrl+C</strong> on Windows, <strong>Cmd+C</strong> on Mac).</li>
            <li>Open your Outlook Settings (Web or Desktop) and go to the signature section.</li>
            <li>Paste (<strong>Ctrl+V</strong> or <strong>Cmd+V</strong>) it into the editor.</li>
            <li>Save your settings!</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with inst_col2:
    st.markdown("""
    <div style="padding-left: 15px; height: 100%;">
        <h4 style="color: #f08519; margin-top: 0; font-weight: 600;">Method 2: Native Image Embedding</h4>
        <p style="font-size: 0.85rem; color: #666; font-style: italic; margin-bottom: 0.5rem;">Outlook occasionally blocks raw Base64 images for external recipients. If this happens:</p>
        <ol style="padding-left: 1.2rem; line-height: 1.6; color: #444; font-size: 0.95rem;">
            <li>Click <strong>Download Signature HTML</strong> to download your signature file.</li>
            <li>Click <strong>Download Processed Photo</strong> to save your 300x300px PNG picture.</li>
            <li>Copy the signature from the HTML file and paste it into Outlook.</li>
            <li>Delete the placeholder photo in Outlook's editor.</li>
            <li>Click Outlook's <strong>Insert Picture</strong> icon and select the downloaded PNG photo.</li>
            <li>Save!</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-top: 1.5rem; border-top: 1px solid #f1f3f5; padding-top: 1rem;">
    <span style="font-size: 0.95rem; color: #5A2B86; font-weight: 600;">💬 Need help? Check in with someone whose signature looks okay!</span>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
