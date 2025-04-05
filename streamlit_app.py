# File: streamlit_app.py (Version with Colored Lines, Special Blue Period, and Gray/MIST Transplant)

import streamlit as st
import re
from datetime import datetime, date, timedelta

# --- Configuration ---
ANCHOR_DATE = date(2025, 3, 12)
ANCHOR_DAY_NUM = 3  # March 12, 2025 is Day 3

# --- Special Date Range for Blue Line ---
SPECIAL_BLUE_START_DATE = date(2025, 4, 7)
SPECIAL_BLUE_END_DATE = date(2025, 5, 2)

# --- Rotation Definitions ---

GOLD_ROTATION = {
    # Gold Num: {DayNum: ShiftType}
    2: {1: 'Early', 2: 'Middle', 3: 'Late', 4: 'Middle'},
    3: {1: 'Middle', 2: 'Late', 3: 'Middle', 4: 'Early'},
    4: {1: 'Late', 2: 'Middle', 3: 'Early', 4: 'Middle'},
    5: {1: 'Middle', 2: 'Early', 3: 'Middle', 4: 'Late'},
}

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
# Define sets for easier lookup based on the full, cleaned identifier
GRAY_MIST_EARLY_ON_1_3 = {"gray 1 md", "mist transplant"}
GRAY_MIST_MIDDLE_ON_1_3 = {"gray 2 md", "gray 3 app"}
ALL_GRAY_MIST_ROLES = GRAY_MIST_EARLY_ON_1_3.union(GRAY_MIST_MIDDLE_ON_1_3)

# --- Helper Functions ---

def clean_input(text):
    """Removes extra spaces, converts to lowercase, removes commas."""
    if not isinstance(text, str):
        return ""
    text = text.strip().lower().replace(',', '')
    text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with single space
    return text

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
    # Note: This is for MIST SCU, not MIST Transplant which has its own logic now
    return f"{shift_type} for MIST SCU, MD is fixed 8 am - 5 pm (4 pm weekends/holidays)"

