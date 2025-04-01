# File: streamlit_app.py (Version with Colored Lines)

import streamlit as st
import re
from datetime import datetime, date, timedelta

# --- Configuration ---
ANCHOR_DATE = date(2025, 3, 12)
ANCHOR_DAY_NUM = 3  # March 12, 2025 is Day 3

# --- Rotation Definitions ---

GOLD_ROTATION = {
    # Gold Num: {DayNum: ShiftType}
    2: {1: 'Early', 2: 'Middle', 3: 'Late', 4: 'Middle'},
    3: {1: 'Middle', 2: 'Late', 3: 'Middle', 4: 'Early'},
    4: {1: 'Late', 2: 'Middle', 3: 'Early', 4: 'Middle'},
    5: {1: 'Middle', 2: 'Early', 3: 'Middle', 4: 'Late'},
}

# Yellow, Purple, Blue, Bronze use the same suffix pattern
YPBB_SUFFIX_ROTATION = {
    # Suffix: {DayNum: ShiftType}
    "1-1": {1: 'Early', 2: 'Middle', 3: 'Late', 4: 'Middle'},
    "1-2": {1: 'Middle', 2: 'Late', 3: 'Middle', 4: 'Early'},
    "2-1": {1: 'Late', 2: 'Middle', 3: 'Early', 4: 'Middle'},
    "2-2": {1: 'Middle', 2: 'Early', 3: 'Middle', 4: 'Late'},
    "3":   {1: 'Middle', 2: 'Early', 3: 'Middle', 4: 'Late'},
}

# Green and MIST SCU rotations
GREEN_SUFFIX_ROTATION = {
    # Suffix: {DayNum: ShiftType}
    "1": {1: 'Early', 2: 'Middle', 3: 'Late', 4: 'Middle'},
    "2": {1: 'Middle', 2: 'Late', 3: 'Middle', 4: 'Early'},
    "3": {1: 'Late', 2: 'Middle', 3: 'Early', 4: 'Middle'},
}
MIST_SCU_ROTATION = {
    # DayNum: ShiftType
    1: 'Middle', 2: 'Early', 3: 'Middle', 4: 'Late'
}

# --- Helper Functions ---

def clean_input(text):
    """Removes extra spaces, converts to lowercase, removes commas."""
    if not isinstance(text, str):
        return ""
    text = text.strip().lower().replace(',', '')
    text = re.sub(r'\s+', ' ', text)
    return text

# --- Core Calculation Functions ---

def get_day_number(target_dt):
    """Calculates the day number (1-4) for a given date."""
    if not isinstance(target_dt, date):
        raise TypeError("Internal Error: Input must be a date object.")
    delta_days = (target_dt - ANCHOR_DATE).days
    return (delta_days + ANCHOR_DAY_NUM - 1) % 4 + 1

