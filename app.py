import streamlit as st
import requests
from datetime import datetime
import random

st.set_page_config(page_title="EcoGuard", page_icon="🌍", layout="wide")

# ---------------------------
# EcoGuard: beginner prototype
# ---------------------------
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #f4fbf3 0%, #ffffff 55%); }
h1, h2, h3 { color: #17633b; }
div[data-testid="stMetric"] { background: #eef8ed; padding: 14px; border-radius: 12px; }
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
if "quiz_round" not in st.session_state:
    st.session_state.quiz_round = 0
if "active_username" not in st.session_state:
    st.session_state.active_username = ""
if "supabase_status" not in st.session_state:
    st.session_state.supabase_status = ""

def supabase_configured():
    """Use a server-side Supabase secret key stored only in Streamlit Secrets."""
    return bool(st.secrets.get("SUPABASE_URL", "").strip() and
                st.secrets.get("SUPABASE_SECRET_KEY", "").strip())

def supabase_headers():
    secret_key = st.secrets.get("SUPABASE_SECRET_KEY", "").strip()
    return {
        "apikey": secret_key,
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }

def load_progress(username):
    """Load one username's saved progress from Supabase."""
    if not supabase_configured():
        st.session_state.supabase_status = (
            "Supabase is not configured for saving yet. Add SUPABASE_URL and "
            "SUPABASE_SECRET_KEY in Streamlit Secrets."
        )
        return False
    base_url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    try:
        response = requests.get(
            f"{base_url}/rest/v1/ecoguard_progress",
            headers=supabase_headers(),
            params={"select": "user_id,eco_points,quiz_score,trees_planted,completed_challenges",
                    "user_id": f"eq.{username}", "limit": "1"},
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json()
        row = rows[0] if rows else None
        st.session_state.points = int(row.get("eco_points", 0)) if row else 0
        st.session_state.quiz_score = int(row.get("quiz_score", 0)) if row else 0
        st.session_state.trees = int(row.get("trees_planted", 0)) if row else 0
        completed = row.get("completed_challenges", []) if row else []
        st.session_state.completed_challenges = set(completed if isinstance(completed, list) else [])
        st.session_state.quiz_awarded = bool(st.session_state.quiz_score)
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.supabase_status = "Progress loaded from Supabase."
        return True
    except (requests.RequestException, ValueError, TypeError, KeyError):
        st.session_state.supabase_status = (
            "Could not load saved progress. Check the Supabase URL, server-side "
            "secret key, table name, and database permissions."
        )
        return False

def save_progress():
    """Save the current user's progress to Supabase."""
    username = st.session_state.get("active_username", "")
    if not username or not supabase_configured():
        return
    base_url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    payload = {
        "user_id": username,
        "eco_points": min(max(int(st.session_state.points), 0), 100),
        "quiz_score": int(st.session_state.get("quiz_score", 0)),
        "trees_planted": int(st.session_state.trees),
        "completed_challenges": sorted(st.session_state.completed_challenges),
        "updated_at": datetime.now().astimezone().isoformat(),
    }
    try:
        response = requests.post(
            f"{base_url}/rest/v1/ecoguard_progress",
            headers={**supabase_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            params={"on_conflict": "user_id"},
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        st.session_state.supabase_status = "Progress saved to Supabase."
except requests.RequestException as e:
    details = ""
    if e.response is not None:
        details = f" | Response: {e.response.text[:500]}"
    st.session_state.supabase_status = (
        f"Progress could not be saved: {e}{details}"
    )

# Username-based profiles are convenient, but a username alone is not authentication:
# another person could enter the same username. Do not store sensitive information here.
if not st.session_state.active_username:
    st.subheader("👤 Open your EcoGuard profile")
    st.write("Enter your username to load your saved EcoPoints, quiz score, challenges, and tree records.")
    with st.form("profile_login"):
        entered_username = st.text_input(
            "Username", max_chars=32, placeholder="Example: Amuthan05"
        )
        open_profile = st.form_submit_button("Open my profile", type="primary")
    st.info("Username-only profiles are not private accounts. Someone else could enter the same username. Use a nickname, not personal or sensitive information.")
    if open_profile:
        clean_username = entered_username.strip()
        if len(clean_username) < 3 or not all(ch.isalnum() or ch in "_-" for ch in clean_username):
            st.error("Choose a username with 3–32 letters, numbers, underscores, or hyphens.")
        else:
            st.session_state.active_username = clean_username
            st.session_state.points = 0
            st.session_state.quiz_score = 0
            st.session_state.trees = 0
            st.session_state.completed_challenges = set()
            st.session_state.quiz_awarded = False
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            load_progress(clean_username)
            st.rerun()
    if not supabase_configured():
        st.warning("Saving between visits is not ready yet. In Streamlit Secrets, add SUPABASE_URL and SUPABASE_SECRET_KEY. Keep the secret key private and never put it in GitHub.")
    st.stop()

st.sidebar.success(f"Profile: {st.session_state.active_username}")
if st.sidebar.button("Log out / switch username"):
    st.session_state.active_username = ""
    st.rerun()
if st.session_state.get("supabase_status"):
    st.sidebar.caption(st.session_state.supabase_status)

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
    "📣 Pollution Report", "🌦️ Weather & Climate", "🌫️ Air Quality index(AQI)"
]
page = st.sidebar.radio("Navigate", pages)
eco_score = min(max(int(st.session_state.points), 0), 100)
st.sidebar.metric("Your EcoPoints", f"{eco_score}/100")
st.sidebar.caption("Displayed EcoPoints are capped at 100. Points are for learning, not a verified environmental measurement.")

if page == "🏠 Dashboard":
    st.subheader("Your environmental dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("EcoPoints", f"{eco_score}/100")
    c2.metric("Challenges done", len(st.session_state.completed_challenges))
    c3.metric("Trees recorded", st.session_state.trees)
    st.progress(eco_score / 100, text=f"EcoPoints: {eco_score} / 100")
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
    - **Air Quality (AQI):** check live air quality and pollutant readings where available.
    """)
    if not supabase_configured():
        st.warning("Supabase saving is not configured, so progress may reset when this session ends.")
    else:
        st.success(f"Signed in as **{st.session_state.active_username}**. Progress is saved to your Supabase profile.")

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
                earned = min(points, max(0, 100 - int(st.session_state.points)))
                st.session_state.points = min(100, int(st.session_state.points) + earned)
                if earned > 0:
                    st.success(f"Completed! You earned {earned} EcoPoints.")
                else:
                    st.info("Challenge completed! Your EcoPoints are already at 100/100.")
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
    question_pool = [
        ("Which gas is a major contributor to human-caused global warming?", ["Oxygen", "Carbon dioxide", "Helium", "Neon"], 1,
         "Carbon dioxide traps heat in the atmosphere and is released by burning fossil fuels and other activities."),
        ("Which source produces electricity without directly burning fossil fuels during operation?", ["Coal power", "Diesel generator", "Solar panels", "Petrol engine"], 2,
         "Solar panels convert sunlight into electricity without combustion during operation."),
        ("What is one useful way to reduce single-use plastic waste?", ["Use a refillable bottle", "Throw plastic into rivers", "Burn plastic outdoors", "Use more disposable bags"], 0,
         "A refillable bottle can replace many single-use bottles."),
        ("What does biodiversity mean?", ["Only the number of trees", "The variety of living things", "Daily temperature", "The amount of traffic"], 1,
         "Biodiversity means the variety of life, including plants, animals and microorganisms."),
        ("Which action can help save household electricity?", ["Leave every light on", "Keep unused devices running", "Switch off unused lights", "Open the fridge for a long time"], 2,
         "Turning off unnecessary lights reduces electricity use."),
        ("Which gas is released when fossil fuels are burned?", ["Carbon dioxide", "Oxygen", "Helium", "Neon"], 0,
         "Burning coal, oil and gas releases carbon dioxide, a heat-trapping greenhouse gas."),
        ("Which practice helps conserve water at home?", ["Leave taps running", "Fix leaking taps", "Wash one item at a time", "Water pavement"], 1,
         "Repairing leaks prevents clean water from being wasted."),
        ("What is composting?", ["Burning household waste", "Turning organic scraps into soil material", "Putting all waste in a river", "Making plastic bottles"], 1,
         "Composting lets food and garden scraps break down into useful organic material."),
        ("Which transport choice usually creates fewer emissions per passenger?", ["A bus", "A solo car trip", "A short flight", "An idling car"], 0,
         "Shared transport can reduce emissions per passenger compared with individual car trips."),
        ("What does renewable energy come from?", ["Sources replenished naturally", "Only coal", "Plastic waste alone", "A limited fuel deposit"], 0,
         "Sunlight, wind and flowing water are examples of renewable energy sources."),
        ("Why are wetlands valuable?", ["They support wildlife and store water", "They increase plastic waste", "They prevent all rain", "They contain no plants"], 0,
         "Wetlands provide habitat, help filter water and can reduce flooding."),
        ("What is one good way to reduce food waste?", ["Plan meals and use leftovers", "Buy more than needed", "Throw away unopened food", "Leave food outdoors"], 0,
         "Planning meals and using leftovers can prevent edible food from being discarded."),
        ("Which item is generally reusable?", ["A refillable cup", "A disposable straw", "A single-use wrapper", "A one-time plastic bag"], 0,
         "A refillable cup can be used repeatedly instead of disposable cups."),
        ("What does the ozone layer help protect life from?", ["Some harmful ultraviolet radiation", "All earthquakes", "Ocean tides", "Wind"], 0,
         "Ozone high in the atmosphere absorbs much of the Sun's harmful ultraviolet radiation."),
        ("Which is an example of adapting to climate impacts?", ["Planning for heatwaves", "Using more disposable items", "Ignoring flood risk", "Wasting electricity"], 0,
         "Heat action plans help communities prepare for and reduce risks from extreme heat."),
        ("What is biodiversity?", ["The variety of life", "The daily weather", "One type of crop", "The number of cars"], 0,
         "Biodiversity includes the variety of genes, species and ecosystems."),
        ("How can shade trees help a neighborhood?", ["Cool shaded areas", "Increase traffic", "Make drinking water", "Remove all pollution"], 0,
         "Tree shade can cool nearby surfaces and make outdoor spaces more comfortable."),
        ("Which action is safest around unknown pollution?", ["Keep a safe distance and report it", "Touch or smell it", "Burn it", "Move it by hand"], 0,
         "Avoid contact with unknown substances and tell the appropriate local authority or a trusted adult."),
        ("What does recycling usually require?", ["Following local sorting rules", "Mixing hazardous waste with food", "Putting everything in one bin", "Rinsing waste into drains"], 0,
         "Accepted materials and sorting rules vary, so follow your local recycling guidance."),
        ("Which surface usually absorbs more heat in direct sunlight?", ["Dark asphalt", "A shaded pond", "Fresh snow", "A light-colored roof"], 0,
         "Dark paved surfaces absorb sunlight and can become much hotter than lighter surfaces."),
        ("What is a local climate?", ["Long-term weather patterns in a place", "Today's temperature only", "One rain shower", "This week's wind"], 0,
         "Climate describes patterns and averages over many years."),
        ("Which household habit can reduce standby electricity use?", ["Turn off devices when not needed", "Leave every charger plugged in", "Keep screens on overnight", "Open the refrigerator often"], 0,
         "Switching off devices when they are not needed can reduce some standby electricity use."),
        ("Why should native plants be considered in gardens?", ["They can support local wildlife", "They always need more water", "They remove the need for all care", "They are harmful everywhere"], 0,
         "Plants native to an area can provide food and habitat for local wildlife, depending on the species and site."),
        ("Which source is a direct observation of climate?", ["Many years of temperature records", "One unusually cold morning", "A single cloudy afternoon", "One windy day"], 0,
         "Long-term records help scientists identify climate patterns beyond day-to-day variation.")
    ]
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = random.sample(question_pool, 10)
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
    if st.button("🔄 Reset quiz and shuffle questions", key="reset_quiz"):
        st.session_state.quiz_round += 1
        st.session_state.quiz_questions = random.sample(question_pool, 10)
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.rerun()
    questions = st.session_state.quiz_questions
    st.caption(f"This round draws 10 questions at random from a pool of {len(question_pool)}. Quiz points can be earned once per app session.")
    with st.form("climate_quiz"):
        answers = {}
        for i, (q, opts, correct, explanation) in enumerate(questions):
            answers[i] = st.radio(f"{i+1}. {q}", opts, key=f"quiz_{st.session_state.quiz_round}_{i}")
        submitted = st.form_submit_button("Check answers")
    if submitted:
        score = sum(1 for i, (q, opts, correct, explanation) in enumerate(questions) if answers[i] == opts[correct])
        st.session_state.quiz_answers = answers
        st.session_state.quiz_score = score
        st.session_state.quiz_submitted = True
        if not st.session_state.quiz_awarded:
            earned = min(score * 5, max(0, 100 - int(st.session_state.points)))
            st.session_state.points = min(100, int(st.session_state.points) + earned)
            st.session_state.quiz_awarded = True
            st.success(f"You scored {score}/{len(questions)} and earned {earned} EcoPoints!")
        else:
            st.info(f"You scored {score}/{len(questions)}. Quiz points have already been awarded in this session.")
    if st.session_state.get("quiz_submitted"):
        for i, (q, opts, correct, explanation) in enumerate(questions):
            picked = st.session_state.quiz_answers.get(i)
            st.markdown(f"**Q{i+1}:** {'✅' if picked == opts[correct] else '❌'} {explanation}")
    if st.session_state.quiz_awarded:
        st.caption("To avoid repeatedly collecting points, this prototype awards quiz points once per session.")

elif page == "🌳 Tree Tracker":
    st.subheader("Tree planting and care tracker")
    st.write("Record trees you have planted or helped care for. Only count real activities.")
    amount = st.number_input("How many trees are you recording?", min_value=1, max_value=1000, value=1, step=1)
    activity = st.selectbox("Activity", ["Planted a tree", "Helped care for existing trees", "Joined a tree-planting event"])
    if st.button("Add tree activity", type="primary"):
        st.session_state.trees += int(amount)
        earned = min(int(amount) * 5, 50, max(0, 100 - int(st.session_state.points)))
        st.session_state.points = min(100, int(st.session_state.points) + earned)
        st.success(f"Recorded {amount} tree(s) for: {activity}. Earned {earned} EcoPoints (maximum 50 per entry).")
    st.metric("Trees / tree activities recorded", st.session_state.trees)
    st.caption("This prototype counts recorded activities, not independently verified surviving trees. Tree planting should use suitable native species and appropriate local guidance.")

elif page == "💬 Eco Chatbot":
    st.subheader("EcoGuide — AI environmental assistant")
    st.write("Ask questions about climate, trees, recycling, water, energy, wildlife, or pollution.")
    st.caption("AI answers can be imperfect. Do not enter passwords, private details, or sensitive information.")

    if "eco_chat_history" not in st.session_state:
        st.session_state.eco_chat_history = []

    for item in st.session_state.eco_chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("Ask EcoGuide an environmental question...")
    if prompt:
        st.session_state.eco_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key or api_key == "PASTE_YOUR_NEW_API_KEY_HERE":
            answer = "Gemini AI is not configured yet. Add GEMINI_API_KEY to your Streamlit app's Secrets, then restart or rerun the app. Never put the key in GitHub code."
            with st.chat_message("assistant"):
                st.warning(answer)
        else:
            with st.chat_message("assistant"):
                with st.spinner("EcoGuide is thinking..."):
                    try:
                        history = []
                        for item in st.session_state.eco_chat_history[-10:]:
                            role = "user" if item["role"] == "user" else "model"
                            history.append({"role": role, "parts": [{"text": item["content"]}]})
                        # Use Gemini's REST API so no extra Python package is needed.
                        response = requests.post(
                            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
                            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                            json={
                                "systemInstruction": {"parts": [{"text": "You are EcoGuide, a friendly environmental education assistant for students. Give clear, accurate, age-appropriate answers about the environment. Use simple language, practical safe actions, and concise explanations. Do not ask for personal information. If unsure, say so."}]},
                                "contents": history,
                                "generationConfig": {"temperature": 0.6, "maxOutputTokens": 700}
                            },
                            timeout=30
                        )
                        if response.status_code == 200:
                            data = response.json()
                            answer = data["candidates"][0]["content"]["parts"][0]["text"]
                            st.markdown(answer)
                        elif response.status_code in (400, 401, 403):
                            answer = "Gemini could not accept the API key or request. Check that your key is valid, the Gemini API is enabled, and your free-tier quota is available. Do not share the key publicly."
                            st.error(answer)
                        elif response.status_code == 429:
                            answer = "The Gemini free-tier limit may have been reached. Please wait a while and try again."
                            st.warning(answer)
                        else:
                            answer = f"Gemini returned an error (HTTP {response.status_code}). Please try again later."
                            st.error(answer)
                    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
                        answer = "I couldn't get an AI response just now. Check the app's internet connection and try again."
                        st.error(answer)
            st.session_state.eco_chat_history.append({"role": "assistant", "content": answer})

    if st.button("Clear chat history"):
        st.session_state.eco_chat_history = []
        st.rerun()

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
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,precipitation,rain,showers,snowfall,weather_code",
                        "timezone": "auto"
                    },
                    timeout=10
                )
                weather.raise_for_status()
                current = weather.json().get("current", {})
                weather_codes = {
                    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
                    55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
                    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
                    67: "Heavy freezing rain", 71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                    77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
                    82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
                    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
                }
                st.success(f"Weather for {place['name']}, {place.get('country', '')}")
                code = current.get("weather_code")
                description = weather_codes.get(code, "Condition unavailable")
                st.markdown(f"### {description}")
                a, b, c = st.columns(3)
                a.metric("Temperature", f"{current.get('temperature_2m', 'N/A')} °C")
                b.metric("Feels like", f"{current.get('apparent_temperature', 'N/A')} °C")
                c.metric("Wind speed", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                st.write(f"Relative humidity: **{current.get('relative_humidity_2m', 'N/A')}%**")
                st.write(f"Precipitation: **{current.get('precipitation', 'N/A')} mm** · Rain: **{current.get('rain', 'N/A')} mm** · Showers: **{current.get('showers', 'N/A')} mm** · Snowfall: **{current.get('snowfall', 'N/A')} cm**")
                st.caption(f"Condition code: {code if code is not None else 'unavailable'} · Observation time: {current.get('time', 'unavailable')} ({weather.json().get('timezone_abbreviation', 'local time')})")
                st.caption("Weather data supplied by Open-Meteo. Conditions can change; check official local warnings for safety-critical decisions.")
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            st.error("Could not connect to the weather service. Check your internet connection and try again.")
    st.subheader("Weather vs climate")
    st.markdown("""
    - **Weather:** conditions over minutes, hours or days, such as today's rain or temperature.
    - **Climate:** patterns and averages measured over many years.
    - A single hot day does not prove climate change; scientists examine long-term observations and many kinds of evidence.
    """)
    st.caption("Weather service: Open-Meteo (internet connection required).")

elif page == "🌫️ Air Quality index(AQI)":
    st.subheader("Current air quality")
    st.write("Look up the latest available air-quality model data for a city. Readings and pollutant coverage vary by location and provider availability.")
    aqi_city = st.text_input("City for air quality", value="Chennai", key="aqi_city")
    if st.button("Get current AQI", type="primary", key="get_aqi"):
        try:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": aqi_city, "count": 1, "language": "en", "format": "json"},
                timeout=10,
            )
            geo.raise_for_status()
            places = geo.json().get("results", [])
            if not places:
                st.error("City not found. Try a larger nearby city or check the spelling.")
            else:
                place = places[0]
                air_response = requests.get(
                    "https://air-quality-api.open-meteo.com/v1/air-quality",
                    params={
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                        "current": "us_aqi,european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
                        "timezone": "auto",
                    },
                    timeout=15,
                )
                air_response.raise_for_status()
                air_data = air_response.json()
                current = air_data.get("current", {})
                us_aqi = current.get("us_aqi")
                eu_aqi = current.get("european_aqi")
                if us_aqi is None and eu_aqi is None:
                    st.warning("The air-quality service returned no current AQI for this location. Try again later or choose a nearby city.")
                else:
                    st.success(f"Air quality for {place['name']}, {place.get('country', '')}")
                    if us_aqi is not None:
                        if us_aqi <= 50:
                            category, advice = "Good", "Air quality is satisfactory for most people."
                        elif us_aqi <= 100:
                            category, advice = "Moderate", "Unusually sensitive people may consider reducing prolonged, heavy outdoor exertion."
                        elif us_aqi <= 150:
                            category, advice = "Unhealthy for sensitive groups", "Sensitive groups may wish to reduce prolonged outdoor exertion."
                        elif us_aqi <= 200:
                            category, advice = "Unhealthy", "Consider reducing prolonged outdoor exertion, especially if you are sensitive to air pollution."
                        elif us_aqi <= 300:
                            category, advice = "Very unhealthy", "Reduce prolonged outdoor exertion and follow local health guidance."
                        else:
                            category, advice = "Hazardous", "Avoid prolonged outdoor exertion and follow local health advisories."
                        st.metric("U.S. AQI", f"{us_aqi} · {category}")
                        st.info(advice)
                    if eu_aqi is not None:
                        st.metric("European AQI", str(eu_aqi))
                    pollutants = [
                        ("PM2.5", "pm2_5", "µg/m³"), ("PM10", "pm10", "µg/m³"),
                        ("Ozone", "ozone", "µg/m³"), ("Nitrogen dioxide", "nitrogen_dioxide", "µg/m³"),
                        ("Sulphur dioxide", "sulphur_dioxide", "µg/m³"), ("Carbon monoxide", "carbon_monoxide", "µg/m³"),
                    ]
                    available = [(label, current[key], unit) for label, key, unit in pollutants if current.get(key) is not None]
                    if available:
                        st.subheader("Pollutants")
                        cols = st.columns(min(3, len(available)))
                        for index, (label, value, unit) in enumerate(available):
                            cols[index % len(cols)].metric(label, f"{value} {unit}")
                    st.caption(f"Model data time: {current.get('time', 'unavailable')} ({air_data.get('timezone_abbreviation', 'local time')}). AQI is not a direct measurement from a local monitoring station; follow official local advisories.")
        except requests.RequestException:
            st.error("Could not connect to the air-quality service. Check your internet connection and try again.")
        except (KeyError, TypeError, ValueError):
            st.error("The air-quality service returned data in an unexpected format. Please try again later.")
    st.caption("Air-quality data: Open-Meteo Air Quality API (internet connection required). AQI values use the provider's published index; pollutant concentrations are shown when available.")

st.divider()
st.caption("EcoGuard prototype • Educational use • Verify local environmental and emergency guidance with official sources.")

# Persist this profile after page actions and reruns.
save_progress()
