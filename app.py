# ================================
# app.py – AI LinkedIn Auto Poster (Styled)
# ================================

import os
import time
import requests
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from huggingface_hub import InferenceClient

# -------------------------------
# LOAD ENV VARIABLES
# -------------------------------
load_dotenv()
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

REDIRECT_URI = "https://linkedinpostgenerator1234.streamlit.app/"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(
    page_title="AI LinkedIn Auto Poster",
    layout="centered"
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    /* Softer LinkedIn-inspired background */
    .stApp {
        background: linear-gradient(135deg, #007182 20%, #001699 100%);
        color: white;
    }

    /* Larger headings with bright accents */
    h1, h2, h3, h4, h5, h6 {
        font-size: 2.2em !important;
        font-weight: 800 !important;
        color: #FFD700 !important; /* Bright gold accent */
    }

    /* Subheaders with softer highlight */
    .stMarkdown h2 {
        font-size: 1.4em !important;
        color: #FFDDC1 !important; /* Soft peach */
    }

    /* Buttons with bold colors */
    .stButton>button {
        background-color: #FF5733 !important; /* Bright orange-red */
        color: white !important;
        border-radius: 8px !important;
        font-size: 1.1em !important;
        font-weight: bold !important;
    }
    .stButton>button:hover {
        background-color: #FFC300 !important; /* Bright yellow hover */
        color: black !important;
    }

    /* Divider styling */
    hr {
        border: 2px solid #FFD700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    /* Style the "Login with LinkedIn" link */
    a[href*="linkedin.com/oauth/v2/authorization"] {
        color: #32CD32 !important;   /* Bright lime green */
        font-style: italic;
        font-size: 1.2em;
        text-decoration: underline;

    }
    a[href*="linkedin.com/oauth/v2/authorization"]:hover {
        color: #FF4500 !important;   /* Orange-red on hover */
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# -------------------------------
# TITLE
# -------------------------------
st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Generate AI content and post it directly to LinkedIn")

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "has_content" not in st.session_state:
    st.session_state.has_content = False

if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False

if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

# -------------------------------
# (Keep your existing logic below unchanged)
# -------------------------------

# -------------------------------
# TEXT GENERATION (GEMINI)
# -------------------------------
def generate_text(topic: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.7
    )

    prompt = PromptTemplate(
        input_variables=["topic"],
        template="""
        Write a professional and engaging LinkedIn post (100–120 words) about:
        "{topic}"

        Tone: professional, inspiring, positive.
        """
    )

    formatted_prompt = prompt.format(topic=topic)
    response = llm.invoke(formatted_prompt)

    return response.content

# -------------------------------
# IMAGE GENERATION (HF with retry)
# -------------------------------
def generate_image(prompt, output_path="generated_image.png"):
    client = InferenceClient(
        model="black-forest-labs/FLUX.1-schnell",
        token=HF_API_KEY
    )

    for attempt in range(3):
        try:
            image = client.text_to_image(prompt)
            image.save(output_path)
            return output_path
        except Exception as e:
            print(f"Image retry {attempt+1}: {e}")
            time.sleep(5)

    raise RuntimeError("Image generation failed")

# -------------------------------
# AI PIPELINE (RUN ONCE)
# -------------------------------
def ai_generate_pipeline(query):
    text = generate_text(query)
    image_path = generate_image(
        f"Professional illustration representing {query}"
    )
    return text, image_path

# -------------------------------
# LINKEDIN OAUTH HELPERS
# -------------------------------
def get_access_token(auth_code):
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    r = requests.post(TOKEN_URL, data=payload)
    if r.status_code == 200:
        return r.json()["access_token"]
    return None


def get_user_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    data = r.json()
    return f"urn:li:person:{data['sub']}"

# -------------------------------
# LINKEDIN POST HELPERS
# -------------------------------
def upload_image_to_linkedin(token, image_path, owner_urn):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    register_payload = {
        "registerUploadRequest": {
            "owner": owner_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }

    r = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=headers,
        json=register_payload
    )

    upload_url = r.json()["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]

    asset = r.json()["value"]["asset"]

    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f.read())

    return asset


def create_linkedin_post(token, owner_urn, text, asset):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "media": asset
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    )

    return r.status_code

# ===============================
# UI: GENERATE CONTENT
# ===============================
query = st.text_input("Enter your topic")

if st.button("Generate"):
    if query.strip() == "":
        st.warning("Please enter a topic")
    else:
        with st.spinner("Generating AI content..."):
            text, image_path = ai_generate_pipeline(query)

        st.session_state.generated_text = text
        st.session_state.image_path = image_path
        st.session_state.has_content = True

# -------------------------------
# DISPLAY GENERATED CONTENT
# -------------------------------
if st.session_state.has_content:
    st.subheader("📝 Generated Text")
    st.write(st.session_state.generated_text)

    st.subheader("🖼️ Generated Image")
    st.image(
        Image.open(st.session_state.image_path),
        use_container_width=True
    )

# ===============================
# LINKEDIN AUTH
# ===============================
st.divider()
st.subheader("🔐 LinkedIn Authorization")

login_url = (
    f"{AUTH_URL}"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=openid%20profile%20w_member_social"
)

st.markdown(f"[Login with LinkedIn]({login_url})")


query_params = st.query_params

if "code" in query_params and not st.session_state.linkedin_logged_in:
    token = get_access_token(query_params["code"])
    if token:
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.success("LinkedIn authorization successful!")

# ===============================
# UPLOAD TO LINKEDIN
# ===============================
upload_disabled = not (
    st.session_state.has_content and
    st.session_state.linkedin_logged_in
)

if st.button("Upload to LinkedIn", disabled=upload_disabled):
    with st.spinner("Posting to LinkedIn..."):
        owner_urn = get_user_urn(st.session_state.linkedin_token)
        asset = upload_image_to_linkedin(
            st.session_state.linkedin_token,
            st.session_state.image_path,
            owner_urn
        )
        status = create_linkedin_post(
            st.session_state.linkedin_token,
            owner_urn,
            st.session_state.generated_text,
            asset
        )

    if status == 201:
        st.success("🎉 Posted successfully on LinkedIn!")
    else:
        st.error("Failed to post on LinkedIn")
