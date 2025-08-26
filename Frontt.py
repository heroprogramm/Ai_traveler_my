import streamlit as st
import requests
import time
import json

# Configuration
API_URL = "http://127.0.0.1:8000"  # FastAPI backend

# Page config
st.set_page_config(
    page_title="AI Traveling Agent", 
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Enhanced Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

.stApp {
    background: linear-gradient(45deg, #1a1c3a 0%, #2d4a87 25%, #4a90e2 50%, #87ceeb 75%, #ffd700 100%);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    font-family: 'Poppins', sans-serif;
}

@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    25% { background-position: 100% 50%; }
    50% { background-position: 50% 100%; }
    75% { background-position: 50% 0%; }
}

/* Hide Streamlit elements */
.stDeployButton { display: none; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }
footer { visibility: hidden; }

/* Main container */
.main-container {
    backdrop-filter: blur(20px);
    background: rgba(255, 255, 255, 0.1);
    border-radius: 25px;
    padding: 2rem;
    margin: 1rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Hero section */
.hero-section {
    text-align: center;
    padding: 3rem 1rem;
    position: relative;
    overflow: hidden;
}

.floating-icons {
    position: absolute;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
}

.floating-icon {
    position: absolute;
    font-size: 2rem;
    opacity: 0.3;
    animation: float 6s ease-in-out infinite;
}

.floating-icon:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
.floating-icon:nth-child(2) { top: 20%; right: 15%; animation-delay: 1s; }
.floating-icon:nth-child(3) { bottom: 30%; left: 20%; animation-delay: 2s; }
.floating-icon:nth-child(4) { bottom: 20%; right: 10%; animation-delay: 3s; }
.floating-icon:nth-child(5) { top: 50%; left: 5%; animation-delay: 4s; }
.floating-icon:nth-child(6) { top: 40%; right: 5%; animation-delay: 5s; }

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    33% { transform: translateY(-20px) rotate(5deg); }
    66% { transform: translateY(10px) rotate(-5deg); }
}

.hero-title {
    font-size: 4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffd700, #ff6b6b, #4ecdc4, #45b7d1);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientText 3s ease infinite, bounceIn 1s ease-out;
    text-shadow: 0 5px 15px rgba(255, 215, 0, 0.3);
    position: relative;
    z-index: 2;
}

@keyframes gradientText {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

@keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); opacity: 1; }
}

.hero-subtitle {
    font-size: 1.4rem;
    color: rgba(255, 255, 255, 0.9);
    margin-top: 1rem;
    font-weight: 300;
    animation: slideUp 1s ease-out 0.5s both;
    position: relative;
    z-index: 2;
}

@keyframes slideUp {
    0% { transform: translateY(30px); opacity: 0; }
    100% { transform: translateY(0); opacity: 1; }
}

/* Features grid */
.features-container {
    margin: 3rem 0;
    position: relative;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    padding: 1rem;
}

.feature-card {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    animation: slideInCard 0.8s ease-out forwards;
    opacity: 0;
    transform: translateY(30px);
}

.feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
}

.feature-card:hover::before {
    left: 100%;
}

.feature-card:nth-child(1) { animation-delay: 0.1s; }
.feature-card:nth-child(2) { animation-delay: 0.2s; }
.feature-card:nth-child(3) { animation-delay: 0.3s; }
.feature-card:nth-child(4) { animation-delay: 0.4s; }

@keyframes slideInCard {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.feature-card:hover {
    transform: translateY(-10px) scale(1.05);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.25);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.feature-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.8rem;
}

.feature-desc {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.95rem;
    line-height: 1.4;
}

/* Input section */
.input-section {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
    border: 1px solid rgba(255, 255, 255, 0.2);
    animation: slideUp 0.8s ease-out 0.6s both;
}

.input-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 1.5rem;
    text-align: center;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

/* Custom input styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.2) !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 15px !important;
    color: white !important;
    font-size: 1.1rem !important;
    padding: 1rem 1.5rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: #4ecdc4 !important;
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.3) !important;
    background: rgba(255, 255, 255, 0.25) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* Custom button */
.stButton > button {
    background: linear-gradient(135deg, #ff6b6b, #4ecdc4) !important;
    color: white !important;
    border: none !important;
    border-radius: 15px !important;
    padding: 0.8rem 2rem !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 10px 25px rgba(255, 107, 107, 0.3) !important;
    width: 100% !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 35px rgba(255, 107, 107, 0.4) !important;
    background: linear-gradient(135deg, #ff5252, #26a69a) !important;
}

/* Answer container */
.answer-container {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    animation: answerSlideIn 0.8s ease-out;
    position: relative;
    overflow: hidden;
}

.answer-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #ffd700);
    background-size: 400% 100%;
    animation: gradientMove 2s ease infinite;
}

@keyframes gradientMove {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

@keyframes answerSlideIn {
    0% { 
        opacity: 0; 
        transform: translateY(30px) scale(0.95); 
    }
    100% { 
        opacity: 1; 
        transform: translateY(0) scale(1); 
    }
}

.answer-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #4ecdc4;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.answer-text {
    color: rgba(255, 255, 255, 0.95);
    font-size: 1.1rem;
    line-height: 1.7;
    animation: typeWriter 0.5s ease-in-out;
}

@keyframes typeWriter {
    0% { width: 0; opacity: 0; }
    100% { width: 100%; opacity: 1; }
}

/* Loading spinner */
.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
}

.loading-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(255, 255, 255, 0.2);
    border-top: 4px solid #4ecdc4;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