def get_shift_type_or_info(shift_str, day_num, target_dt):
    """
    Determines shift type/info based on shift string, day number, and target date.
    Handles Gold, Silver, Yellow, Purple, Blue, Bronze, Green, MIST SCU, Gray, MIST Transplant.
    Includes special logic for Blue line during a specific period.
    Returns formatted string for known lines, None for others, error strings for issues.
    """
    if not isinstance(day_num, int) or not 1 <= day_num <= 4:
         return "Error: Invalid Day Number calculated."
    if not isinstance(target_dt, date):
         return "Error: Internal - Target date missing for shift calculation."

    clean_shift = clean_input(shift_str)
    if not clean_shift:
        return "Error: Shift name input cannot be empty."

    # --- Early Check for Specific Multi-Word Shifts (Gray/MIST Transplant/MIST SCU) ---
    # We check these first as their full names are the identifiers.
    if clean_shift in ALL_GRAY_MIST_ROLES:
        shift_type = None
        if clean_shift in GRAY_MIST_EARLY_ON_1_3:
            if day_num in [1, 3]:
                shift_type = "Early"
            elif day_num in [2, 4]:
                shift_type = "Middle"
        elif clean_shift in GRAY_MIST_MIDDLE_ON_1_3:
            if day_num in [1, 3]:
                shift_type = "Middle"
            elif day_num in [2, 4]:
                shift_type = "Early"

        if shift_type:
            return shift_type # Return *only* the shift type as requested
        else:
            # Should not happen with valid day_num
            return f"Internal Error: Missing Gray/MIST Transplant rule for '{clean_shift}' Day {day_num}."

    elif clean_shift.startswith("mist scu"): # Handle "MIST SCU" potentially followed by ignored number/suffix
        shift_name_for_lookup = "mist scu"
        shift_type = MIST_SCU_ROTATION.get(day_num)
        if shift_type:
             # Use specific formatter for MIST SCU
             return format_md_app_mist_scu_output(shift_type)
        else:
            return f"Internal Error: Missing MIST SCU Day {day_num} rule."

    # --- Process remaining shifts (split into parts) ---
    parts = clean_shift.split()
    shift_name = parts[0]

    # Handle potential MD/APP suffixes (ignore them for rotation lookup)
    core_parts = parts[:] # Create a copy to modify
    if len(core_parts) > 1 and core_parts[-1] in ["md", "app"]:
        core_parts.pop() # Remove the last element if it's md or app

    num_str = "" # For Gold/Silver
    suffix = "" # For YPBB/Green/Blue

    # Extract suffix/number if present (excluding the already handled multi-word shifts)
    if len(core_parts) > 1:
        # For others, the number/suffix is typically the second part
        potential_second_part = core_parts[1]
        # Need to decide if it's a number (Gold/Silver) or suffix (YPBB/Green/Blue)
        # We'll assign to both and let the specific logic below decide
        num_str = potential_second_part
        suffix = potential_second_part

    # --- Determine Shift Type based on remaining rules ---

    # Gold Shifts
    if shift_name == "gold":
        if not num_str: return f"Error: Shift '{shift_str}' needs a number (e.g., Gold 3)."
        try:
            num = int(num_str)
            if num <= 0: return f"Error: Gold shift number in '{shift_str}' must be positive."
            if num == 1: return "Early"
            if num >= 6: return "Middle"
            if 2 <= num <= 5:
                # Return only shift type for Gold
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
                 # If suffix exists but isn't a valid number, treat as Silver 1 (Early)
                 # or potentially error? Let's default to Silver 1 for now if just "Silver" or "Silver APP" etc.
                 # If it's like "Silver abc", let the num=1 logic handle it.
                 pass # Keep num = 1
        if num == 1: return "Early" # Return only shift type for Silver
        if num >= 2: return "Middle" # Return only shift type for Silver
        # This part should not be reachable if logic above is correct
        # return f"Error: Invalid Silver shift number {num}."

    # Blue Shifts (Check for special period first)
    elif shift_name == "blue":
        if not suffix: return f"Error: Blue shift '{shift_str}' needs a suffix."

        # --- Special Blue Period Logic ---
        if SPECIAL_BLUE_START_DATE <= target_dt <= SPECIAL_BLUE_END_DATE:
            special_blue_suffixes = ["1", "3-1", "3-2"]
            if suffix not in special_blue_suffixes:
                return f"Error: Invalid suffix '{suffix}' for Blue shift during {SPECIAL_BLUE_START_DATE.strftime('%Y-%m-%d')} to {SPECIAL_BLUE_END_DATE.strftime('%Y-%m-%d')}. Use 1, 3-1, or 3-2."

            shift_type = None
            if suffix == "1":
                if day_num in [1, 3]: shift_type = "Early"
                elif day_num in [2, 4]: shift_type = "Middle"
            elif suffix in ["3-1", "3-2"]:
                if day_num in [1, 3]: shift_type = "Middle"
                elif day_num in [2, 4]: shift_type = "Early"

            if shift_type:
                return format_md_app_output(shift_type) # Use standard formatting
            else:
                 return f"Internal Error: Missing Special Blue {suffix} Day {day_num} rule."

        # --- Standard Blue Period Logic ---
        else:
            if suffix not in YPBB_SUFFIX_ROTATION:
                return f"Error: Invalid suffix '{suffix}' for Blue shift (standard period). Use 1-1, 1-2, 2-1, 2-2, or 3."
            shift_type = YPBB_SUFFIX_ROTATION[suffix].get(day_num)
            if shift_type:
                 return format_md_app_output(shift_type) # Use standard formatting
            else:
                 return f"Internal Error: Missing Blue {suffix} Day {day_num} rule (standard period)."

    # Yellow, Purple, Bronze Shifts (Use standard YPBB logic)
    elif shift_name in ["yellow", "purple", "bronze"]:
        if not suffix: return f"Error: {shift_name.capitalize()} shift '{shift_str}' needs a suffix (e.g., 1-1, 2-2, 3)."
        if suffix not in YPBB_SUFFIX_ROTATION:
            return f"Error: Invalid suffix '{suffix}' for {shift_name.capitalize()} shift. Use 1-1, 1-2, 2-1, 2-2, or 3."
        shift_type = YPBB_SUFFIX_ROTATION[suffix].get(day_num)
        if shift_type:
             return format_md_app_output(shift_type) # Use standard formatting
        else:
             return f"Internal Error: Missing {shift_name.capitalize()} {suffix} Day {day_num} rule."

    # Green Shifts
    elif shift_name == "green":
        if not suffix: return f"Error: Green shift '{shift_str}' needs a suffix (1, 2, or 3)."
        if suffix not in GREEN_SUFFIX_ROTATION:
             return f"Error: Invalid suffix '{suffix}' for Green shift. Use 1, 2, or 3."
        shift_type = GREEN_SUFFIX_ROTATION[suffix].get(day_num)
        if shift_type:
             return format_md_app_green_output(shift_type) # Use Green specific formatting
        else:
             return f"Internal Error: Missing Green {suffix} Day {day_num} rule."

    # If Gray but didn't match specific roles above (e.g., "Gray 4", "Gray")
    elif shift_name == "gray":
        return f"Error: Unknown Gray shift role '{shift_str}'. Use 'Gray 1 MD', 'Gray 2 MD', or 'Gray 3 APP'."

    # If none of the above match, return None for generic handling
    else:
        return None


