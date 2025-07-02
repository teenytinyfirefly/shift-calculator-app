# File: streamlit_app.py (Full Version with New Blue Line Special Periods)

import streamlit as st
import re
from datetime import datetime, date, timedelta

# --- Configuration ---
ANCHOR_DATE = date(2025, 7, 1)
ANCHOR_DAY_NUM = 2  # July 1, 2025 is Day 2

# --- Special Date Ranges for Blue Line ---
# A list of tuples, where each tuple is a (start_date, end_date) for a special period.
SPECIAL_BLUE_PERIODS = [
    (date(2025, 7, 7),  date(2025, 8, 3)),
    (date(2025, 9, 29), date(2025, 10, 26)),
    (date(2026, 1, 5),  date(2026, 2, 1)),
    (date(2026, 4, 6),  date(2026, 5, 3)),
]

# --- Rotation Definitions ---

# Yellow, Purple, Blue (Standard), Bronze use the same suffix pattern
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

# Gray and MIST Transplant Rotation Definition
GRAY_MIST_EARLY_ON_1_3 = {"gray 1 md", "mist transplant"}
GRAY_MIST_MIDDLE_ON_1_3 = {"gray 2 md", "gray 3 app"}
ALL_GRAY_MIST_ROLES = GRAY_MIST_EARLY_ON_1_3.union(GRAY_MIST_MIDDLE_ON_1_3)

# --- Helper Functions ---

def clean_input(text):
    """Removes extra spaces, converts to lowercase, removes commas."""
    if not isinstance(text, str):
        return ""
    text = text.strip().lower().replace(',', '')
    text = re.sub(r'\s+', ' ', text)
    return text

def is_in_special_blue_period(target_dt):
    """Checks if a date falls within any of the special Blue line periods."""
    for start_date, end_date in SPECIAL_BLUE_PERIODS:
        if start_date <= target_dt <= end_date:
            return True
    return False

# --- Core Calculation Functions ---

def get_day_number(target_dt):
    """Calculates the day number (1-4) for a given date."""
    if not isinstance(target_dt, date):
        raise TypeError("Internal Error: Input must be a date object.")
    delta_days = (target_dt - ANCHOR_DATE).days
    return (delta_days + ANCHOR_DAY_NUM - 1) % 4 + 1

def format_md_app_output(shift_type):
    """Helper to format the output string for lines with standard MD/APP distinction."""
    return f"{shift_type} for APP/TML, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"

def format_md_app_green_output(shift_type):
    """Helper to format the output string for Green line."""
    return f"{shift_type} for APP, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"

def format_md_app_mist_scu_output(shift_type):
    """Helper to format the output string for MIST SCU line."""
    return f"{shift_type} for MIST SCU, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"

