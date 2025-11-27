import streamlit as st
import pandas as pd
import random
import datetime

# --- Configuration ---
CURRENT_YEAR = 2025
FIXED_NAME_24 = "Sachuriga"  # Still assigned here, but hidden in the UI!

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
    /* Standard card style for EVERY day */
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

def allocate_names(names_list):
    """
    Allocates names to 24 random bags (1-23 + extra 8).
    Day 24 is quietly fixed to Sachuriga.
    """
    
    # 1. Clean the list: Remove Sachuriga if they are in the excel file
    # so they don't get assigned twice.
    filtered_names = [name for name in names_list if name.lower().strip() != FIXED_NAME_24.lower()]
    
    # 2. Define the Random Pool Bags (Days 1 to 23, plus an extra 8)
    # Total = 24 bags to fill randomly
    random_bags = [{'day': i, 'assigned': []} for i in range(1, 24)]
    random_bags.append({'day': 8, 'assigned': []}) # The extra 8
    
    total_random_bags = 24
    total_people = len(filtered_names)
    
    # Shuffle the remaining names
    random.shuffle(filtered_names)
    
    # --- Logic 1: Fewer people than random bags (N < 24) ---
    if total_people < total_random_bags:
        # Give everyone at least one
        for i in range(total_people):
            random_bags[i]['assigned'].append(filtered_names[i])
            
        # Distribute remaining bags
        remaining_bags_indices = list(range(total_people, total_random_bags))
        name_index = 0
        random.shuffle(filtered_names) # Reshuffle
        
        for bag_idx in remaining_bags_indices:
            random_bags[bag_idx]['assigned'].append(filtered_names[name_index])
            name_index = (name_index + 1) % total_people

    # --- Logic 2: More people than random bags (N > 24) ---
    else:
        # Fill every bag once
        for i in range(total_random_bags):
            random_bags[i]['assigned'].append(filtered_names[i])
            
        # Distribute remaining people
        remaining_people = filtered_names[total_random_bags:]
        bag_indices = list(range(total_random_bags))
        random.shuffle(bag_indices)
        
        for i, person in enumerate(remaining_people):
            target_bag_index = bag_indices[i % total_random_bags]
            random_bags[target_bag_index]['assigned'].append(person)

    # 3. Create the Fixed Day 24 Bag (Stealthily)
    bag_24 = {
        'day': 24,
        'assigned': [FIXED_NAME_24]
    }
    
    # 4. Combine and Sort
    all_bags = random_bags + [bag_24]
    all_bags.sort(key=lambda x: x['day'])
    
    return all_bags

# --- Main App Logic ---

st.title("🎅 Secret Advent Calendar Generator 🎄")
st.markdown("### Distribute the sugary surprises!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Setup")
    uploaded_file = st.file_uploader("Upload Names (.xlsx)", type=['xlsx', 'xls'])
    
    generate_btn = st.button("🎁 Generate Calendar", use_container_width=True)

if uploaded_file is not None and generate_btn:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        names = df.iloc[:, 0].dropna().astype(str).tolist()
        
        if names and names[0].lower() == 'name':
            names.pop(0)
            
        if len(names) == 0:
            st.error("The file seems empty!")
        else:
            st.snow()
            
            # Run Allocation
            result_bags = allocate_names(names)
            
            st.success("Allocation Complete! Scroll down to see the calendar.")
            
            cols = st.columns(3)
            
            for index, bag in enumerate(result_bags):
                col_idx = index % 3
                
                pickup_text = get_pickup_date(bag['day'], CURRENT_YEAR)
                people_string = " & ".join(bag['assigned'])
                day_display = f"Day {bag['day']}"
                
                # Render the card (No special styling for 24 anymore!)
                with cols[col_idx]:
                    st.markdown(f"""
                        <div class="bag-card">
                            <div class="day-number">🎁 {day_display}</div>
                            <div class="names">{people_string}</div>
                            <div class="pickup-info">{pickup_text}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Export Logic
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

    except Exception as e:
        st.error(f"An error occurred: {e}")
        
elif not uploaded_file:
    st.info("Please upload your Excel file to begin.")