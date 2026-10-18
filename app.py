import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="EcoGuard", page_icon="🌍", layout="wide")

# ---------------------------
# EcoGuard: beginner prototype
# ---------------------------
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #f4fbf3 0%, #ffffff 55%); }
h1, h2, h3 { color: #17633b; }
div[data-testid="stMetric"] { background: #eef8ed; padding: 14px; border-radius: 12px; }
/* EcoGuard Modern Green Theme */
.stApp {
    background: linear-gradient(135deg, #f0fdf4, #ecfeff, #ffffff);
}

h1, h2, h3 {
    color: #166534 !important;
    font-weight: 800 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #16a34a, #059669);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    font-weight: 700;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #15803d, #047857);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(22, 163, 74, 0.25);
}

[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #dcfce7;
    box-shadow: 0 4px 12px rgba(22, 101, 52, 0.08);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #dcfce7, #f0fdf4);
}

.stTextInput input,
.stTextArea textarea {
    border-radius: 10px;
}

hr {
    border-color: #bbf7d0;
}
</style>
""", unsafe_allow_html=True)

st.title("🌍 EcoGuard")
st.caption("Small actions. A greener future.")
st.write("Learn about climate change, take eco-friendly actions, and track your progress.")

if "points" not in st.session_state:
    st.session_state.points = 0
if "completed_challenges" not in st.session_state:
    st.session_state.completed_challenges = set()
if "trees" not in st.session_state:
    st.session_state.trees = 0
if "reports" not in st.session_state:
    st.session_state.reports = []
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_awarded" not in st.session_state:
    st.session_state.quiz_awarded = False

challenges = {
    "Switch off unused lights": ("Save electricity when a room is empty.", 10),
    "Carry a reusable bottle": ("Avoid a single-use plastic bottle today.", 10),
    "Sort recyclable waste": ("Separate clean paper, metal, glass, or accepted plastics.", 15),
    "Walk or cycle a short safe trip": ("Choose active travel when practical and safe.", 15),
    "Care for a plant": ("Check whether a plant needs water or care.", 10),
    "Save water": ("Turn off the tap while brushing your teeth.", 10),
}

pages = [
    "🏠 Dashboard", "🌱 Eco Challenges", "🌡️ Carbon Calculator",
    "🧠 Climate Quiz", "🌳 Tree Tracker", "💬 Eco Chatbot",
    "📣 Pollution Report", "🌦️ Weather & Climate"
]
page = st.sidebar.radio("Navigate", pages)
st.sidebar.metric("Your EcoPoints", st.session_state.points)
st.sidebar.caption("Prototype points are for learning, not a verified environmental measurement.")

if page == "🏠 Dashboard":
    st.subheader("Your environmental dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("EcoPoints", st.session_state.points)
    c2.metric("Challenges done", len(st.session_state.completed_challenges))
    c3.metric("Trees recorded", st.session_state.trees)
    st.info("Start with one small action. Repeating good habits can help reduce environmental impact.")
    st.subheader("Explore EcoGuard")
    st.markdown("""
    - **Eco Challenges:** complete actions and earn points.
    - **Carbon Calculator:** estimate emissions from a few everyday activities.
    - **Climate Quiz:** test your knowledge.
    - **Tree Tracker:** record planting activities.
    - **Eco Chatbot:** get basic environmental tips.
    - **Pollution Report:** create a local demo report.
    - **Weather & Climate:** look up current weather for a city.
    """)
    st.warning("Your current progress is stored only for this app session. It may reset when the session ends.")

elif page == "🌱 Eco Challenges":
    st.subheader("Today's eco challenges")
    st.write("Complete actions you really did. Each challenge can earn points once per session.")
    for name, (description, points) in challenges.items():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{name}**  \n{description}  \n`+{points} points`")
        with col2:
            if name in st.session_state.completed_challenges:
                st.success("Completed")
            elif st.button("Complete", key="challenge_" + name):
                st.session_state.completed_challenges.add(name)
                st.session_state.points += points
                st.rerun()
        st.divider()

elif page == "🌡️ Carbon Calculator":
    st.subheader("Everyday carbon footprint estimator")
    st.write("This is a simplified educational estimate, not an official carbon audit.")
    km = st.number_input("Car or taxi travel (km per week)", min_value=0.0, max_value=5000.0, value=20.0, step=5.0)
    kwh = st.number_input("Household electricity use (kWh per week)", min_value=0.0, max_value=10000.0, value=25.0, step=5.0)
    meat_meals = st.number_input("Meat-heavy meals per week", min_value=0, max_value=50, value=3, step=1)
    st.caption("For this demo only: car/taxi = 0.20 kg CO₂e/km; electricity = 0.70 kg CO₂e/kWh; meat-heavy meal = 2.0 kg CO₂e/meal. Actual values vary by vehicle, electricity grid, food and location.")
    if st.button("Estimate my weekly footprint", type="primary"):
        travel = km * 0.20
        electricity = kwh * 0.70
        food = meat_meals * 2.0
        total = travel + electricity + food
        st.session_state.last_footprint = total
        st.metric("Estimated weekly total", f"{total:.1f} kg CO₂e")
        st.write(f"Travel: **{travel:.1f} kg** · Electricity: **{electricity:.1f} kg** · Food estimate: **{food:.1f} kg CO₂e**")
        st.info("Try changing one input to see how different habits affect this simplified estimate. This is not a medical, scientific, or official personal rating.")
    st.markdown("**Ideas to reduce impact:** use public transport when practical, avoid wasting electricity, reduce food waste, and choose reusable items.")

elif page == "🧠 Climate Quiz":
    st.subheader("Climate knowledge quiz")
    questions = [
        ("Which gas is a major contributor to human-caused global warming?", ["Oxygen", "Carbon dioxide", "Helium", "Neon"], 1,
         "Carbon dioxide traps heat in the atmosphere and is released by burning fossil fuels and other activities."),
        ("Which source produces electricity without directly burning fossil fuels during operation?", ["Coal power", "Diesel generator", "Solar panels", "Petrol engine"], 2,
         "Solar panels convert sunlight into electricity without combustion during operation."),
        ("What is one useful way to reduce single-use plastic waste?", ["Use a refillable bottle", "Throw plastic into rivers", "Burn plastic outdoors", "Use more disposable bags"], 0,
         "A refillable bottle can replace many single-use bottles."),
        ("What does biodiversity mean?", ["Only the number of trees", "The variety of living things", "Daily temperature", "The amount of traffic"], 1,
         "Biodiversity means the variety of life, including plants, animals and microorganisms."),
        ("Which action can help save household electricity?", ["Leave every light on", "Keep unused devices running", "Switch off unused lights", "Open the fridge for a long time"], 2,
         "Turning off unnecessary lights reduces electricity use.")
    ]
    with st.form("climate_quiz"):
        answers = {}
        for i, (q, opts, correct, explanation) in enumerate(questions):
            answers[i] = st.radio(f"{i+1}. {q}", opts, key=f"quiz_{i}")
        submitted = st.form_submit_button("Check answers")
    if submitted:
        score = sum(1 for i, (q, opts, correct, explanation) in enumerate(questions) if answers[i] == opts[correct])
        st.session_state.quiz_answers = answers
        st.session_state.quiz_score = score
        if not st.session_state.quiz_awarded:
            earned = score * 5
            st.session_state.points += earned
            st.session_state.quiz_awarded = True
            st.success(f"You scored {score}/{len(questions)} and earned {earned} points!")
        else:
            st.info(f"You scored {score}/{len(questions)}. Quiz points have already been awarded in this session.")
        for i, (q, opts, correct, explanation) in enumerate(questions):
            st.markdown(f"**Q{i+1}:** {'✅' if answers[i] == opts[correct] else '❌'} {explanation}")
    if st.session_state.quiz_awarded:
        st.caption("To avoid repeatedly collecting points, this prototype awards quiz points once per session.")

elif page == "🌳 Tree Tracker":
    st.subheader("Tree planting and care tracker")
    st.write("Record trees you have planted or helped care for. Only count real activities.")
    amount = st.number_input("How many trees are you recording?", min_value=1, max_value=1000, value=1, step=1)
    activity = st.selectbox("Activity", ["Planted a tree", "Helped care for existing trees", "Joined a tree-planting event"])
    if st.button("Add tree activity", type="primary"):
        st.session_state.trees += int(amount)
        st.session_state.points += min(int(amount) * 5, 50)
        st.success(f"Recorded {amount} tree(s) for: {activity}. Points added (maximum 50 per entry).")
    st.metric("Trees / tree activities recorded", st.session_state.trees)
    st.caption("This prototype counts recorded activities, not independently verified surviving trees. Tree planting should use suitable native species and appropriate local guidance.")

elif page == "💬 Eco Chatbot":
    st.subheader("EcoGuide AI 🌿")
    st.write("Ask Gemini AI about climate change, biodiversity, recycling, water, renewable energy, or everyday eco-friendly actions.")
    st.info("Please don't enter passwords, API keys, your home address, or other private information.")
    prompt = st.text_area("Ask EcoGuide AI", placeholder="Example: Explain climate change in simple words.", max_chars=1500)
    if st.button("Ask EcoGuide AI", type="primary"):
        if not prompt.strip():
            st.warning("Type a question first.")
        else:
            try:
                api_key = st.secrets.get("GEMINI_API_KEY", "")
                if not api_key:
                    st.error("Gemini API key is missing. Add GEMINI_API_KEY in your Streamlit app's Settings → Secrets, then save.")
                else:
                    with st.spinner("EcoGuide AI is thinking..."):
                        response = requests.post(
                            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
                            params={"key": api_key},
                            headers={"Content-Type": "application/json"},
                            json={
                                "system_instruction": {
                                    "parts": [{"text": "You are EcoGuide, a friendly environmental education assistant for a school project. Give accurate, age-appropriate, practical answers in clear simple English. Focus on climate, nature, pollution, recycling, water, energy, and sustainability. Do not claim to contact authorities or perform actions. If unsure, say so. Keep answers concise."}]
                                },
                                "contents": [{"role": "user", "parts": [{"text": prompt.strip()}]}],
                                "generationConfig": {"temperature": 0.6, "maxOutputTokens": 600}
                            },
                            timeout=30
                        )
                    if response.ok:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
                        answer = "\n".join(part.get("text", "") for part in parts if part.get("text"))
                        if answer.strip():
                            st.markdown(answer)
                        else:
                            st.warning("Gemini returned no text this time. Please try asking in a different way.")
                    elif response.status_code == 429:
                        st.warning("The Gemini free-tier usage limit may have been reached. Wait a little and try again.")
                    elif response.status_code in (401, 403):
                        st.error("Gemini did not accept this API key or the project is not allowed to use the API. Check your key in Streamlit Secrets and confirm Gemini API access is enabled.")
                    else:
                        st.error(f"Gemini request failed (HTTP {response.status_code}). Check the API key, model availability, and Google AI Studio project settings.")
            except requests.Timeout:
                st.error("Gemini took too long to respond. Please try again.")
            except requests.RequestException:
                st.error("Could not connect to Gemini. Check the app's internet connection and try again.")
            except Exception:
                st.error("Something went wrong while contacting Gemini. Check Streamlit app logs for details; never share your API key.")
    st.caption("Gemini API availability and free-tier limits can vary. EcoGuard is an educational prototype; verify important environmental or safety advice with trusted sources.")

elif page == "📣 Pollution Report":
    st.subheader("Community pollution report")
    st.write("This is a demo form. Reports are kept only in this current session and are not sent to authorities.")
    with st.form("pollution_report"):
        category = st.selectbox("Type of concern", ["Litter / plastic waste", "Smoke / air pollution", "Water pollution", "Noise pollution", "Other"])
        area = st.text_input("General area (do not enter your home address)", placeholder="Example: near the public park")
        details = st.text_area("What did you observe?", placeholder="Describe what you saw without confronting anyone.")
        urgent = st.checkbox("This may be an immediate safety or health concern")
        submitted = st.form_submit_button("Save demo report")
    if submitted:
        if not area.strip() or not details.strip():
            st.error("Please add a general area and a short description.")
        else:
            report = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "category": category,
                "area": area.strip(),
                "details": details.strip(),
                "urgent": urgent,
            }
            st.session_state.reports.append(report)
            st.success("Demo report saved in this session. It has not been sent to anyone.")
            if urgent:
                st.warning("Keep a safe distance and tell a trusted adult or the appropriate local emergency/service authority. Do not approach hazardous waste or confront anyone.")
    if st.session_state.reports:
        st.subheader("Reports created in this session")
        for i, report in enumerate(reversed(st.session_state.reports), start=1):
            st.markdown(f"**Report {i} — {report['category']}** · {report['time']}")
            st.write(f"Area: {report['area']}")
            st.write(report["details"])
            st.divider()

elif page == "🌦️ Weather & Climate":
    st.subheader("Current weather lookup")
    st.write("Enter a city name to look up current conditions. Weather is not the same as climate: weather is short-term; climate describes long-term patterns.")
    city = st.text_input("City", value="Chennai")
    if st.button("Get current weather", type="primary"):
        try:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=10
            )
            geo.raise_for_status()
            places = geo.json().get("results", [])
            if not places:
                st.error("City not found. Try a larger nearby city or check the spelling.")
            else:
                place = places[0]
                weather = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
                        "timezone": "auto"
                    },
                    timeout=10
                )
                weather.raise_for_status()
                current = weather.json().get("current", {})
                st.success(f"Weather for {place['name']}, {place.get('country', '')}")
                a, b, c = st.columns(3)
                a.metric("Temperature", f"{current.get('temperature_2m', 'N/A')} °C")
                b.metric("Feels like", f"{current.get('apparent_temperature', 'N/A')} °C")
                c.metric("Wind speed", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                st.write(f"Relative humidity: **{current.get('relative_humidity_2m', 'N/A')}%**")
                st.caption("Weather data supplied by Open-Meteo. Conditions can change; check official local warnings for safety-critical decisions.")
        except requests.RequestException:
            st.error("Could not connect to the weather service. Check your internet connection and try again.")
    st.subheader("Weather vs climate")
    st.markdown("""
    - **Weather:** conditions over minutes, hours or days, such as today's rain or temperature.
    - **Climate:** patterns and averages measured over many years.
    - A single hot day does not prove climate change; scientists examine long-term observations and many kinds of evidence.
    """)
    st.caption("Weather service: Open-Meteo (internet connection required).")

st.divider()
st.caption("EcoGuard prototype • Educational use • Verify local environmental and emergency guidance with official sources.")