def get_shift_type_or_info(shift_str, day_num, target_dt):
    """
    Determines shift type/info based on shift string, day number, and target date.
    Handles all lines with their specific rules.
    """
    if not isinstance(day_num, int) or not 1 <= day_num <= 4:
         return "Error: Invalid Day Number calculated."
    if not isinstance(target_dt, date):
         return "Error: Internal - Target date missing for shift calculation."

    clean_shift = clean_input(shift_str)
    if not clean_shift:
        return "Error: Shift name input cannot be empty."

    # --- Early Check for Specific Multi-Word Shifts ---
    if clean_shift in ALL_GRAY_MIST_ROLES:
        shift_type = None
        if clean_shift in GRAY_MIST_EARLY_ON_1_3:
            if day_num in [1, 3]: shift_type = "Early"
            elif day_num in [2, 4]: shift_type = "Middle"
        elif clean_shift in GRAY_MIST_MIDDLE_ON_1_3:
            if day_num in [1, 3]: shift_type = "Middle"
            elif day_num in [2, 4]: shift_type = "Early"
        return shift_type if shift_type else f"Internal Error: Missing Gray/MIST Transplant rule for '{clean_shift}' Day {day_num}."

    elif clean_shift.startswith("mist scu"):
        shift_type = MIST_SCU_ROTATION.get(day_num)
        return format_md_app_mist_scu_output(shift_type) if shift_type else f"Internal Error: Missing MIST SCU Day {day_num} rule."

    # --- Process remaining shifts (split into parts) ---
    parts = clean_shift.split()
    shift_name = parts[0]
    core_parts = parts[:]
    if len(core_parts) > 1 and core_parts[-1] in ["md", "app"]:
        core_parts.pop()

    num_str = ""
    suffix = ""
    if len(core_parts) > 1:
        num_str = core_parts[1]
        suffix = core_parts[1]

    # --- Determine Shift Type based on rules ---

    # Gold Shifts (NEW ACADEMIC YEAR 2025-2026)
    if shift_name == "gold":
        if not num_str: return f"Error: Shift '{shift_str}' needs a number (e.g., Gold 3)."
        try:
            num = int(num_str)
            if num <= 0: return f"Error: Gold shift number in '{shift_str}' must be positive."

            if num == 1:
                return "Early"
            if num >= 6:
                return "Middle"
            if num in [3, 5]:  # Gold 3 and Gold 5
                return "Early" if day_num in [1, 3] else "Middle"
            if num in [2, 4]:  # Gold 2 and Gold 4
                return "Middle" if day_num in [1, 3] else "Early"

            return f"Error: Invalid or unhandled Gold shift number {num}."
        except ValueError:
            return f"Error: Invalid number '{num_str}' in Gold shift '{shift_str}'."

    # Silver Shifts
    elif shift_name == "silver":
        num = 1
        if num_str:
             try:
                 num = int(num_str)
                 if num <= 0: return f"Error: Silver shift number in '{shift_str}' must be positive."
             except ValueError:
                 pass
        if num == 1: return "Early"
        if num >= 2: return "Middle"

    # Blue Shifts (Check for special period first)
    elif shift_name == "blue":
        if not suffix: return f"Error: Blue shift '{shift_str}' needs a suffix."
        
        # Check if the date falls into any of the special periods
        if is_in_special_blue_period(target_dt):
            special_blue_suffixes = ["1", "3-1", "3-2"]
            if suffix not in special_blue_suffixes:
                return f"Error: Invalid suffix '{suffix}' for Blue shift during special period. Use 1, 3-1, or 3-2."
            shift_type = None
            if suffix == "1":
                if day_num in [1, 3]: shift_type = "Early"
                elif day_num in [2, 4]: shift_type = "Middle"
            elif suffix in ["3-1", "3-2"]:
                if day_num in [1, 3]: shift_type = "Middle"
                elif day_num in [2, 4]: shift_type = "Early"
            return format_md_app_output(shift_type) if shift_type else f"Internal Error: Missing Special Blue {suffix} Day {day_num} rule."
        
        # --- Standard Blue Period Logic ---
        else:
            if suffix not in YPBB_SUFFIX_ROTATION:
                return f"Error: Invalid suffix '{suffix}' for Blue shift (standard period). Use 1-1, 1-2, 2-1, 2-2, or 3."
            shift_type = YPBB_SUFFIX_ROTATION[suffix].get(day_num)
            return format_md_app_output(shift_type) if shift_type else f"Internal Error: Missing Blue {suffix} Day {day_num} rule."

    # Yellow, Purple, Bronze Shifts
    elif shift_name in ["yellow", "purple", "bronze"]:
        if not suffix: return f"Error: {shift_name.capitalize()} shift '{shift_str}' needs a suffix (e.g., 1-1, 2-2, 3)."
        if suffix not in YPBB_SUFFIX_ROTATION:
            return f"Error: Invalid suffix '{suffix}' for {shift_name.capitalize()} shift. Use 1-1, 1-2, 2-1, 2-2, or 3."
        shift_type = YPBB_SUFFIX_ROTATION[suffix].get(day_num)
        return format_md_app_output(shift_type) if shift_type else f"Internal Error: Missing {shift_name.capitalize()} {suffix} Day {day_num} rule."

    # Green Shifts
    elif shift_name == "green":
        if not suffix: return f"Error: Green shift '{shift_str}' needs a suffix (1, 2, or 3)."
        if suffix not in GREEN_SUFFIX_ROTATION:
             return f"Error: Invalid suffix '{suffix}' for Green shift. Use 1, 2, or 3."
        shift_type = GREEN_SUFFIX_ROTATION[suffix].get(day_num)
        return format_md_app_green_output(shift_type) if shift_type else f"Internal Error: Missing Green {suffix} Day {day_num} rule."

    elif shift_name == "gray":
        return f"Error: Unknown Gray shift role '{shift_str}'. Use 'Gray 1 MD', 'Gray 2 MD', or 'Gray 3 APP'."

    else:
        return None


# --- Streamlit User Interface ---

st.title("HMU Shift Calculator")

st.markdown(f"""
Calculates the **day number (1-4)** based on a known reference date (7/1/25 is day 2).

Determines the shift timing for **Gold, Silver, Yellow, Purple, Blue, Bronze, Green, Gray, MIST SCU,** and **MIST Transplant** lines based on the day number and specific line rules.

*Last updated 7/2/25: revised gold schedule and added new special blue periods with medical students for the 2025-2026 academic year.*
            
""")

input_date = st.date_input("Select the date:", value=date.today())
input_shift_raw = st.text_input("Enter shift (e.g., Gold 5, Silver, Blue 1-1, Green 3, Gray 1 MD, MIST Transplant):")

if st.button("Calculate Day Number & Shift Type"):
    if not input_shift_raw:
        st.warning("Please enter a shift name.")
    elif input_date is None:
         st.warning("Please select a date.")
    else:
        try:
            day_num = get_day_number(input_date)
            result = get_shift_type_or_info(input_shift_raw, day_num, input_date)

            st.subheader("--- Result ---")
            st.write(f"**Date:** {input_date.strftime('%A, %B %d, %Y')}")
            st.write(f"**Calculated Day Number:** {day_num}")
            st.write(f"**Input Shift:** {input_shift_raw}")

            if result is None:
                st.info(f"This is Day {day_num}. For '{input_shift_raw}', "
                        "refer to the most updated scheduling details or check spelling/format.")
            elif isinstance(result, str):
                if result.startswith("Error:"):
                    st.error(result)
                else:
                    st.success(f"Determined Shift Info: {result}")

        except Exception as e:
            st.error(f"An unexpected error occurred during calculation: {e}")

st.markdown("---")
st.caption(f"Calculates day number and shift timing for specified lines. Special blue rules apply during specific periods (July 7 - Aug 3 2025, Sept 29 - Oct 26 2025, Jan 5 - Feb 1 2026, and April 6 - May 3 2026). *If any questions or concerns, reach out to melu@mgb.org*")