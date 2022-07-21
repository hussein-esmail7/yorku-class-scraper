'''
yorku_scrape.py
Hussein Esmail
Created: 2022 06 08
Description: This program converts HTML pages of courses from York University
    to JSON
'''

import json     # Used to parse output
import os
import re       # Used to separate some data
import sys      # Used to exit the program
import time as t # Used for tracking how long the program is taking
from bs4 import BeautifulSoup

# ========= VARIABLES ===========
bool_run_in_background  = True

target_site             = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/5/wo/haRSuBvTH011F9mNuT4260/0.3.10.39"
BOOL_DEV_PRINTS         = False # Unnaturally verbose, maybe too much
BOOL_NO_COLOR           = False
INT_PROGRESS_BAR_LEN    = 50

# ========= COLOR CODES =========
if not BOOL_NO_COLOR:
    color_end               = '\033[0m'
    color_darkgrey          = '\033[90m'
    color_red               = '\033[91m'
    color_green             = '\033[92m'
    color_yellow            = '\033[93m'
    color_blue              = '\033[94m'
    color_pink              = '\033[95m'
    color_cyan              = '\033[96m'
    color_white             = '\033[97m'
    color_grey              = '\033[98m'
else:
    color_end               = ""
    color_darkgrey          = ""
    color_red               = ""
    color_green             = ""
    color_yellow            = ""
    color_blue              = ""
    color_pink              = ""
    color_cyan              = ""
    color_white             = ""
    color_grey              = ""

# ========= COLORED STRINGS =========
str_prefix_q            = f"[{color_pink}Q{color_end}]\t "
str_prefix_y_n          = f"[{color_pink}y/n{color_end}]"
str_prefix_err          = f"[{color_red}ERROR{color_end}]\t "
str_prefix_done         = f"[{color_green}DONE{color_end}]\t "
str_prefix_info         = f"[{color_cyan}INFO{color_end}]\t "
str_prefix_warn         = f"[{color_yellow}WARN{color_end}]\t "
str_prefix_dev          = f"[{color_red}DEV{color_end}]\t "

def nth_occur(input_str, occurence_num, substring_find):
    int_occur = -1
    for i in range(0, occurence_num):
        int_occur = input_str.find(substring_find, int_occur+1)
    return int_occur

def time_location_formatted(input_str):
    """
    0: Weekday
    ":"+2: time
    until letter: duration
    rest: room
    """
    bool_print = False
    input_str_separated = input_str.split(" "*4)
    prof = ""
    to_return = []
    for input_str in input_str_separated:
        input_str = input_str.strip()
        re_match = re.match("([A-Za-z ]+)$", input_str)
        if re_match:
            # If it is a prof and not a time format
            prof = input_str
    for input_str in input_str_separated:
        weekday = ""
        time = ""
        duration = ""
        room = ""
        input_str = input_str.replace("  ", " ").strip()
        re_match = re.match("([MTWRF])(\d{1,2}:\d{2})(\d{2,3})(.*)", input_str)
        if re_match:
            weekday = re_match.group(1)
            time = re_match.group(2)
            duration = re_match.group(3)
            room = re_match.group(4).replace("  ", " ")
            to_return.append([weekday, time, duration, room, prof])
    return to_return

def get_table_contents(filepath):
    if filepath.lower().endswith(".html"):
        index = open(filepath.replace("file://", ""), 'rb').read() # Get contents of file
        S = BeautifulSoup(index, 'lxml') # Make bs4 object using lxml parser
        Attr = S.html.body.table.tbody # Locating table row elements
        # Using the Children attribute to get the children of a tag
        # Only contain tag names and not the spaces
        Attr_Tag = [e.text.replace("\n", "\xa0").split("\xa0") for e in Attr.children if e.name is not None]
        # Attr_Tag = [e.text for e in Attr.children if e.name is not None]
        Attr_Tag.pop(0) # Delete the first row that shows the titles per column
        for num, i in enumerate(Attr_Tag):
            for num_ii, ii in enumerate(Attr_Tag[num]):
                Attr_Tag[num][num_ii] = Attr_Tag[num][num_ii].strip()

            # Delete all empty strings inside each row, so that each element means something
        #     Attr_Tag[num] = [item.strip() for item in Attr_Tag[num] if item != ""]
        if not Attr_Tag[0][0] == "The course timetables for this Faculty have not been released yet.":
            return Attr_Tag
    return []


