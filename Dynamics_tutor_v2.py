import streamlit as st
import google.generativeai as genai

st.title("🔑 API Key Diagnostic Tool")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    st.write("### Checking Available Models...")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    if available_models:
        st.success(f"Successfully connected! Your key can see {len(available_models)} models.")
        st.write("Available Model Strings (use one of these in logic.py):")
        st.code(available_models)
        
        # Test a simple generation
        st.write("### Testing Generation...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, are you active?")
        st.info(f"Test Response: {response.text}")
    else:
        st.warning("Connected, but no models found. Check your API project permissions.")

except Exception as e:
    st.error(f"Diagnostic Failed: {e}")
    st.write("This usually means the API Key is invalid or the 'Generative Language API' is not enabled in Google Cloud Console.")