def get_shift_type_or_info(shift_str, day_num):
    """
    Determines shift type/info based on shift string and day number.
    Handles Gold, Silver, Yellow, Purple, Blue, Bronze, Green, MIST SCU.
    Returns formatted string for known lines, None for others, error strings for issues.
    """
    if not isinstance(day_num, int) or not 1 <= day_num <= 4:
         return "Error: Invalid Day Number calculated."

    clean_shift = clean_input(shift_str)
    if not clean_shift:
        return "Error: Shift name input cannot be empty."

    parts = clean_shift.split()
    shift_name = parts[0]

    # --- Handle potential MD/APP suffixes (ignore them for rotation lookup) ---
    core_parts = parts[:] # Create a copy to modify
    if len(core_parts) > 1 and core_parts[-1] in ["md", "app"]:
        core_parts.pop() # Remove the last element if it's md or app

    num_str = "" # For Gold/Silver
    suffix = "" # For YPBB/Green

    if len(core_parts) > 1:
        # Check if it's MIST SCU first, as it uses two words
        if core_parts[0] == "mist" and core_parts[1] == "scu":
            shift_name = "mist scu" # Combine for easier lookup
            # Suffix here might be a number like '1' or '2' which we ignore for MIST SCU rotation
        else:
            # For others, the number/suffix is typically the second part
            suffix = core_parts[1] # Use for YPBB/Green
            num_str = core_parts[1] # Use for Gold/Silver

    # --- Determine Shift Type based on rules ---

    # Gold Shifts
    if shift_name == "gold":
        if not num_str: return f"Error: Shift '{shift_str}' needs a number (e.g., Gold 3)."
        try:
            num = int(num_str)
            if num <= 0: return f"Error: Gold shift number in '{shift_str}' must be positive."
            if num == 1: return "Early"
            if num >= 6: return "Middle"
            if 2 <= num <= 5:
                return GOLD_ROTATION.get(num, {}).get(day_num, f"Internal Error: Missing Gold {num} Day {day_num} rule.")
            return f"Error: Invalid Gold shift number {num}." # Should be caught above
        except ValueError:
            return f"Error: Invalid number '{num_str}' in Gold shift '{shift_str}'."

    # Silver Shifts
    elif shift_name == "silver":
        num = 1 # Default if no number provided
        if num_str:
             try:
                 num = int(num_str)
                 if num <= 0: return f"Error: Silver shift number in '{shift_str}' must be positive."
             except ValueError:
                 return f"Error: Invalid number '{num_str}' in Silver shift '{shift_str}'."
        if num == 1: return "Early"
        if num >= 2: return "Middle"
        return f"Error: Invalid Silver shift number {num}." # Should be caught above

    # Yellow, Purple, Blue, Bronze Shifts
    elif shift_name in ["yellow", "purple", "blue", "bronze"]:
        if not suffix: return f"Error: {shift_name.capitalize()} shift '{shift_str}' needs a suffix (e.g., 1-1, 2-2, 3)."
        if suffix not in YPBB_SUFFIX_ROTATION:
            return f"Error: Invalid suffix '{suffix}' for {shift_name.capitalize()} shift. Use 1-1, 1-2, 2-1, 2-2, or 3."
        shift_type = YPBB_SUFFIX_ROTATION[suffix].get(day_num)
        if shift_type:
             # Format output as requested
             return f"{shift_type} for APP/TML, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"
        else:
             return f"Internal Error: Missing {shift_name.capitalize()} {suffix} Day {day_num} rule."

    # Green Shifts
    elif shift_name == "green":
        if not suffix: return f"Error: Green shift '{shift_str}' needs a suffix (1, 2, or 3)."
        if suffix not in GREEN_SUFFIX_ROTATION:
             return f"Error: Invalid suffix '{suffix}' for Green shift. Use 1, 2, or 3."
        shift_type = GREEN_SUFFIX_ROTATION[suffix].get(day_num)
        if shift_type:
             # Format output as requested
             return f"{shift_type} for APP, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"
        else:
             return f"Internal Error: Missing Green {suffix} Day {day_num} rule."

    # MIST SCU Shifts
    elif shift_name == "mist scu":
        shift_type = MIST_SCU_ROTATION.get(day_num)
        if shift_type:
             # Format output as requested (adapting slightly for clarity)
             return f"{shift_type} for MIST SCU, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"
        else:
            return f"Internal Error: Missing MIST SCU Day {day_num} rule."

    # If none of the above match, return None for generic handling
    else:
        return None


# --- Streamlit User Interface ---

st.title("Shift Day Number and Type Calculator")

# Updated description
st.markdown(f"""
Calculates the **Day Number (1-4)** based on a known reference date.

Determines the shift timing (Early/Middle/Late) for **Gold, Silver, Yellow, Purple, Blue, Bronze, Green,** and **MIST SCU** lines based on the Day Number and specific line rules.

""")

# Input Widgets
input_date = st.date_input("Select the date:")

# Updated example text
input_shift_raw = st.text_input("Enter shift (e.g., Gold 5, Silver, Blue 1-1, Green 3, MIST SCU 1):")

# Button to trigger calculation
if st.button("Calculate Day Number & Shift Type"):
    # Validate inputs exist
    if not input_shift_raw:
        st.warning("Please enter a shift name.")
    elif input_date is None:
         st.warning("Please select a date.")
    else:
        # Perform calculations
        try:
            day_num = get_day_number(input_date)
            result = get_shift_type_or_info(input_shift_raw, day_num) # Pass raw input

            # Display Results
            st.subheader("--- Result ---")
            st.write(f"**Date:** {input_date.strftime('%A, %B %d, %Y')}")
            st.write(f"**Calculated Day Number:** {day_num}")
            st.write(f"**Input Shift:** {input_shift_raw}")

            if result is None: # Unhandled shift type
                st.info(f"This is Day {day_num}. For '{input_shift_raw}', "
                        "refer to the most updated scheduling details to determine the shift timing.")
            elif isinstance(result, str):
                if result.startswith("Error:"):
                    st.error(result) # Display errors clearly
                else: # Success (specific formatted string or Early/Middle/Late for G/S)
                    st.success(f"Determined Shift Info: {result}") # Use success box for all valid outputs

        except Exception as e:
            # Catch any unexpected errors during calculation
            st.error(f"An unexpected error occurred during calculation: {e}")

st.markdown("---") # Visual separator
# Updated caption
st.caption("Calculates day number and shift timing for specified lines")