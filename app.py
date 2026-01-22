# ================================
# app.py – AI LinkedIn Auto Poster (Styled + Correct Flow)
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
st.set_page_config(page_title="AI LinkedIn Auto Poster", layout="centered")

# -------------------------------
# CUSTOM UI (UNCHANGED)
# -------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #007182 20%, #001699 100%);
        color: white;
    }
    h1, h2, h3 {
        color: #FFD700 !important;
        font-weight: 800 !important;
    }
    .stButton>button {
        background-color: #FF5733 !important;
        color: white !important;
        border-radius: 8px !important;
        font-size: 1.1em !important;
        font-weight: bold !important;
    }
    .stButton>button:hover {
        background-color: #FFC300 !important;
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    a[href*="linkedin.com/oauth"] {
        color: #32CD32 !important;
        font-size: 1.2em;
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
if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False

if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

if "has_content" not in st.session_state:
    st.session_state.has_content = False

# ======================================================
# STEP 1️⃣ LINKEDIN AUTH (FIRST)
# ======================================================
st.divider()
st.subheader("🔐 LinkedIn Authorization")

login_url = (
    f"{AUTH_URL}"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=openid%20profile%20w_member_social"
)

if not st.session_state.linkedin_logged_in:
    st.markdown(f"[Login with LinkedIn]({login_url})")

query_params = st.query_params

if "code" in query_params and not st.session_state.linkedin_logged_in:
    payload = {
        "grant_type": "authorization_code",
        "code": query_params["code"],
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=payload)
    if r.status_code == 200:
        st.session_state.linkedin_token = r.json()["access_token"]
        st.session_state.linkedin_logged_in = True
        st.success("LinkedIn authorization successful!")

# ======================================================
# STEP 2️⃣ GENERATE CONTENT (ONLY AFTER LOGIN)
# ======================================================
def generate_text(topic):
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.7
    )
    prompt = PromptTemplate(
        input_variables=["topic"],
        template="Write a professional LinkedIn post (100–120 words) about {topic}."
    )
    return llm.invoke(prompt.format(topic=topic)).content


def generate_image(prompt, output_path="generated_image.png"):
    client = InferenceClient(
        model="black-forest-labs/FLUX.1-schnell",
        token=HF_API_KEY
    )
    image = client.text_to_image(prompt)
    image.save(output_path)
    return output_path


def ai_generate_pipeline(query):
    text = generate_text(query)
    image_path = generate_image(f"Professional illustration representing {query}")
    return text, image_path


if st.session_state.linkedin_logged_in:
    st.divider()
    st.subheader("✍️ Generate LinkedIn Post")

    query = st.text_input("Enter your topic")

    if st.button("Generate"):
        with st.spinner("Generating AI content..."):
            text, image_path = ai_generate_pipeline(query)

        st.session_state.generated_text = text
        st.session_state.image_path = image_path
        st.session_state.has_content = True
else:
    st.info("Please login with LinkedIn to generate content.")

# ======================================================
# STEP 3️⃣ PREVIEW GENERATED CONTENT
# ======================================================
if st.session_state.has_content:
    st.subheader("📝 Generated Text")
    st.write(st.session_state.generated_text)

    st.subheader("🖼️ Generated Image")
    st.image(
        Image.open(st.session_state.image_path),
        use_container_width=True
    )

# ======================================================
# STEP 4️⃣ UPLOAD TO LINKEDIN (FINAL)
# ======================================================
def get_user_urn(token):
    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    )
    return f"urn:li:person:{r.json()['sub']}"


def upload_image(token, image_path, owner_urn):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
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


def create_post(token, owner_urn, text, asset):
    payload = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{"status": "READY", "media": asset}]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    return requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload
    ).status_code


if st.session_state.has_content and st.session_state.linkedin_logged_in:
    if st.button("Upload to LinkedIn"):
        with st.spinner("Posting to LinkedIn..."):
            owner_urn = get_user_urn(st.session_state.linkedin_token)
            asset = upload_image(
                st.session_state.linkedin_token,
                st.session_state.image_path,
                owner_urn
            )
            status = create_post(
                st.session_state.linkedin_token,
                owner_urn,
                st.session_state.generated_text,
                asset
            )

        if status == 201:
            st.success("🎉 Posted successfully on LinkedIn!")
        else:
            st.error("Failed to post on LinkedIn")
