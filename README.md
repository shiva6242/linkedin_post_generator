# 🤖 AI LinkedIn Auto Poster

An AI-powered web application that generates professional LinkedIn posts (text + image) and publishes them directly to LinkedIn using OAuth authentication.

Built using **Streamlit**, **Google Gemini**, **Hugging Face**, and **LinkedIn APIs**.

---

## LINK : https://linkedinpostgenerator1234.streamlit.app/

## 🚀 Features

- ✨ Generate professional LinkedIn post text using **Google Gemini**
- 🖼️ Generate AI images using **Hugging Face**
- 🔐 Secure LinkedIn login using **OAuth 2.0**
- 📤 Upload posts (text + image) directly to LinkedIn
- ☁️ Deployed on **Streamlit Cloud**
- 🔒 API keys managed securely using environment variables

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit  
- **AI Text Generation**: Google Gemini (LangChain)  
- **AI Image Generation**: Hugging Face (FLUX model)  
- **Authentication**: LinkedIn OAuth 2.0  
- **Deployment**: Streamlit Cloud  

---

## 📂 Project Structure

linkedin_post_application/
│
├── app.py # Main Streamlit application
├── requirements.txt # Python dependencies
├── .gitignore # Ignore secrets & cache files
├── README.md # Project documentation


---

## 🔑 Environment Variables

The following variables **must NOT be hardcoded**.

### Local Development (`.env` file)

```env
GEMINI_API_KEY=your_gemini_api_key
HF_API_KEY=your_huggingface_api_key
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret


### To Run Locally ##
pip install -r requirements.txt
streamlit run app.py