# --- Streamlit User Interface ---

st.title("Shift Day Number and Type Calculator")

# Updated description
st.markdown(f"""
Calculates the **Day Number (1-4)** based on a known reference date.

Determines the shift timing (Early/Middle/Late) for **Gold, Silver, Yellow, Purple, Blue, Bronze, Green, Gray, MIST SCU,** and **MIST Transplant** lines based on the Day Number and specific line rules.

*Last updated 4/5/25: Added gray and MIST transplant. Added special rules to the **Blue** line between **{SPECIAL_BLUE_START_DATE.strftime('%Y-%m-%d')}** and **{SPECIAL_BLUE_END_DATE.strftime('%Y-%m-%d')}**.*
""")

# Input Widgets
input_date = st.date_input("Select the date:", value=date.today()) # Default to today

# Updated example text
input_shift_raw = st.text_input("Enter shift (e.g., Gold 5, Silver, Blue 1-1, Green 3, Gray 1 MD, MIST Transplant):")

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
            # Pass the input_date to the calculation function
            result = get_shift_type_or_info(input_shift_raw, day_num, input_date)

            # Display Results
            st.subheader("--- Result ---")
            st.write(f"**Date:** {input_date.strftime('%A, %B %d, %Y')}")
            st.write(f"**Calculated Day Number:** {day_num}")
            st.write(f"**Input Shift:** {input_shift_raw}")

            if result is None: # Unhandled shift type
                st.info(f"This is Day {day_num}. For '{input_shift_raw}', "
                        "refer to the most updated scheduling details or check spelling/format.")
            elif isinstance(result, str):
                if result.startswith("Error:"):
                    st.error(result) # Display errors clearly
                else: # Success (specific formatted string or Early/Middle/Late)
                    # Check if the result is *just* Early/Middle/Late (Gold, Silver, Gray, MIST Transplant)
                    is_simple_result = result in ["Early", "Middle", "Late"]
                    # Check if the date is within the special Blue period for potential extra info label
                    is_special_blue = clean_input(input_shift_raw).startswith("blue") and SPECIAL_BLUE_START_DATE <= input_date <= SPECIAL_BLUE_END_DATE

                    output_label = "Determined Shift Info"
                    if is_special_blue:
                        output_label += " (Special Blue Period)"
                    elif clean_input(input_shift_raw) in ALL_GRAY_MIST_ROLES:
                         output_label += " (Gray/MIST Tx Rotation)" # Optional label for clarity

                    # Use success box for all valid outputs
                    st.success(f"{output_label}: {result}")

        except TypeError as te:
            # Catch specific internal errors like missing date object
             st.error(f"An internal error occurred: {te}")
        except Exception as e:
            # Catch any other unexpected errors during calculation
            st.error(f"An unexpected error occurred during calculation: {e}")

st.markdown("---") # Visual separator
# Updated caption
st.caption(f"Calculates day number and shift timing for specified lines. Special Blue rules apply {SPECIAL_BLUE_START_DATE.strftime('%m/%d/%y')} - {SPECIAL_BLUE_END_DATE.strftime('%m/%d/%y')}. Gray/MIST Transplant follow specific MD/APP rotation.")