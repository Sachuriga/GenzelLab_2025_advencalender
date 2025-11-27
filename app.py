import streamlit as st
import pandas as pd
import random
import datetime
import io
import requests

# --- Configuration ---
CURRENT_YEAR = 2025
FIXED_NAME_24 = "Sachuriga"  # Secretly fixed to Day 24
# 👇 PASTE YOUR GITHUB LINK HERE 👇
DATA_URL = "https://github.com/YOUR_USERNAME/YOUR_REPO/blob/main/names.xlsx?raw=true"

# --- Page Setup ---
st.set_page_config(
    page_title="Christmas Advent Allocator",
    page_icon="🎅",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stApp {
        background-image: url("https://www.transparenttextures.com/patterns/snow.png");
    }
    h1 {
        color: #D42426;
        text-align: center;
        font-family: 'Georgia', serif;
    }
    .bag-card {
        background-color: white;
        border: 2px solid #165B33;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .day-number {
        font-size: 24px;
        font-weight: bold;
        color: #D42426;
    }
    .names {
        font-size: 18px;
        color: #333;
        margin-top: 5px;
        font-weight: 500;
    }
    .pickup-info {
        font-size: 14px;
        color: #165B33;
        font-style: italic;
        margin-top: 10px;
        border-top: 1px dashed #ccc;
        padding-top: 5px;
    }
    /* Simple button styling */
    .stButton>button {
        background-color: #D42426;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #B01E20;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def get_pickup_date(day, year):
    date_obj = datetime.date(year, 12, day)
    weekday = date_obj.weekday() # 0=Mon, 5=Sat, 6=Sun
    
    pickup_msg = ""
    if weekday == 5: # Saturday
        pickup_date = date_obj - datetime.timedelta(days=1)
        pickup_msg = f"🗓️ Weekend Rule: Pick up on Friday, Dec {pickup_date.day}"
    elif weekday == 6: # Sunday
        pickup_date = date_obj + datetime.timedelta(days=1)
        pickup_msg = f"🗓️ Weekend Rule: Pick up on Monday, Dec {pickup_date.day}"
    else:
        pickup_msg = f"🗓️ Pick up on {date_obj.strftime('%A')}, Dec {day}"
    return pickup_msg

@st.cache_data(ttl=600) # Caches the data for 10 mins so we don't spam GitHub
def load_data_from_github(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Read Excel content from the response
        return pd.read_excel(io.BytesIO(response.content), header=None)
    except Exception as e:
        return None

def allocate_names(names_list):
    # 1. Clean the list: Remove the fixed person (Sachuriga)
    filtered_names = [str(name) for name in names_list if str(name).lower().strip() != FIXED_NAME_24.lower()]
    
    # 2. Define Random Bags (Days 1-23 + extra 8) -> 24 bags total
    random_bags = [{'day': i, 'assigned': []} for i in range(1, 24)]
    random_bags.append({'day': 8, 'assigned': []})
    
    total_random_bags = 24
    total_people = len(filtered_names)
    
    random.shuffle(filtered_names)
    
    # Logic 1: Fewer people than bags
    if total_people < total_random_bags:
        for i in range(total_people):
            random_bags[i]['assigned'].append(filtered_names[i])
        
        remaining_bags_indices = list(range(total_people, total_random_bags))
        name_index = 0
        random.shuffle(filtered_names)
        
        for bag_idx in remaining_bags_indices:
            random_bags[bag_idx]['assigned'].append(filtered_names[name_index])
            name_index = (name_index + 1) % total_people

    # Logic 2: More people than bags
    else:
        for i in range(total_random_bags):
            random_bags[i]['assigned'].append(filtered_names[i])
            
        remaining_people = filtered_names[total_random_bags:]
        bag_indices = list(range(total_random_bags))
        random.shuffle(bag_indices)
        
        for i, person in enumerate(remaining_people):
            target_bag_index = bag_indices[i % total_random_bags]
            random_bags[target_bag_index]['assigned'].append(person)

    # 3. Create Fixed Bag 24 (Stealth Mode)
    bag_24 = {'day': 24, 'assigned': [FIXED_NAME_24]}
    
    # 4. Combine
    all_bags = random_bags + [bag_24]
    all_bags.sort(key=lambda x: x['day'])
    
    return all_bags

# --- Main App Logic ---

st.title("🎅 Secret Advent Calendar Generator 🎄")
st.markdown("### Distribute the sugary surprises!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    st.write("Data Source: GitHub Linked ✅")
    
    # We use a session state to keep the results stable until "Regenerate" is clicked
    if 'allocation_done' not in st.session_state:
        st.session_state.allocation_done = False

    generate_btn = st.button("🎁 Generate / Shuffle", use_container_width=True)

if generate_btn:
    st.session_state.allocation_done = True
    # We force a re-run of the logic below

if st.session_state.allocation_done:
    # Load Data
    df = load_data_from_github(DATA_URL)
    
    if df is None:
        st.error(f"❌ Could not load data from GitHub. Please check the URL in the code.\nCurrent URL: `{DATA_URL}`")
    else:
        names = df.iloc[:, 0].dropna().astype(str).tolist()
        # Clean header if exists
        if names and names[0].lower() == 'name':
            names.pop(0)

        if not names:
            st.error("The file on GitHub seems empty!")
        else:
            st.snow()
            
            # Run Allocation
            result_bags = allocate_names(names)
            
            st.success(f"Loaded {len(names)} names from GitHub and distributed them!")
            
            cols = st.columns(3)
            
            for index, bag in enumerate(result_bags):
                col_idx = index % 3
                pickup_text = get_pickup_date(bag['day'], CURRENT_YEAR)
                people_string = " & ".join(bag['assigned'])
                day_display = f"Day {bag['day']}"

                with cols[col_idx]:
                    st.markdown(f"""
                        <div class="bag-card">
                            <div class="day-number">🎁 {day_display}</div>
                            <div class="names">{people_string}</div>
                            <div class="pickup-info">{pickup_text}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Export
            export_data = []
            for bag in result_bags:
                export_data.append({
                    "Day": bag['day'],
                    "Assigned": ", ".join(bag['assigned']),
                    "Pickup Instructions": get_pickup_date(bag['day'], CURRENT_YEAR)
                })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "📥 Download List as CSV",
                csv,
                "advent_calendar_allocations.csv",
                "text/csv",
                key='download-csv'
            )
else:
    st.info("👋 Click the **Generate** button in the sidebar to fetch names from GitHub and start the lottery!")