def yes_or_no(str_ask):
    while True:
        y_n = input(f"{str_prefix_q} {str_prefix_y_n} {str_ask}").lower()
        if len(y_n) == 0: # Add these 2 lines to template
            return True
        if y_n[0] == "y":
            return True
        elif y_n[0] == "n":
            return False
        if y_n[0] == "q":
            sys.exit()
        else:
            print(f"{str_prefix_err} {error_neither_y_n}")

def progress_bar(BOOL_PROGRESS, INT_PROGRESS_BAR_LEN, progress, total, msg):
    if BOOL_PROGRESS:
        color_prog = color_red # Color to show when in progress
        color_done = color_green # Color to show when complete
        color_prog = color_end # Color to show when in progress
        color_done = color_end # Color to show when complete
        window_width = os.get_terminal_size().columns
        if len(msg.strip()) != 0:
            msg = " - " + msg.strip()
        if INT_PROGRESS_BAR_LEN > (window_width - 21):
            # If the window width is smaller, shrink the max bar length
            INT_PROGRESS_BAR_LEN = window_width - 21
        if progress == 0:
            percent = 0
            p_bar = 0
            bar = '-' * (INT_PROGRESS_BAR_LEN)
            print(f"\r|{color_prog}{bar}{color_end}|{percent:.2f}%{msg}{' '*(13-len(msg))}", end="\r")
        else:
            percent = ((progress) / float(total)) * 100
            p_bar = int(((progress) / float(total)) * INT_PROGRESS_BAR_LEN)
            bar = '\u2588' * p_bar + '-' * (INT_PROGRESS_BAR_LEN - p_bar)
            if progress == total:
                print(f"\r|{color_done}{bar}{color_end}|{percent:.2f}%" + " "*13)
            else:
                print(f"\r|{color_prog}{bar}{color_end}|{percent:.2f}%{msg}{' '*(13-len(msg))}", end="\r")

def ask_int(question, max):
    bool_continue_asking_q = True
    ans = ""
    while bool_continue_asking_q:
        ans = input(f"{str_prefix_q} {question} ")
        try:
            ans = int(ans.strip())
            if ans < 1:
                print(f"{str_prefix_err} Must be a positive number!")
            elif ans > max:
                print(f"{str_prefix_err} Your answer cannot exceed {max}!")
            else:
                bool_continue_asking_q = False
        except:
            print(f"{str_prefix_err} Input a number and no other characters!")
    return ans

def get_timetable_online():
    # TODO
    return ""

