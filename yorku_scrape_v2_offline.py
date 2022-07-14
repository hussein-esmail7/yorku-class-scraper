'''
yorku_scrape.py
Hussein Esmail
Created: 2022 06 08
Updated: 2022 06 24
Description: [DESCRIPTION]
'''

import json     # Used to parse output
import os
import re       # Used to separate some data
import sys      # Used to exit the program
import time     # Used for tracking how long the program is taking
from selenium import webdriver
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options # Used to add aditional settings (ex. run in background)
from selenium.webdriver.chrome.service import Service # Used to set Chrome location
from selenium.webdriver.common.action_chains import ActionChains # To scroll down to an element in a Select menu
from selenium.webdriver.common.by import By # Used to determine type to search for (normally By.XPATH)
from selenium.webdriver.support.ui import Select # To select items from a menu

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
    # INT_PROGRESS_BAR_LEN
    if BOOL_PROGRESS:
        color_prog = color_red # Color to show when in progress
        color_done = color_green # Color to show when complete
        color_prog = color_end # Color to show when in progress
        color_done = color_end # Color to show when complete
        window_width = os.get_terminal_size().columns
        if INT_PROGRESS_BAR_LEN > (window_width - 21):
            # If the window width is smaller, shrink the max bar length
            INT_PROGRESS_BAR_LEN = window_width - 21
        percent = ((progress) / float(total)) * 100 # Always out of 100 since this is for the number percentage
        percent_bar = ((progress) / float(total)) * INT_PROGRESS_BAR_LEN # Formatted to width
        bar = '\u2588' * int(percent_bar) + '-' * (INT_PROGRESS_BAR_LEN - int(percent_bar))
        print(f"\r|{color_prog}{bar}{color_end}|{percent:.2f}% - {msg}{' '*(10-len(msg))}", end="\r")
        if progress == total:
            print(f"\r|{color_done}{bar}{color_end}|{percent:.2f}%" + " "*13)

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

def time_str(convert):
    # This function inputs a number in seconds, and returns a string of how to
    # print it (including units). This is so that you don't have something like
    # "2000s remaining"
    if convert >= 60:
        # If a minute or more remaining
        str_return = ""
        hours = int(convert/3600)
        if hours != 0:
            convert = convert - (hours * 3600)
            str_return += f"{hours}h "
        minutes = int(convert/60)
        if minutes != 0:
            convert = convert - (minutes * 60)
            str_return += f"{minutes}m "
        return str_return + f"{convert}s"
    else:
        # If there is less than a minute remaining, only return seconds
        return str(int(convert)) + "s"

