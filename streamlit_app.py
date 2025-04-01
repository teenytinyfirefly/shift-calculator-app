# File: streamlit_app.py

import streamlit as st
import re
from datetime import datetime, date, timedelta

# --- Configuration (Copied from original script) ---
ANCHOR_DATE = date(2025, 3, 12)
ANCHOR_DAY_NUM = 3  # March 12, 2025 is Day 3

GOLD_ROTATION = {
    2: {1: 'Early', 2: 'Middle', 3: 'Late', 4: 'Middle'},
    3: {1: 'Middle', 2: 'Late', 3: 'Middle', 4: 'Early'},
    4: {1: 'Late', 2: 'Middle', 3: 'Early', 4: 'Middle'},
    5: {1: 'Middle', 2: 'Early', 3: 'Middle', 4: 'Late'},
}

# --- Helper Functions (Copied from original script) ---

def clean_input(text):
    """Removes extra spaces, converts to lowercase, removes commas."""
    if not isinstance(text, str):
        return ""
    text = text.strip().lower().replace(',', '')
    text = re.sub(r'\s+', ' ', text)
    return text

# NOTE: Streamlit's date_input handles parsing, so parse_date_flexible is less critical here
# We'll rely on st.date_input for simplicity, but keep clean_input for the shift name.

# --- Core Calculation Functions (Copied from original script) ---

def get_day_number(target_dt):
    """Calculates the day number (1-4) for a given date."""
    if not isinstance(target_dt, date):
        raise TypeError("Internal Error: Input must be a date object.")
    delta_days = (target_dt - ANCHOR_DATE).days
    return (delta_days + ANCHOR_DAY_NUM - 1) % 4 + 1

def get_shift_type_or_info(shift_str, day_num):
    """
    Determines shift type (Early/Middle/Late) for Gold/Silver shifts.
    Returns None for non-Gold/Silver shifts.
    Returns error strings for parsing issues with Gold/Silver.
    """
    if not isinstance(day_num, int) or not 1 <= day_num <= 4:
         return "Error: Invalid Day Number calculated."

    clean_shift = clean_input(shift_str)
    if not clean_shift:
        return "Error: Shift name input cannot be empty."

    parts = clean_shift.split()
    shift_name = parts[0]
    num = 0

    if shift_name not in ["gold", "silver"]:
        return None # Indicates non-Gold/Silver shift

    if len(parts) == 1:
        if shift_name == "silver":
            num = 1
            # Use st.info for contextual messages in Streamlit if needed inside logic
            # st.info(f"(Interpreting '{shift_str}' as Silver 1)") # Can't use st here directly
        else:
             return f"Error: Shift '{shift_str}' needs a number (e.g., Gold 3)."
    elif len(parts) == 2:
        try:
            num = int(parts[1])
            if num <= 0:
                 return f"Error: Shift number in '{shift_str}' must be positive."
        except ValueError:
            return f"Error: Invalid number '{parts[1]}' in shift '{shift_str}'."
    else:
        return f"Error: Cannot parse shift format '{shift_str}'. Expected 'Gold #', 'Silver #', or 'Silver'."

    if shift_name == "gold":
        if num == 1: return "Early"
        if num >= 6: return "Middle"
        if 2 <= num <= 5:
            return GOLD_ROTATION.get(num, {}).get(day_num, f"Internal Error: Missing Gold {num} Day {day_num} rule.")
        return f"Error: Invalid Gold shift number {num}."
    elif shift_name == "silver":
        if num == 1: return "Early"
        if num >= 2: return "Middle"
        return f"Error: Invalid Silver shift number {num}."

    return "Internal Error: Could not determine shift type."


# --- Streamlit User Interface ---

st.title("Shift Day Number and Type Calculator")


st.markdown(f"""
Calculates the **Day Number (1-4)** based on a known reference date.

For **Gold** or **Silver** shifts, it also determines the type (Early/Middle/Late).
For other shifts, please refer to the schedule and use the day number to determine type of shift.
""")


# Input Widgets
# Use st.date_input for a user-friendly calendar picker. It returns a datetime.date object.
input_date = st.date_input("Select the date:")

input_shift_raw = st.text_input("Enter the shift name (e.g., Gold 5, Silver 2, Blue):")

# Button to trigger calculation
if st.button("Calculate Day Number & Shift Type"):
    # Validate inputs exist
    if not input_shift_raw:
        st.warning("Please enter a shift name.")
    elif input_date is None: # Should not happen with date_input unless cleared?
         st.warning("Please select a date.")
    else:
        # Perform calculations
        try:
            day_num = get_day_number(input_date)
            result = get_shift_type_or_info(input_shift_raw, day_num) # Pass raw input for context

            # Display Results
            st.subheader("--- Result ---")
            st.write(f"**Date:** {input_date.strftime('%A, %B %d, %Y')}")
            st.write(f"**Calculated Day Number:** {day_num}")
            st.write(f"**Input Shift:** {input_shift_raw}")

            if result is None: # Non-Gold/Silver shift
                st.info(f"This is Day {day_num}. For '{input_shift_raw}', "
                        "refer to the most updated scheduling details to determine the shift timing.")
            elif isinstance(result, str):
                if result.startswith("Error:"):
                    st.error(result) # Display errors clearly
                else: # Success (Early/Middle/Late)
                    st.success(f"Determined Shift Type: {result}")

        except Exception as e:
            # Catch any unexpected errors during calculation
            st.error(f"An unexpected error occurred during calculation: {e}")

st.markdown("---") # Visual separator
st.caption("Calculate the assigned number of a date and the shift type (for gold and silver only)")