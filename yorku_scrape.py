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
target_site             = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/1/wo/o8OnkyYDyavkUersg4PShg/0.3.10.21"
BOOL_DEV_PRINTS         = False # Unnaturally verbose, maybe too much
BOOL_NO_COLOR           = False
INT_PROGRESS_BAR_LEN    = 50 # TODO: Unused. Implement this

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


def verify_course_choices(choices, all_course_options):
    choices_good = []
    if len(choices) > 0:
        if choices[0].upper() == "ALL":
            choices_good = list(range(len(all_course_options)))
        else:
            for course_choice in choices:
                if course_choice.upper() in all_course_options:
                    choices_good.append(all_course_options.index(course_choice.upper()))
                else:
                    print(f"{str_prefix_err} '{course_choice}' is not a valid input!")
    return choices_good


def progress_bar(BOOL_PROGRESS, progress, total, msg):
    if BOOL_PROGRESS:
        color_prog = color_red # Color to show when in progress
        color_done = color_green # Color to show when complete
        color_prog = color_end # Color to show when in progress
        color_done = color_end # Color to show when complete
        percent = ((progress) / float(total)) * 100
        bar = '\u2588' * int(percent) + '-' * (100 - int(percent))
        print(f"\r|{color_prog}{bar}{color_end}|{percent:.2f}% - {msg}", end="\r")
        if progress == total:
            print(f"\r|{color_done}{bar}{color_end}|{percent:.2f}%" + " "*10)


def print_dev(str):
    if BOOL_DEV_PRINTS:
        print(f"\t\t\t{str}")


def ask_int(question):
    bool_continue_asking_q = True
    ans = ""
    while bool_continue_asking_q:
        ans = input(f"{str_prefix_q} {question} ")
        try:
            ans = int(ans.strip())
            if ans < 1:
                print(f"{str_prefix_err} Must be a positive number!")
            else:
                bool_continue_asking_q = False
        except:
            print(f"{str_prefix_err} Input a number and no other characters!")
    return ans


def valid_sem(str_in):
    opts_y = ["FW", "Y", "F", "W"]
    opts_s = ["SU", "S1", "S2"]
    if str_in.upper() in opts_y:
        return "Fall/Winter"
    elif str_in.upper() in opts_s:
        return "Summer"
    else:
        print(f"{str_prefix_err} `-s` command options: {opts_y + opts_s}")
    return ""