def main():
    BOOL_QUIET = True
    BOOL_PROGRESS              = True # False if user turns off progress bars
    FILENAME_OUTPUT = "" # JSON output file name. Changed by user later
    term_use = "" # User selected term to get. Choice required when empty
    times = [] # Runtimes for each course
    html_folder = os.path.expanduser("~/git/yorku-class-scraper/html/")
    row_multiplier = 0.25 # Roughly how long the program takes to process 1 row (in seconds)
    # Local file paths
    spreadsheet_urls = [f"file://{html_folder}" + i for i in os.listdir(html_folder)]
    all_rows = [] # Row text will be placed here

    # USER ARGUMENT PARSING
    args = sys.argv
    if len(args) > 1:
        # args[0] = file name, ignore this
        for arg_num, arg in enumerate(args[1:]):
            if arg == "-h" or arg == "--help":
                print("--- yorku-class-scraper ---")
                print("https://github.com/hussein-esmail7/yorku-class-scraper\n")
                print("Arguments:")
                print("\t-h, --help\tHelp message and exit program.")
                print("\t-o, --output\tInput the output JSON file name as a string.")
                print("\t-c, --code\tInput the course code(s) you want to get (Example: EECS, ADMS, EN, ENG, etc.)")
                print("\t-s, --sem, --semester\n\t\t\tInput the semester you want as a string (Example: FW, SU)")
                print("\t-q, --quiet\tQuiet mode. Only display text when required (progress bars not included, use `--no-progress` for this).")
                print("\t--no-progress\tNo progress bars. Independent from `--quiet`.")
                sys.exit()
            elif arg == "-o" or arg == "--output": # .json file name
                # User inputs the JSON location in the next arg
                FILENAME_OUTPUT = args[arg_num+2]
                if os.path.exists(os.path.expanduser(FILENAME_OUTPUT)):
                    # If JSON not found, reset the variable to ask again later
                    print(f"{str_prefix_err} JSON file already exists!")
                    FILENAME_OUTPUT = ""
            elif arg == "-s" or arg == "--sem" or arg == "--semester":
                # User inputs the semester they want in the next arg
                term_use = valid_sem(args[arg_num+2])
            elif arg == "-q" or arg == "--quiet":
                BOOL_QUIET = True
            elif arg == "--no-progress":
                BOOL_PROGRESS = False


    # Ask the user what they want the output file name to be
    while len(FILENAME_OUTPUT) == 0:
        FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.json` file: ")
        if len(FILENAME_OUTPUT) > 0:
            if not FILENAME_OUTPUT.endswith(".json"):
                FILENAME_OUTPUT = FILENAME_OUTPUT + ".json"
            if not yes_or_no(f"Is '{FILENAME_OUTPUT}' correct? "):
                FILENAME_OUTPUT = ""

    bool_print_times = yes_or_no("Print times after file is done? ")

    if not BOOL_QUIET:
        print(f"{str_prefix_info} Starting...")
    # START WEB SCRAPER
    options = Options() # Used so we can add the run-in-background option
    if bool_run_in_background:
        options.add_argument("--headless")  # Hides the window
    try:
        # This line won't work if you don't have internet
        service = Service(ChromeDriverManager(log_level=0).install())
        driver = webdriver.Chrome(service=service, options=options)
    except:
        driver = webdriver.Chrome(options=options)
        pass
    # driver.set_window_size(400, 1000) # Window size
    driver.implicitly_wait(15) # Timeout 10s when getting any element or page
    # Go to the main page with all the view options like timetable, exam
    # schedule, etc.

    # Used for progress bar
    total_progress = 0 # Addition of all row numbers for all spreadsheets
    progress_current = 0 # What row number out of all spreadsheets you're on
    for url in spreadsheet_urls:
        driver.get(url)
        trs = driver.find_elements(By.XPATH, "/html/body/table/tbody/tr")[1:]
        total_progress += len(trs)
    print(f"{str_prefix_info} {total_progress} rows, ~{time_str(int(total_progress*row_multiplier))}")

    # Actually iterate the tables
    for url in spreadsheet_urls:
        # print(f"\t  Getting {url.split('/')[-1].split('.')[0]}...")
        driver.get(url)
        """
        Columns:
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
        trs = driver.find_elements(By.XPATH, "/html/body/table/tbody/tr")[1:]
        # "[1:]" explanation: Column names row, not actually part of courses
        for num, tr in enumerate(trs):
            progress_current += 1
            t_start = time.time() # Documentation purposes, resetting timer
            all_rows.append([cell.text for cell in tr.find_elements(By.XPATH, "td")])
            times.append(f"{time.time() - t_start}") # Documentation purposes
            time_estimate = time_str(int(round((total_progress - progress_current) * row_multiplier, 0)))
            progress_bar(BOOL_PROGRESS, INT_PROGRESS_BAR_LEN, progress_current, total_progress, time_estimate)
            # print(f"Time for row {num}: {round(time.time() - t_start, 2)}s")
            # print(row_text)
        # print(all_rows)
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
            if not row[0] == "The course timetables for this Faculty have not been released yet.":
                if not BOOL_QUIET:
                    print(f"ROW: {len(row)}, {row}")
                if len(row) == 9 and "Cancelled" not in row[5]:
                    # Lecture type (not counting TUTR)
                    # It is a course row that is not cancelled
                    # 0: Nothing
                    # 1: 4 numbers + Credits (_.__ format) + Section
                    # 2: Language
                    # 3: Type (LECT, ONLN, etc.)
                    # 4: Type Num
                    # 5: CAT or "Cancelled" (with space, make sure to strip)
                    # 6: Day + Time + Duration + Room (single day, each entry is a different day, never 2 days in same row)
                    # 7: Day
                    # 8: Time
                    # 9: Duration
                    # 10: Building + Room
                    # 11: Instructor
                    # 12: Course outline URL
                    row[1] = row[1].replace("  ", " ") # Replace double spaces
                    row[4] = row[4].replace("  ", " ") # Replace double spaces
                    row[5] = row[5].replace("  ", " ") # Replace double spaces
                    row[6] = row[6].replace("  ", " ") # Replace double spaces

                    current_section = row[1].strip().split(" ")[-1] # A, B, etc.
                    meet_times_unformatted = row[6].split("\n")
                    for item in meet_times_unformatted:
                        if row[3] == "ONLN":
                            # Online course has less parameters
                            course_duration = "0"
                            course_time = "0:00"
                            course_location = ""
                            course_day = ""
                        else:
                            course_duration = item.split(" ")[2]
                            course_time = item.split(" ")[1]
                            course_location = " ".join(item.split(" ")[3:])
                            course_day = item.split(" ")[0]
                        course_current["Num"] = row[1].strip().split(" ")[0] # 4 digits
                        course_current["Credits"] = row[1].strip().split(" ")[1] # _.__
                        course_current["Language"] = row[2] # Language taught (ex. EN)
                        course_current["Meetings"].append({
                            "Section": current_section,
                            "Type": row[3].strip(), # LECT, ONLN, etc.
                            "CAT": row[5].strip(), # 6 characters
                            "Day": course_day.strip(), # "M", "T", "W", "R", "F" (only 1)
                            "Time": course_time.strip(), # Ex. "13:00"
                            "Duration": course_duration.strip(), # Ex. "180" (minutes)
                            "Location": course_location.strip(), # Ex. "DB 0011"
                            "Instructor": row[7].strip() # Prof/TA name
                        })
                elif ( row[1].strip() == "TUTR" or row[1].strip() == "LAB" ) and "Cancelled" not in row[3]:
                    # TUTR or LAB
                    row[0] = row[0].replace("  ", " ") # Replace double spaces
                    row[1] = row[1].replace("  ", " ") # Replace double spaces
                    row[2] = row[2].replace("  ", " ") # Replace double spaces
                    row[3] = row[3].replace("  ", " ") # Replace double spaces
                    row[4] = row[4].replace("  ", " ") # Replace double spaces
                    row[5] = row[5].replace("  ", " ") # Replace double spaces
                    row[6] = row[6].replace("  ", " ") # Replace double spaces
                    meet_times_unformatted = row[4].split("\n")
                    for item in meet_times_unformatted:
                        course_duration = item.split(" ")[2]
                        course_time = item.split(" ")[1]
                        course_location = " ".join(item.split(" ")[3:])
                        course_day = item.split(" ")[0]
                        course_current["Meetings"].append({
                            "Section": current_section,
                            "Type": row[1].strip(),
                            "Num": row[2].strip(),
                            "CAT": row[3].strip(), # 6 characters
                            "Day": course_day.strip(), # "M", "T", "W", "R", "F" (only 1)
                            "Time": course_time.strip(), # Ex. "13:00"
                            "Duration": course_duration.strip(), # Ex. "180" (minutes)
                            "Location": course_location.strip(), # Ex. "DB 0011"
                            "Instructor": row[5].strip() # Prof/TA name
                        })
                else:
                    # It is a 'title' row
                    # Add the previous course as it is now done
                    # (if there was a previous)
                    if course_current != {} and len(course_current["Meetings"]) > 0:
                        # If it is not empty and has meeting occurences
                        all_courses.append(course_current)
                        if not BOOL_QUIET:
                            print(course_current)
                    course_current = {} # Reset the working variable
                    current_dept = row[0] # AP, LE, GS, etc.
                    current_code = row[1] # ADMS, EECS, ENG, etc.
                    current_term = row[2] # F, Y, W, SU, S1, etc.
                    current_title = row[3] # Course title for the rows below
                    course_current["Department"] = row[0].strip()
                    course_current["Code"] = row[1].strip() # ADMS, EECS, ENG, etc.
                    course_current["Term"] = row[2].strip() # F, W, Y, S1, etc.
                    course_current["Title"] = row[3].strip() # Title for rows below
                    # Below: Resetting for the course rows
                    course_current["Num"] = "" # The "1001" from "EECS 1001"
                    course_current["Credits"] = "" # _.__ format
                    course_current["Language"] = "" # Language course is taught in
                    course_current["Meetings"] = [] # Individual time occurences
                    current_section = "" # A, B, C, Z, etc.
        else:
            pass
    # Output JSON
    final = json.dumps(all_courses, indent=4)
    open(FILENAME_OUTPUT, "w").writelines(final)
    if not BOOL_QUIET:
        print(f"{str_prefix_done} JSON file written: {FILENAME_OUTPUT}")

    if bool_print_times:
        print("\n".join(times))

    # Cleanup
    driver.close()  # Close the browser
    options.extensions.clear() # Clear the options that were set
    sys.exit() # Exit the program
    # NOTE: END OF PROGRAM

    """
    else:
        while not bool_valid_input:
            # Keeps asking for input until it receives a valid input, or "exit"
            # Stripped in case they add beginning or trailing whitespace in input
            # Split by space so that you can select multiple course codes at once
            # Example: EECS and MATH but nothing else
            # EXIT|QUIT: Exits program
            # ALL: Gets all course codes of that semester
                # If the user wants to exit the program
                sys.exit()
            else:
                if len(course_choice) == 0:
                    for num, item in enumerate(list_depts):
                        print(f"\t  {item.text}")
                else:
                    bool_valid_input = True


            # At this point, the department page contains a large table with each
            # course, title, and URL. This section gets the table data and puts it into
            # an array of dictionary entries. 1 dictionary is 1 course
            # Dictionary format:
            # {
            #   "Department": 2 letters, LE, AP, GS, etc.
            #   "Code": 2-4 letters, "VISA", "ADMS", "EECS", etc.
            #   "Num": 4 numbers, like the "1001" in EECS 1001 (as string)
            #   "Credits": Number including the decimals as a string
            #       - NOTE/TODO: Later, find out if the numbers after the decimal mean
            #           anything by searching all the courses
            #   "Title": Course title
            #   "URL": Course URL
            #   "Description": Course description
            #   "Sections": Course sections, it's own array. Will be explained later
            # }
            table_courses = driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/table[2]/tbody")
            table_courses_list = table_courses.find_elements(By.XPATH, ".//tr")[1:]
            # [1:] in table_courses_list -> First entry is the column names (index 0)
            for num, item in enumerate(table_courses_list):
                course_info = item.find_elements(By.XPATH, ".//td")
                # course_info[0]: Course code info "LE/EECS 1001 1.00" (example)
                # course_info[1]: Course title
                # course_info[2]: URL (inside <a> element)
                # course_info[3]: Irrelevent (under "General Education Details" column)
                info_split = re.search(r"(..)\/(.{2,4}) (....) (.).(..)", course_info[0].text)
                # "(.{2,4})" instead of "(....)" because a course code can be
                # 2-4 letters. "(....)" only accepts 4-letter codes
                # print(f"{num} {course_info[0].text}")
                if info_split is not None:
                    course_url = course_info[2].find_element(By.XPATH, ".//a").get_attribute("href")
                    arr_courses.append({
                            "Department":   info_split.group(1),
                            "Code":         info_split.group(2),
                            "Num":          info_split.group(3),
                            "Credits":      info_split.group(4),
                            "Title":        course_info[1].text,
                            "URL":          course_url,
                            "Description":  "", # To be added later
                            "Sections": [] # To be added later
                        })
        except NoSuchElementException:
            pass # Table not found, meaning this is an empty course page
        except Exception as e:
            # Some other error
            print(f"{str_prefix_err} {course_codes_all[course_number]}: Could not get courses!")
            progress_bar(BOOL_PROGRESS, course_iteration_num, len(course_choices), course_codes_all[course_number])
    progress_bar(BOOL_PROGRESS, len(course_choices), len(course_choices), "")
    if not BOOL_QUIET:
        print(f"{str_prefix_info} Getting information from each course URL...")
    progress_bar(BOOL_PROGRESS, 0, len(arr_courses), arr_courses[0]["Code"] + " " + arr_courses[0]["Num"])
    for num, course_entry in enumerate(arr_courses):
        # if not BOOL_QUIET:
        # Each individual course page
        try:
            t_s = time.time()
            driver.get(course_entry["URL"]) # Go to the course page
            course_entry_page_main = driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td")
            arr_courses[num]["Description"] = course_entry_page_main.find_elements(By.XPATH, ".//p")[4].text # Add course description to entry dictionary
            course_entry_page_table = course_entry_page_main.find_elements(By.XPATH, ".//table[2]/tbody/*") # Number of elements = number of sections during this term
            # "Sections" portion of arr_courses:
            # {
            #   "Term": F/W/SU/S1/etc.
            #   "Code": Course section code, single letter
            #       - NOTE: SU/F sections start at A, W starts at M
            #   "Profs": Array. Who is teaching the LECTURES ONLY. Possibly
            #       multiple
            #   "CAT": CAT Code.
            #       - NOTE: If there is more than 1 tutorial in this course,
            #               have "-1" here, because then it is tutorial-specific
            #   "Meetings": Array of occurences for lectures, tutorials, labs, etc.
            #   {
            #       "Type": "LECT", "TUTR", "LAB", "BLEN", etc.
            #       "CAT": If there is a CAT associated to this course row
            #           NOTE: If "Cancelled" in the CAT column, don't add
            #       "Day": Weekday (single letter, MTWRF)
            #       "Time": Start time, in 24h. Ex: 14:30 is 2:30pm
            #       "Duration": In minutes
            #       "Location": Building + Room
            #       "TA": TA of this course
            #       "Num": Tutorial number, if you want a specific tutorial
            #   }
            # }
            for course_section in course_entry_page_table:
                # Each course section
                temp_section = {} # Temporary dict. Will add to array when done
                temp_section["Term"] = course_section.find_element(By.XPATH, ".//td/table/tbody/tr[1]/td[1]/span/span").text.split(" ")[1] # F/W/SU/etc
                temp_section["Year"] = semester_year[0]
                if temp_section["Term"] == "W":
                    temp_section["Year"] = semester_year[1]
                # temp_section["Year"] = course_section.find_element(By.XPATH, ".//td/table/tbody/tr[1]/td[1]/span/span").text.split(" ")[1] # F/W/SU/etc
                temp_section["Code"] = course_section.find_element(By.XPATH, ".//td/table/tbody/tr[1]/td[1]/span").text.split(" ")[-1] # Section (A/B/C/M/N)
                temp_section["Meetings"] = []
                course_section_table = course_section.find_elements(By.XPATH, ".//td/table/tbody/tr[3]/td/table/tbody/tr") # List of LECT/TUTR/Lab/etc.
                if BOOL_DEV_PRINTS:
                    print(f"\t\t\tStarting iteration for Section {temp_section['Code']}")
                    print(f"\t\t\t{len(course_section_table)} - course_section_table length")
                # for course_section_part in course_section_table[1:-1]:
                for course_section_part in course_section_table[1:]:
                    # First entry is the column names
                    table_main = course_section_part.find_elements(By.XPATH, ".//td")
                    temp_type = table_main[0].text.split(" ")[0].strip()
                    # If it's a valid type
                    subtable_location = course_section_part.find_elements(By.XPATH, ".//td[2]/table/tbody/tr")
                    if BOOL_DEV_PRINTS:
                        print(f"{str_prefix_info}\t\ttable_main:")
                        for num3, item3 in enumerate(table_main):
                            print(f"\t\t\t{num3}: {item3.text}")
                    # Calculate how many meeting times there are
                    num_meeting = (len(table_main) - 5) /4
                    print_dev(f"{num_meeting} meetings")
                    # However many items there are depends on the type
                    # If LECT, as many lectures there are in that week
                    # If TUTR, likely only 1
                    # If LAB, likely only 1
                    for subtable_entry in subtable_location:
                        if table_main[-3].text != "Cancelled":
                            subtable_items = subtable_entry.find_elements(By.XPATH, ".//td")
                            temp_entry = {}
                            if BOOL_DEV_PRINTS:
                                for test_item in subtable_items:
                                    print(f"\t\t\t - {test_item.text}")
                            temp_entry["Type"] = temp_type
                            temp_entry["Day"] = subtable_items[0].text.strip()
                            temp_entry["Time"] = subtable_items[1].text.strip()
                            temp_entry["Duration"] = subtable_items[2].text.strip()
                            temp_entry["Location"] = ' '.join(subtable_items[3].text.split()).strip()
                            temp_entry["CAT"] = table_main[-3].text.strip()
                            temp_entry["TA"] = table_main[-2].text.strip()
                            temp_entry["Num"] = table_main[0].text.split(" ")[-1].strip()
                            temp_section["Meetings"].append(temp_entry)
                # NOTE: End of loop
                arr_courses[num]["Sections"].append(temp_section)
            t_e = time.time()
            times.append(t_e - t_s)
        except: # Unable to get course
            pass
        try:
            # Put into try/catch since you are getting the next index, since
            # this will fail at the last index
            progress_bar(BOOL_PROGRESS, num+1, len(arr_courses), arr_courses[num+1]["Code"] + " " + arr_courses[num+1]["Num"])
        except IndexError:
            pass
    progress_bar(BOOL_PROGRESS, len(arr_courses), len(arr_courses), "")

    # Output JSON
    final = json.dumps(arr_courses, indent=4)
    open(FILENAME_OUTPUT, "w").writelines(final)

    # Cleanup
    driver.close()  # Close the browser
    options.extensions.clear() # Clear the options that were set
    sys.exit() # Exit the program
    """

if __name__ == "__main__":
    main()