.loading-text {
    color: rgba(255, 255, 255, 0.8);
    font-size: 1.1rem;
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Footer */
.footer {
    text-align: center;
    padding: 3rem 1rem 1rem;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.95rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: 3rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .hero-title { font-size: 2.5rem; }
    .hero-subtitle { font-size: 1.1rem; }
    .features-grid { grid-template-columns: 1fr; gap: 1rem; }
    .feature-card { padding: 1.5rem; }
    .main-container { margin: 0.5rem; padding: 1rem; }
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar-thumb {
    background: rgba(78, 205, 196, 0.5);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(78, 205, 196, 0.7);
}
</style>
""", unsafe_allow_html=True)

# --- Main Container ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# --- Hero Section ---
st.markdown("""
<div class="hero-section">
    <div class="floating-icons">
        <div class="floating-icon">✈️</div>
        <div class="floating-icon">🏖️</div>
        <div class="floating-icon">🗺️</div>
        <div class="floating-icon">🏨</div>
        <div class="floating-icon">🍽️</div>
        <div class="floating-icon">📸</div>
    </div>
    <h1 class="hero-title">🌍 AI Traveling Agent</h1>
    <p class="hero-subtitle">Your intelligent companion for unforgettable journeys ✨</p>
</div>
""", unsafe_allow_html=True)

# --- Features Section ---
st.markdown("""
<div class="features-container">
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <div class="feature-title">Smart Itineraries</div>
            <div class="feature-desc">Personalized travel plans crafted just for you with insider recommendations</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <div class="feature-title">Budget Optimizer</div>
            <div class="feature-desc">Discover amazing deals and budget-friendly travel hacks to save money</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🏨</div>
            <div class="feature-title">Perfect Stays</div>
            <div class="feature-desc">Find unique accommodations that match your style and preferences</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🍽️</div>
            <div class="feature-title">Culinary Adventures</div>
            <div class="feature-desc">Taste authentic local cuisine and hidden foodie gems</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Input Section ---
st.markdown("""
<div class="input-section">
    <h2 class="input-title">💭 What's your travel dream?</h2>
</div>
""", unsafe_allow_html=True)

# Enhanced input with better placeholder
question = st.text_input(
    "✍️ Ask your travel question:",
    placeholder="Where should I go for a romantic getaway in Europe? 🌹",
    key="travel_input",
    help="Ask about destinations, budgets, activities, food, or anything travel-related!"
)

# Create two columns for the button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ask_button = st.button("🚀 Plan My Adventure", use_container_width=True)

# --- Handle Question with Enhanced UX ---
if ask_button and question.strip():
    # Show loading animation
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">🤖 Your AI travel expert is thinking...</div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Make API call to FastAPI backend
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            answer_text = data.get("answer", "No answer returned.")
        else:
            answer_text = f"⚠️ API returned status {response.status_code}. Please try again later."
            
    except requests.exceptions.ConnectionError:
        # Fallback response when API is not available
        answer_text = f"""🌟 Thanks for asking: "{question}"
        
        I'd love to help you with your travel plans! However, I'm currently unable to connect to the travel database.
        
        For now, here are some general tips:
        • Research visa requirements for your destination
        • Check the weather and pack accordingly  
        • Book accommodations in advance for popular destinations
        • Try local cuisine and explore beyond tourist areas
        • Keep copies of important documents
        
        Please make sure your FastAPI backend is running on {API_URL} for personalized recommendations!"""
        
    except Exception as e:
        answer_text = f"❌ An unexpected error occurred. Please try again later."
    
    # Clear loading and show answer
    loading_placeholder.empty()
    
    st.markdown(f"""
    <div class="answer-container">
        <div class="answer-title">🎯 Your Travel Insights</div>
        <div class="answer-text">{answer_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add follow-up suggestions
    st.markdown("""
    <div style="margin-top: 1rem; text-align: center;">
        <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">
            💡 Want more details? Ask about specific cities, activities, or travel dates!
        </p>
    </div>
    """, unsafe_allow_html=True)

elif ask_button and not question.strip():
    st.markdown("""
    <div style="background: rgba(255, 193, 7, 0.2); border: 1px solid rgba(255, 193, 7, 0.5); 
                border-radius: 15px; padding: 1rem; margin: 1rem 0; text-align: center;">
        <span style="color: #ffc107; font-size: 1.1rem;">⚠️ Please share your travel question first!</span>
    </div>
    """, unsafe_allow_html=True)

# --- Quick Suggestions ---
if not question:
    st.markdown("""
    <div style="margin: 2rem 0; text-align: center;">
        <p style="color: rgba(255,255,255,0.8); margin-bottom: 1rem; font-size: 1.1rem;">
            🌟 Need inspiration? Try these popular questions:
        </p>
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;">
            <span style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; color: rgba(255,255,255,0.8);">
                "Best time to visit Japan?"
            </span>
            <span style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; color: rgba(255,255,255,0.8);">
                "Budget backpacking Europe itinerary"
            </span>
            <span style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; color: rgba(255,255,255,0.8);">
                "Hidden gems in Southeast Asia"
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div class="footer">
    <p>🌍 Made with ❤️ for adventurous souls | Powered by AI magic ✨</p>
    <p style="margin-top: 0.5rem; font-size: 0.8rem;">
        Ready to explore the world? Your next adventure starts here! 🚀
    </p>
</div>
""", unsafe_allow_html=True)

# Close main container
st.markdown('</div>', unsafe_allow_html=True)