def main():
    course_choices = [] # Course department options to get (EECS, ADMS, EN, etc.)
    BOOL_QUIET              = False
    BOOL_PROGRESS              = True # False if user turns off progress bars
    num_courses_get = 0 # Number of courses to download
    FILENAME_OUTPUT = "" # JSON output file name. Changed by user later
    course_choices = [] # Indexes of the course codes the user wants
    # Ex. If there are 100 options in SU 2022, and the user wants EECS which is
    # the 13th option (starting at 1), the entry here would be 12 (because the
    # real array starts at 0).
    arr_courses = [] # All JSON data of every course will end up here.
    term_use = "" # User selected term to get. Choice required when empty
    times = [] # Runtimes for each course

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
            elif arg == "-c" or arg == "--code":
                course_choices = args[arg_num+2].strip().split(" ")

            elif arg == "-s" or arg == "--sem" or arg == "--semester":
                # User inputs the semester they want in the next arg
                term_use = valid_sem(args[arg_num+2])
            elif arg == "-q" or arg == "--quiet":
                BOOL_QUIET = True
            elif arg == "--no-progress":
                BOOL_PROGRESS = False


    # START WEB SCRAPER
    options = Options() # Used so we can add the run-in-background option
    if bool_run_in_background:
        options.add_argument("--headless")  # Hides the window
    service = Service(ChromeDriverManager(log_level=0).install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(400, 1000) # Window size
    driver.implicitly_wait(15) # Timeout 10s when getting any element or page
    driver.get(target_site)
    try:
        driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td/a[1]").click()
        driver.find_element(By.XPATH, "/html/body/p/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/ul/li[1]/ul/li[1]/a").click()
    except NoSuchElementException:
        pass

    # Select the box where you can pick the semesters (FW 2021-22, SU 22, etc.)
    list_semesters_box = Select(driver.find_element(By.ID, "sessionSelect"))
    list_semesters = driver.find_element(By.ID, "sessionSelect").find_elements(By.XPATH, ".//*")
    # Asks what semester they want to iterate.
    if term_use == "":
        # Print the options and ask the user which one they want
        print(f"{str_prefix_info} Semesters list")
        for num, item in enumerate(list_semesters):
            print(f"\t  {num+1}. {item.text}")
        # If the user wants to iterate multiple semesters, they would have to run
        # this program multiple times
        num_semester = ask_int("Which semester to iterate:") -1
        # Convert the selected option's text to get the year
        # Formats:
        #   "Summer 2022"
        #   "Fall/Winter 2021-2022"
        # .split("-") is there in case a FW option is selected, need to calculate
        #   which semester is needed per section of a course (can be offered in
        #   both semesters).
    else:
        term_options = [] # Int array of semester indexes
        # This is used in case there are 2 FW options, like during the summer
        for num, item in enumerate(list_semesters):
            if term_use in item.text:
                term_options.append(num)
        if len(term_options) == 0:
            print(f"{str_prefix_err} No {term_use} options available")
        elif len(term_options) > 1:
            print(f"{str_prefix_info} Multiple semester options found!")
            for num, item in enumerate(term_options):
                print(f"\t  {num+1}. {list_semesters[item]}")
            bool_accepted_input = False
            while not bool_accepted_input:
                temp = ask_int("Which semester do you want to use?")
                if len(term_options) > temp:
                    num_semester = term_options[temp]
                    bool_accepted_input = True
                else:
                    print(f"{str_prefix_err} Invalid number!")
        else:
            num_semester = term_options[0]



    semester_year = list_semesters[num_semester].text.split(" ")[-1].split("-")

    list_semesters_box.select_by_value(str(num_semester))
    # Find the semester option box
    list_depts_box_orig = driver.find_element(By.ID, "subjectSelect")
    # Convert the semester option box to something interactable
    list_depts_box = Select(list_depts_box_orig)
    # Get the possible semester values
    list_depts = driver.find_element(By.ID, "subjectSelect").find_elements(By.XPATH, ".//*")
    # Print the options and ask the user which one they want
    bool_valid_input = False
    # 2-4 letter course codes only
    course_codes_all = [code.text.split(" ")[0].upper() for code in list_depts]
    if len(course_choices) != 0: # If courses were already preselected
        course_choices = verify_course_choices(course_choices, course_codes_all)
    else:
        while not bool_valid_input:
            # Keeps asking for input until it receives a valid input, or "exit"
            course_choices = input(f"{str_prefix_q} Type 2-4 letter code to index a specific course, or ENTER to list codes, \"ALL\" for all courses: ").strip().split(" ")
            # Stripped in case they add beginning or trailing whitespace in input
            # Split by space so that you can select multiple course codes at once
            # Example: EECS and MATH but nothing else
            # EXIT|QUIT: Exits program
            # ALL: Gets all course codes of that semester
            if course_choices[0].upper() == "EXIT" or course_choices[0].upper() == "QUIT":
                # If the user wants to exit the program
                sys.exit()
            else:
                course_choices = verify_course_choices(course_choices, course_codes_all)
                if len(course_choice) == 0:
                    for num, item in enumerate(list_depts):
                        print(f"\t  {item.text}")
                else:
                    bool_valid_input = True

    # Ask the usre what they want the output file name to be
    while len(FILENAME_OUTPUT) == 0:
        FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.json` file: ")
        if len(FILENAME_OUTPUT) > 0:
            if not FILENAME_OUTPUT.endswith(".json"):
                FILENAME_OUTPUT = FILENAME_OUTPUT + ".json"
            if not yes_or_no(f"Is '{FILENAME_OUTPUT}' correct? "):
                FILENAME_OUTPUT = ""

    if not BOOL_QUIET:
        print(f"{str_prefix_info} Starting...")
    # Iterate through every course choice
    if not BOOL_QUIET:
        print(f"\t  Getting lists of courses...")
    progress_bar(BOOL_PROGRESS, 0, len(course_choices), course_choices[0])
    for course_iteration_num, course_number in enumerate(course_choices):
        try: # Attempt to get the URL
            # Go back to the main site and pick the next course
            if course_iteration_num != 0:
                driver.get(target_site)
                try:
                    driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td/a[1]").click()
                    driver.find_element(By.XPATH, "/html/body/p/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/ul/li[1]/ul/li[1]/a").click()
                except NoSuchElementException:
                    pass
                # Select the box where you can pick the semesters (FW 2021-22, SU 22, etc.)
                list_semesters_box = Select(driver.find_element(By.ID, "sessionSelect"))
                list_semesters_box.select_by_value(str(num_semester))
                # Find the semester option box
                list_depts_box_orig = driver.find_element(By.ID, "subjectSelect")
                # Convert the semester option box to something interactable
                list_depts_box = Select(list_depts_box_orig)
            # Select the course code from the Select box
            list_depts_box.select_by_value(str(course_number))
            # Press the "Search Courses" button
            button_submit = driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/form/table/tbody/tr[3]/td[2]/input").click()

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
        if len(course_choices) > course_iteration_num + 1:
            progress_bar(BOOL_PROGRESS, course_iteration_num, len(course_choices), course_codes_all[course_number])
    progress_bar(BOOL_PROGRESS, len(course_choices), len(course_choices), "")
    num_courses_get = len(arr_courses)
    if not BOOL_QUIET:
        if num_courses_get != 1:
            print(f"{str_prefix_info} {num_courses_get} courses to get")
        else:
            print(f"{str_prefix_info} {num_courses_get} course to get")
        print(f"{str_prefix_info} Getting information from each course URL...")
    progress_bar(BOOL_PROGRESS, 0, len(arr_courses), arr_courses[0]["Code"] + " " + arr_courses[0]["Num"])
    for num, course_entry in enumerate(arr_courses):
        # if not BOOL_QUIET:
        #     print(f"\t  {course_entry['Code']} {course_entry['Num']} - {num+1}/{num_courses_get} ({int(round((num+1)/num_courses_get*100, 0))}%)")
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

if __name__ == "__main__":
    main()