def main():
    BOOL_QUIET = True
    FILENAME_OUTPUT = "" # JSON output file name. Changed by user later
    runtimes = [] # Runtimes for each course
    # html_folder = os.path.expanduser("~/git/yorku-class-scraper/html/")
    row_multiplier = 0.25 # Roughly how long the program takes to process 1 row (in seconds)
    # Local file paths
    filepaths = [] # Paths of HTML files will be stored here
    all_rows = [] # Row text will be placed here

    # USER ARGUMENT PARSING
    args = sys.argv
    if len(args) > 1:
        # args[0] = file name, ignore this
        for arg_num, arg in enumerate(args[1:]):
            if arg == "-h" or arg == "--help":
                print("--- yorku-class-scraper ---")
                print("https://github.com/hussein-esmail7/yorku-class-scraper")
                print("\nArguments:")
                print("\t-h, --help\tHelp message and exit program.")
                print("\t-i, --input\tInput folder path of HTML files or HTML file path to convert.")
                print("\t-o, --output\tInput JSON file name.")
                print("\t-q, --quiet\tQuiet mode.")
                sys.exit()
            elif arg == "-o" or arg == "--output": # .json file name
                # User inputs the JSON location in the next arg
                FILENAME_OUTPUT = args[arg_num+2]
                if os.path.exists(os.path.expanduser(FILENAME_OUTPUT)):
                    # If JSON not found, reset the variable to ask again later
                    print(f"{str_prefix_err} JSON file already exists!")
                    FILENAME_OUTPUT = ""
            elif arg == "-i" or arg == "--input": # html folder or file input
                # if args[arg_num+2].lower() == "online":
                #     filepaths = get_timetable_online()
                test = os.path.expanduser(args[arg_num+2])
                if os.path.exists(test):
                    if test.lower().endswith(".html"):
                        filepaths = [test]
                    elif os.path.isdir(test):
                        if not test.endswith("/"):
                            test = test + "/"
                        filepaths = [f"file://{test}" + i for i in os.listdir(test)]
                    # Else (file exists but does not meet requirements): No handler needed, program will check `filepaths`
                    # and ask user again anyway
                else:
                    print(f"{str_prefix_err} File/folder path invalid!")
            elif arg == "-q" or arg == "--quiet":
                BOOL_QUIET = True

    elif filepaths == []:
        # If the HTML file(s) haven't been specified in the command line args
        html_path = input(f"{str_prefix_q} Path of HTML file(s) to convert: ").strip()
        html_path = os.path.expanduser(html_path)
        while not os.path.exists(html_path):
            # if args[arg_num+2].lower() == "online":
            #     filepaths = get_timetable_online()
            if html_path.lower() == "exit" or html_path.lower() == "quit":
                sys.exit()
            print(f"{str_prefix_err} File/folder path invalid!")
            html_path = os.path.expanduser(html_path)
        if html_path.lower().endswith(".html"):
            filepaths = [html_path]
        elif os.path.isdir(html_path):
            if not html_path.endswith("/"):
                html_path = html_path + "/"
            filepaths = [f"file://{html_path}" + i for i in os.listdir(html_path)]

    # filepaths = [f"file://{html_folder}" + i for i in os.listdir(html_folder)]

    # Ask the user what they want the output file name to be
    while len(FILENAME_OUTPUT) == 0:
        FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.json` file: ")
        if len(FILENAME_OUTPUT) > 0:
            if not FILENAME_OUTPUT.endswith(".json"):
                FILENAME_OUTPUT = FILENAME_OUTPUT + ".json"
            if not yes_or_no(f"Is '{FILENAME_OUTPUT}' correct? "):
                FILENAME_OUTPUT = ""

    print(f"{str_prefix_info} Running...")
    progress_bar(not BOOL_QUIET, INT_PROGRESS_BAR_LEN, 0, len(all_rows), "")

    # Used for progress bar
    progress_current = 0 # What row number out of all spreadsheets you're on
    for filepath in filepaths:
        trs = get_table_contents(filepath)
        # Column title row (for reference):
        """
        0: 'Fac'
        1: 'Dept'
        2: 'Term'
        3: 'Course ID'
        4: 'LOI'
        5: 'Type'
        6: 'Meet'
        7: 'Cat.No.'
        8: 'DayTimeDurationRoom'
        9: 'Instructors'
        10: 'Notes/Additional Fees'
        11: ''
        """
        all_rows = all_rows + trs
    # Actually iterate the tables
    """
    Columns - OLD:
    1. Faculty (2 letters)
    2. Department (2-4 letters)
    3. Term (1-2 characters)
    4. Course ID (title of new course, else 4 num + credits + section)
    5. LOI: Language of instruction (EN/FR)
    6. Type: LECT/ONLN/LAB/etc
    7. Meet: # of Type. Ex: "01" of "LECT 01"
    8. CAT (6 characters or "Cancelled")
    9. Subtable:
        i.   Day
        ii.  Time
        iii. Duration
        iv.  Room
    10. Instructors
    11. Notes/Additional Fees
    """
    # At this point, you have all table data of the different pages,
    # Now you have to format it to JSON
    # These variables are gotten from each 'title' row
    current_dept = ""
    current_code = ""
    current_term = ""
    current_title = ""
    current_section = "" # Set during lecture and reused when a TUTR happens
    course_current = {} # Started at title row, edited during course rows
    all_courses = []
    for row in all_rows:
        progress_current += 1

        # Title row
        # 0: Empty
        # 1: Faculty
        # 2: Course department code ("EECS", "ADMS", etc.)
        # 3: Term (F, Y, etc.)
        # 4: Course title
        # 5: Empty

        # First entry after title row of a course
        # 0: Empty
        # 1: Empty
        # 2: Empty
        # 3: Course number ("1001" in "EECS 1001")
        # 4: Number of credits ("_.__" format)
        # 5: Course section (A, B, etc.)
        # 6: Empty
        # 7: Language course is taught in ("EN", "FR", etc.)
        # 8: Session Type (LECT, TUTR, SEMR, etc.)
        # 9: Empty
        # 10: Session Type Number ("01" in "LECT 01")
        # 11: Empty
        # 12: Empty
        # 13: Empty
        # 14: Weekday, Time, Duration, Location, Prof
        # 15: Additional Notes
        # 16: Empty

        # nth entry after first entry row of a course
        # 0: Empty
        # 1: Empty
        # 2: Session Type (LECT, TUTR, SEMR, etc.)
        # 3: Empty
        # 4: Session Type Number ("01" in "LECT 01")
        # 5: Empty
        # 6: CAT or "Cancelled"
        # 7: Empty
        # 8: Weekday, Time, Duration, Location, Prof
        # 9: Empty
        # 10: Empty
        # 11: Additional Notes
        # 12: Empty
        if row[3] != "" and row[3].isnumeric() and row[12] != "Cancelled":
            # First entry after title row of a course
            current_section = row[5]
            if row[8] == "ONLN" or len(row[14]) == 0:
                times = [["", "", "", "", ""]]
            else:
                times = time_location_formatted(row[14])
            for time in times:
                course_current["Num"] = row[3] # 4 digits
                course_current["Credits"] = row[4]
                course_current["Language"] = row[7] # Language taught (ex. EN)
                course_current["Meetings"].append({
                    "Section": current_section,
                    "Type": row[8],
                    "Num": row[10],
                    "CAT": row[6],
                    "Day": time[0],
                    "Time": time[1],
                    "Duration": time[2],
                    "Location": time[3],
                    "Instructor": time[4]
                })
        elif row[1] == "" and row[2] != "" and row[6] != "Cancelled":
            # nth entry after first entry row of a course
            # Checks row[1] is empty because otherwise it could be a title row
            # Title rows have text in row[1]
            if row[2] == "ONLN" or len(row[8]) == 0:
                times = [["", "", "", "", ""]]
            else:
                times = time_location_formatted(row[8])
            for time in times:
                course_current["Meetings"].append({
                    "Section": current_section,
                    "Type": row[2],
                    "Num": row[4],
                    "CAT": row[6],
                    "Day": time[0],
                    "Time": time[1],
                    "Duration": time[2],
                    "Location": time[3],
                    "Instructor": time[4]
                })
        elif row[1] != "":
            # Condition: Faculty perameter is not empty
            # Title row
            # Add the previous course as it is now done
            # (if there was a previous)
            if course_current != {} and len(course_current["Meetings"]) > 0:
                # If it is not empty and has meeting occurences
                all_courses.append(course_current)
            course_current = {} # Reset the working variable
            course_current["Department"] = row[1] # AP, LE, GS, FA, etc.
            course_current["Code"] = row[2] # ADMS, EECS, ENG, etc.
            course_current["Term"] = row[3] # F, W, Y, S1, etc.
            course_current["Title"] = row[4] # Title for rows below
            # Below: Resetting for the course rows
            course_current["Num"] = "" # The "1001" from "EECS 1001"
            course_current["Credits"] = "" # _.__ format
            course_current["Language"] = "" # Language course is taught in
            course_current["Meetings"] = [] # Individual time occurences
            current_section = "" # A, B, C, Z, etc.
        progress_bar(not BOOL_QUIET, INT_PROGRESS_BAR_LEN, progress_current, len(all_rows), "")
    # Output JSON
    final = json.dumps(all_courses, indent=4)
    open(FILENAME_OUTPUT, "w").writelines(final)
    if not BOOL_QUIET:
        print(f"{str_prefix_done} JSON file written: {FILENAME_OUTPUT}")

    sys.exit() # Exit the program

if __name__ == "__main__":
    main()
