import sqlite3
from datetime import date
from pathlib import Path
import requests
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "ecoguard.db"

st.set_page_config(page_title="EcoGuard", page_icon="🌍", layout="wide")

# -------------------- Database --------------------
def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                points INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("INSERT OR IGNORE INTO profile (id, points) VALUES (1, 0)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completed_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_date TEXT NOT NULL,
                challenge TEXT NOT NULL,
                points INTEGER NOT NULL,
                UNIQUE(challenge_date, challenge)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                answered_on TEXT NOT NULL,
                UNIQUE(question_id, answered_on)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planted_on TEXT NOT NULL,
                species TEXT NOT NULL,
                count INTEGER NOT NULL,
                location TEXT NOT NULL
            )
        """)

def get_points():
    with connect() as conn:
        row = conn.execute("SELECT points FROM profile WHERE id=1").fetchone()
        return int(row["points"])

def add_points(amount):
    with connect() as conn:
        conn.execute("UPDATE profile SET points = points + ? WHERE id=1", (amount,))

def challenge_done_today(challenge):
    with connect() as conn:
        return conn.execute(
            "SELECT 1 FROM completed_challenges WHERE challenge_date=? AND challenge=?",
            (date.today().isoformat(), challenge)
        ).fetchone() is not None

def complete_challenge(challenge, points):
    with connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO completed_challenges (challenge_date, challenge, points) VALUES (?, ?, ?)",
            (date.today().isoformat(), challenge, points)
        )
        if cur.rowcount:
            conn.execute("UPDATE profile SET points = points + ? WHERE id=1", (points,))
            return True
        return False

def already_answered(question_id):
    with connect() as conn:
        return conn.execute(
            "SELECT 1 FROM quiz_answers WHERE question_id=? AND answered_on=?",
            (question_id, date.today().isoformat())
        ).fetchone() is not None

def save_quiz_answer(question_id, points):
    with connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO quiz_answers (question_id, answered_on) VALUES (?, ?)",
            (question_id, date.today().isoformat())
        )
        if cur.rowcount:
            conn.execute("UPDATE profile SET points = points + ? WHERE id=1", (points,))
            return True
        return False

init_db()

# -------------------- Content --------------------
LESSONS = {
    "Climate change basics": {
        "summary": "Climate change means long-term changes in Earth's temperatures and weather patterns.",
        "details": [
            "Human activities, especially burning coal, oil and gas, add greenhouse gases such as carbon dioxide to the atmosphere.",
            "Greenhouse gases trap some heat and warm the planet. This is called the greenhouse effect.",
            "Impacts can include rising sea levels, heatwaves, changing rainfall, and risks to ecosystems and people.",
            "Solutions include clean energy, saving energy, protecting forests, reducing waste, and preparing communities for climate impacts."
        ]
    },
    "Pollution and waste": {
        "summary": "Pollution happens when harmful materials or energy enter the environment.",
        "details": [
            "Plastic litter can harm wildlife and break into smaller pieces.",
            "Burning waste can release harmful air pollutants. Never burn rubbish as a disposal method.",
            "Reduce waste first, reuse items when possible, and recycle materials accepted by local services.",
            "Dispose of batteries, electronics and chemicals through suitable collection services rather than ordinary litter bins."
        ]
    },
    "Biodiversity and forests": {
        "summary": "Biodiversity is the variety of living things, including plants, animals, fungi and microorganisms.",
        "details": [
            "Healthy ecosystems provide food, clean water, soil protection and habitats.",
            "Deforestation and habitat loss can put species at risk.",
            "Native plants can support local wildlife when planted in suitable places.",
            "Tree planting works best when the right species are planted in the right place and cared for over time."
        ]
    },
    "Saving energy and water": {
        "summary": "Using energy and water thoughtfully can reduce waste and some environmental impacts.",
        "details": [
            "Switch off lights and devices when they are not needed.",
            "Choose walking, cycling or public transport when safe and practical.",
            "Fix leaking taps and avoid letting water run unnecessarily.",
            "The best action depends on local conditions, access and personal circumstances."
        ]
    }
}

QUIZ = [
    {
        "id": "q1",
        "question": "Which gas is a major contributor to human-caused global warming?",
        "options": ["Oxygen", "Carbon dioxide", "Helium", "Neon"],
        "answer": "Carbon dioxide",
        "explanation": "Carbon dioxide is released by activities such as burning fossil fuels and contributes to the enhanced greenhouse effect."
    },
    {
        "id": "q2",
        "question": "Which action usually helps reduce single-use plastic waste?",
        "options": ["Using a reusable bottle", "Taking extra plastic bags", "Littering less carefully", "Burning plastic at home"],
        "answer": "Using a reusable bottle",
        "explanation": "A reusable bottle can replace many disposable bottles when it is used and cleaned regularly."
    },
    {
        "id": "q3",
        "question": "What does biodiversity mean?",
        "options": ["Only the number of trees", "The variety of living things", "The amount of plastic", "The daily temperature"],
        "answer": "The variety of living things",
        "explanation": "Biodiversity includes the variety of species, genes and ecosystems."
    },
    {
        "id": "q4",
        "question": "What is a sensible way to care for a newly planted tree?",
        "options": ["Choose a suitable species and care for it", "Plant it anywhere without checking", "Leave all planted trees unwatered", "Remove its roots before planting"],
        "answer": "Choose a suitable species and care for it",
        "explanation": "Suitable species, location, watering and ongoing care improve the chance of survival."
    },
    {
        "id": "q5",
        "question": "Which is a renewable source of electricity?",
        "options": ["Coal", "Diesel", "Solar energy", "Petrol"],
        "answer": "Solar energy",
        "explanation": "Solar energy uses sunlight, which is naturally replenished."
    },
]

CHALLENGES = [
    ("Carry a reusable water bottle", 5),
    ("Switch off an unused light", 5),
    ("Use both sides of a sheet of paper", 5),
    ("Sort recyclable waste correctly", 5),
    ("Walk or cycle for a short trip if safe and practical", 10),
    ("Learn one new fact about local wildlife", 5),
    ("Check a tap for leaks and tell an adult if you find one", 5),
]

# Simple offline assistant: keyword-based educational responses, not a generative AI model.
def eco_answer(question):
    q = question.lower()
    if any(word in q for word in ["climate change", "global warming", "warming"]):
        return ("Climate change is a long-term shift in temperatures and weather patterns. "
                "Human-caused warming is mainly driven by greenhouse gases from burning fossil fuels. "
                "Helpful actions include saving energy, using lower-emission transport where practical, "
                "reducing waste and supporting climate solutions.")
    if any(word in q for word in ["plastic", "waste", "recycle", "litter"]):
        return ("Start by reducing what you throw away, reusing items, and sorting recycling according to "
                "your local rules. Avoid littering and never burn plastic or household rubbish.")
    if any(word in q for word in ["tree", "plant", "forest"]):
        return ("Choose a suitable native or locally recommended species, get permission for the location, "
                "and make a plan for watering and care. Planting a tree is most useful when it survives "
                "and supports the local ecosystem.")
    if any(word in q for word in ["carbon", "footprint", "emission"]):
        return ("A carbon footprint estimates greenhouse-gas emissions linked to activities such as travel "
                "and electricity use. EcoGuard's calculator is a rough educational estimate, not a formal audit.")
    if any(word in q for word in ["water", "save water"]):
        return ("You can reduce water waste by turning off taps when not needed, reporting leaks, and using "
                "water carefully in gardens. Local water-saving advice may differ by region.")
    if any(word in q for word in ["energy", "electricity", "solar"]):
        return ("Saving electricity can reduce energy demand. Switch off unused devices, use efficient lights, "
                "and learn about renewable energy such as solar and wind power.")
    return ("Good environmental questions! Try asking about climate change, plastic waste, trees, water, "
            "energy or carbon footprints. This first assistant uses simple built-in responses; connecting a "
            "real AI model will be a later step.")

# -------------------- App styling and navigation --------------------
st.markdown("""
<style>
    :root { color-scheme: dark; }
    .stApp {
        background: radial-gradient(ellipse at top left, #123b32 0%, #081b19 38%, #07110f 100%);
        color: #e8fff3;
    }
    [data-testid="stHeader"] { background: rgba(5, 18, 16, 0.88); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c2924 0%, #071512 100%);
        border-right: 1px solid #1c5948;
    }
    [data-testid="stSidebar"] * { color: #e3fff0 !important; }
    h1, h2, h3, h4 { color: #69ffb0 !important; }
    p, label, li, .stMarkdown, [data-testid="stCaptionContainer"] { color: #d7eee4; }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(22, 66, 54, .96), rgba(10, 35, 30, .96));
        border: 1px solid #267b5c;
        padding: 16px;
        border-radius: 16px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, .18);
    }
    [data-testid="stMetricLabel"] { color: #a6d9c0 !important; }
    [data-testid="stMetricValue"] { color: #75ffb6 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(12, 39, 33, .72);
        border: 1px solid #205c49;
        border-radius: 16px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #16a36a, #48e69a);
        color: #04150f !important;
        border: 0;
        border-radius: 10px;
        font-weight: 700;
    }
    .stButton > button:hover { background: #75ffb6; color: #04150f !important; border: 0; }
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    [data-baseweb="select"] > div, [data-baseweb="input"] > div {
        background-color: #102a24 !important;
        color: #edfff5 !important;
        border-color: #2d765a !important;
    }
    [data-testid="stAlert"] { border-radius: 12px; }
    a { color: #75ffb6 !important; }
    hr { border-color: #245b48; }
    @media (max-width: 700px) {
        .block-container { padding-top: 1.2rem; padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 2rem !important; }
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌍 EcoGuard")
st.sidebar.caption("Learn today. Protect tomorrow.")
page = st.sidebar.radio(
    "Explore EcoGuard",
    ["Home", "Climate lessons", "Eco quiz", "Daily challenges",
     "Carbon calculator", "Tree tracker", "Live Weather", "AI Eco Assistant"]
)
st.sidebar.divider()
st.sidebar.metric("🌱 Eco points", get_points())
st.sidebar.caption("Starter version · Saved on this device/server")

# -------------------- Home --------------------
if page == "Home":
    st.title("🌍 EcoGuard")
    st.subheader("Small actions. A healthier planet.")
    st.write("Learn about climate change, try eco-friendly habits, and track your environmental actions.")
    a, b, c = st.columns(3)
    a.metric("Eco points", get_points())
    with connect() as conn:
        tree_row = conn.execute("SELECT COALESCE(SUM(count), 0) AS total FROM trees").fetchone()
        challenge_row = conn.execute("SELECT COUNT(*) AS total FROM completed_challenges").fetchone()
    b.metric("Trees recorded", int(tree_row["total"]))
    c.metric("Challenges completed", int(challenge_row["total"]))
    st.info("Start with one small action today. Progress is more important than perfection.")
    st.markdown("### Explore")
    st.write("- **Climate lessons:** understand the science.")
    st.write("- **Eco quiz:** check what you know and earn points.")
    st.write("- **Daily challenges:** practise helpful habits.")
    st.write("- **Carbon calculator:** estimate selected emissions.")
    st.write("- **Tree tracker:** record planting and care.")
    st.write("- **Live Weather:** check current conditions and a short forecast for a city or your location.")
    st.write("- **AI Eco Assistant:** ask common environmental questions.")

# -------------------- Lessons --------------------
elif page == "Climate lessons":
    st.title("📚 Climate lessons")
    topic = st.selectbox("Choose a lesson", list(LESSONS.keys()))
    lesson = LESSONS[topic]
    st.subheader(topic)
    st.write(lesson["summary"])
    for item in lesson["details"]:
        st.markdown(f"- {item}")
    st.caption("Learning note: climate and environmental impacts vary by place. Use trusted scientific and local sources for decisions.")

# -------------------- Quiz --------------------
elif page == "Eco quiz":
    st.title("🏆 Eco quiz")
    st.write("Choose an answer for each question. You can earn 10 points for each correct answer, once per question per day.")
    for item in QUIZ:
        with st.container(border=True):
            st.markdown(f"**{item['question']}**")
            answered = already_answered(item["id"])
            choice = st.radio(
                "Choose one answer",
                item["options"],
                key=f"choice_{item['id']}",
                index=None,
                disabled=answered,
                label_visibility="collapsed"
            )
            if answered:
                st.success("This question has already been scored today.")
            elif st.button("Check answer", key=f"check_{item['id']}"):
                if choice is None:
                    st.warning("Choose an answer first.")
                elif choice == item["answer"]:
                    if save_quiz_answer(item["id"], 10):
                        st.success("Correct! +10 points.")
                    else:
                        st.info("This question was already scored today.")
                    st.write(item["explanation"])
                    st.rerun()
                else:
                    st.error("Not quite. The correct answer is: " + item["answer"])
                    st.write(item["explanation"])
                    # Wrong answers are not saved, so the user can try again.

# -------------------- Challenges --------------------
elif page == "Daily challenges":
    st.title("✅ Daily eco challenges")
    st.write("Complete actions only when they are safe and practical for you. Each challenge can earn points once per day.")
    for challenge, points in CHALLENGES:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.write(challenge)
            right.caption(f"+{points} points")
            if challenge_done_today(challenge):
                st.success("Completed today")
            elif st.button("Mark completed", key=f"challenge_{challenge}"):
                if complete_challenge(challenge, points):
                    st.success(f"Nice work! +{points} points.")
                    st.rerun()
                else:
                    st.info("Already completed today.")

# -------------------- Carbon calculator --------------------
elif page == "Carbon calculator":
    st.title("🧮 Carbon footprint calculator")
    st.write("A simplified educational estimate for selected activities. Actual emissions depend on location, vehicle, fuel, electricity supply and other factors.")
    st.markdown("#### Electricity")
    electricity = st.number_input("Electricity used (kWh per month)", min_value=0.0, max_value=100000.0, value=100.0, step=10.0)
    grid_factor = st.number_input(
        "Electricity emissions factor (kg CO₂e per kWh)",
        min_value=0.0, max_value=3.0, value=0.70, step=0.05,
        help="Editable example factor only. Replace it with a trusted, region-specific value for better estimates."
    )
    st.markdown("#### Travel")
    car_km = st.number_input("Car travel (km per month)", min_value=0.0, max_value=100000.0, value=100.0, step=10.0)
    car_factor = st.number_input(
        "Car emissions factor (kg CO₂e per km)",
        min_value=0.0, max_value=2.0, value=0.20, step=0.01,
        help="Rough example for a car trip; vehicle and occupancy can change the result."
    )
    bus_km = st.number_input("Bus travel (passenger-km per month)", min_value=0.0, max_value=100000.0, value=0.0, step=10.0)
    bus_factor = st.number_input(
        "Bus emissions factor (kg CO₂e per passenger-km)",
        min_value=0.0, max_value=1.0, value=0.08, step=0.01,
        help="Rough example only; actual value varies by bus and occupancy."
    )
    if st.button("Calculate estimate", type="primary"):
        electricity_emissions = electricity * grid_factor
        car_emissions = car_km * car_factor
        bus_emissions = bus_km * bus_factor
        total = electricity_emissions + car_emissions + bus_emissions
        st.metric("Estimated monthly emissions", f"{total:,.1f} kg CO₂e")
        st.write(f"- Electricity: {electricity_emissions:,.1f} kg CO₂e")
        st.write(f"- Car travel: {car_emissions:,.1f} kg CO₂e")
        st.write(f"- Bus travel: {bus_emissions:,.1f} kg CO₂e")
        st.caption("This is not a complete carbon footprint. It excludes food, purchases, waste, flights and many other sources.")

# -------------------- Tree tracker --------------------
elif page == "Tree tracker":
    st.title("🌳 Tree planting tracker")
    st.write("Record trees that have actually been planted. Avoid sharing a private home address.")
    with st.form("tree_form", clear_on_submit=True):
        planted_on = st.date_input("Planting date", value=date.today())
        species = st.text_input("Tree species (if known)", placeholder="e.g. neem")
        count = st.number_input("Number of trees planted", min_value=1, max_value=10000, value=1, step=1)
        location = st.text_input("General location", placeholder="e.g. school garden or local park")
        submitted = st.form_submit_button("Save tree record")
        if submitted:
            if not species.strip() or not location.strip():
                st.error("Please enter the species (or 'unknown') and a general location.")
            else:
                with connect() as conn:
                    conn.execute(
                        "INSERT INTO trees (planted_on, species, count, location) VALUES (?, ?, ?, ?)",
                        (planted_on.isoformat(), species.strip(), int(count), location.strip())
                    )
                st.success("Tree record saved!")
                st.rerun()
    with connect() as conn:
        records = conn.execute(
            "SELECT planted_on, species, count, location FROM trees ORDER BY planted_on DESC, id DESC"
        ).fetchall()
    st.subheader("Your records")
    if records:
        st.dataframe(
            [{"Date": r["planted_on"], "Species": r["species"], "Trees": r["count"], "General location": r["location"]} for r in records],
            use_container_width=True,
            hide_index=True
        )
        st.caption("This tracker records entries; it does not independently verify planting or tree survival.")
    else:
        st.info("No trees recorded yet. Add your first record above.")

# -------------------- Live weather --------------------
elif page == "Live Weather":
    st.title("🌦️ Live Weather")
    st.write("Check current weather and a 5-day forecast. Choose a city or allow your browser to share your location.")

    def weather_description(code):
        if code == 0: return "Clear sky ☀️"
        if code in (1, 2): return "Mainly clear / partly cloudy 🌤️"
        if code == 3: return "Overcast ☁️"
        if code in (45, 48): return "Foggy 🌫️"
        if code in (51, 53, 55, 56, 57): return "Drizzle 🌦️"
        if code in (61, 63, 65, 66, 67): return "Rain 🌧️"
        if code in (71, 73, 75, 77): return "Snow ❄️"
        if code in (80, 81, 82): return "Rain showers 🌧️"
        if code in (85, 86): return "Snow showers ❄️"
        if code in (95, 96, 99): return "Thunderstorm ⛈️"
        return "Conditions unavailable"

    location_choice = st.radio("Choose location method", ["Search city", "Use my location"], horizontal=True)
    selected_coords = None
    selected_name = None

    if location_choice == "Search city":
        with st.form("weather_city_form"):
            city = st.text_input("City or town", placeholder="e.g. Thiruvarur or Chennai")
            submitted = st.form_submit_button("Check weather", type="primary")
        if submitted:
            if not city.strip():
                st.warning("Enter a city or town name first.")
            else:
                try:
                    geo_resp = requests.get(
                        "https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": city.strip(), "count": 5, "language": "en", "format": "json"},
                        timeout=15,
                    )
                    geo_resp.raise_for_status()
                    results = geo_resp.json().get("results", [])
                    if not results:
                        st.error("I couldn't find that place. Check the spelling or try a nearby larger city.")
                    else:
                        picked = results[0]
                        picked_label = ", ".join(part for part in [picked.get("name"), picked.get("admin1"), picked.get("country")] if part)
                        st.session_state["weather_coords"] = (picked["latitude"], picked["longitude"])
                        st.session_state["weather_name"] = picked_label
                        st.rerun()
                except requests.RequestException:
                    st.error("Couldn't reach the weather service. Check your internet connection and try again.")
        if "weather_coords" in st.session_state:
            selected_coords = st.session_state["weather_coords"]
            selected_name = st.session_state.get("weather_name", "Selected location")
    else:
        st.info("Your browser may ask permission to share your location. Your coordinates are used to request weather and are not saved by this feature.")
        try:
            loc = streamlit_geolocation()
            if loc and loc.get("latitude") is not None and loc.get("longitude") is not None:
                selected_coords = (float(loc["latitude"]), float(loc["longitude"]))
                selected_name = "Your current location"
            else:
                st.caption("If no location appears, allow location access in your browser, or use Search city instead.")
        except Exception:
            st.warning("Location detection isn't available in this browser right now. Please use Search city instead.")

    if selected_coords:
        try:
            wx_resp = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": selected_coords[0], "longitude": selected_coords[1],
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset",
                    "timezone": "auto", "forecast_days": 5,
                },
                timeout=15,
            )
            wx_resp.raise_for_status()
            wx = wx_resp.json()
            current = wx.get("current", {})
            st.subheader(f"📍 {selected_name}")
            st.markdown(f"### {weather_description(current.get('weather_code', -1))}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Temperature", f"{current.get('temperature_2m', '—')} °C")
            m2.metric("Feels like", f"{current.get('apparent_temperature', '—')} °C")
            m3.metric("Humidity", f"{current.get('relative_humidity_2m', '—')}%")
            m4.metric("Wind", f"{current.get('wind_speed_10m', '—')} km/h")
            daily = wx.get("daily", {})
            if daily.get("time"):
                st.subheader("📅 5-day forecast")
                rows = []
                for i, day in enumerate(daily["time"]):
                    rows.append({
                        "Date": day,
                        "Conditions": weather_description(daily["weather_code"][i]),
                        "High (°C)": daily["temperature_2m_max"][i],
                        "Low (°C)": daily["temperature_2m_min"][i],
                        "Rain chance (%)": daily.get("precipitation_probability_max", [None] * len(daily["time"]))[i],
                    })
                st.dataframe(rows, use_container_width=True, hide_index=True)
                if daily.get("sunrise") and daily.get("sunset"):
                    st.caption(f"Sunrise: {daily['sunrise'][0].split('T')[-1]} · Sunset: {daily['sunset'][0].split('T')[-1]} (local time for this location)")
            st.caption("Weather provided by Open-Meteo. Forecasts can change; check local official alerts for safety-critical decisions.")
        except (requests.RequestException, ValueError, KeyError) as exc:
            st.error("Weather data couldn't be loaded just now. Check your internet connection and try again.")

# -------------------- Assistant (local Ollama AI) --------------------
elif page == "AI Eco Assistant":
    st.title("🤖 EcoGuard AI Assistant")
    st.write("Ask environmental, science, school, technology, coding, or general questions. This assistant uses a model running locally through Ollama.")

    ollama_url = "http://localhost:11434/api/chat"
    model_name = st.text_input("Ollama model", value="llama3.2:3b", help="Use the same model name you installed with `ollama run`, for example llama3.2:3b.")

    if "eco_chat_messages" not in st.session_state:
        st.session_state.eco_chat_messages = []

    for msg in st.session_state.eco_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask EcoGuard anything...")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear chat"):
            st.session_state.eco_chat_messages = []
            st.rerun()

    if question:
        st.session_state.eco_chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Keep recent messages so the model can understand follow-up questions.
        history = st.session_state.eco_chat_messages[-12:]
        payload = {
            "model": model_name.strip() or "llama3.2:3b",
            "messages": [
                {"role": "system", "content": (
                    "You are EcoGuard, a helpful, honest AI assistant. Answer questions across general topics, "
                    "including environment, science, school, technology and coding. Use clear, simple language "
                    "when helpful. For environmental topics, give practical and safe advice. Do not pretend to "
                    "have live data unless the user provides it. If unsure, say so."
                )},
                *history,
            ],
            "stream": False,
        }
        with st.chat_message("assistant"):
            with st.spinner("EcoGuard is thinking..."):
                try:
                    response = requests.post(ollama_url, json=payload, timeout=180)
                    response.raise_for_status()
                    answer = response.json().get("message", {}).get("content", "").strip()
                    if not answer:
                        answer = "I didn't receive a response. Please try again."
                    st.markdown(answer)
                    st.session_state.eco_chat_messages.append({"role": "assistant", "content": answer})
                except requests.exceptions.ConnectionError:
                    st.error("Can't connect to Ollama. Open Ollama on this computer and check that it is running, then try again.")
                    st.caption("You can test it in PowerShell with: ollama run llama3.2:3b")
                    st.session_state.eco_chat_messages.pop()  # remove unanswered user turn
                except requests.exceptions.Timeout:
                    st.error("The model took too long to respond. Try a shorter question or a smaller model.")
                    st.session_state.eco_chat_messages.pop()
                except requests.exceptions.HTTPError as exc:
                    st.error(f"Ollama returned an error ({response.status_code}). Check that the model name is correct and installed.")
                    st.caption("In PowerShell, run: ollama list")
                    st.session_state.eco_chat_messages.pop()
                except (ValueError, KeyError):
                    st.error("Ollama returned an unexpected response. Please try again.")
                    st.session_state.eco_chat_messages.pop()

st.divider()
st.caption("EcoGuard starter project · Educational estimates only · Be safe and follow local environmental guidance.")
