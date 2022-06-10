'''
yorku_scrape.py
Hussein Esmail
Created: 2022 06 08
Updated: 2022 06 08
Description: [DESCRIPTION]
'''

import json     # Used to parse output
import os
import re       # Used to separate some data
import sys      # Used to exit the program
import time     # Used for time delays
from selenium import webdriver
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options # Used to add aditional settings (ex. run in background)
from selenium.webdriver.chrome.service import Service # Used to set Chrome location
from selenium.webdriver.common.action_chains import ActionChains # To scroll down to an element in a Select menu
from selenium.webdriver.common.by import By # Used to determine type to search for (normally By.XPATH)
from selenium.webdriver.support.ui import Select # To select items from a menu
# from selenium.webdriver.common.keys import Keys  # Used for pressing special keys, like 'enter'

# ========= VARIABLES ===========
bool_run_in_background  = True
target_site             = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/1/wo/o8OnkyYDyavkUersg4PShg/0.3.10.21"
BOOL_DEV_PRINTS         = False # Unnaturally verbose, maybe too much
BOOL_QUIET              = False # TODO: Unused. Implement this
BOOL_NO_COLOR           = False

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


def main():
    FILENAME_OUTPUT = "test.json" # Default file name. Program asks user later
    arr_course_code_choices = [] # Indexes of the course codes the user wants
    # Ex. If there are 100 options in SU 2022, and the user wants EECS which is
    # the 13th option (starting at 1), the entry here would be 12 (because the
    # real array starts at 0).
    arr_courses_all = [] # All JSON data of every course will end up here.
    # This array will be our final JSON file
    options = Options() # Used so we can add the run-in-background option
    if bool_run_in_background:
        options.add_argument("--headless")  # Hides the window
    service = Service(ChromeDriverManager(log_level=0).install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(400, 1000) # Window size
    driver.get(target_site)
    try:
        driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td/a[1]").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/p/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/ul/li[1]/ul/li[1]/a").click()
    except NoSuchElementException:
        pass

    # Select the box where you can pick the semesters (FW 2021-22, SU 22, etc.)
    list_semesters_box = Select(driver.find_element(By.ID, "sessionSelect"))
    list_semesters = driver.find_element(By.ID, "sessionSelect").find_elements(By.XPATH, ".//*")
    # Print the options and ask the user which one they want
    print(f"{str_prefix_info} Semesters list")
    for num, item in enumerate(list_semesters):
        print(f"\t  {num+1}. {item.text}")
    # Asks what semester they want to iterate.
    # If the user wants to iterate multiple semesters, they would have to run
    # this program multiple times
    num_semester = ask_int("Which semester to iterate:") # Starts at 1
    # Convert the selected option's text to get the year
    # Formats:
    #   "Summer 2022"
    #   "Fall/Winter 2021-2022"
    # .split("-") is there in case a FW option is selected, need to calculate
    #   which semester is needed per section of a course (can be offered in
    #   both semesters).
    semester_year = list_semesters[num_semester-1].text.split(" ")[-1].split("-")

    list_semesters_box.select_by_value(str(num_semester-1))
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
        elif course_choices[0].upper() == "ALL":
            arr_course_code_choices = list(range(len(course_codes_all)))
            bool_valid_input = True
        else:
            for course_choice in course_choices:
                if course_choice.upper() in course_codes_all:
                    arr_course_code_choices.append(course_codes_all.index(course_choice.upper()))
                    if arr_course_code_choices[0] != -1:
                        bool_valid_input = True
                elif len(course_choice) == 0:
                    for num, item in enumerate(list_depts):
                        print(f"\t  {item.text}")
                else:
                    print(f"{str_prefix_err} '{course_choice}' is not a valid input!")
    # Ask the usre what they want the output file name to be
    confirmed_filename = False
    while not confirmed_filename:
        FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.json` file: ")
        if not FILENAME_OUTPUT.endswith(".json"):
            FILENAME_OUTPUT = FILENAME_OUTPUT + ".json"
        confirmed_filename = yes_or_no(f"Is '{FILENAME_OUTPUT}' correct? ")
    # Iterate through every course choice
    for course_iteration_num, course_number in enumerate(arr_course_code_choices):
        arr_courses = [] # Dictionary entries will be stored here per course code
        # Added to arr_courses_all at the end of every loop iteration
        if len(arr_course_code_choices) != 1 and not BOOL_QUIET:
            print(f"{str_prefix_info} Starting {course_codes_all[course_number]} courses - {course_iteration_num+1}/{len(arr_course_code_choices)} ({int(round(((course_iteration_num+1)/(len(arr_course_code_choices)))*100, 0))}%)")
        # Go back to the main site and pick the next course
        if course_iteration_num != 0:
            driver.get(target_site)
            try:
                driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td/a[1]").click()
                time.sleep(2)
                driver.find_element(By.XPATH, "/html/body/p/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/ul/li[1]/ul/li[1]/a").click()
            except NoSuchElementException:
                pass
            # Select the box where you can pick the semesters (FW 2021-22, SU 22, etc.)
            list_semesters_box = Select(driver.find_element(By.ID, "sessionSelect"))
            list_semesters_box.select_by_value(str(num_semester-1))
            # Find the semester option box
            list_depts_box_orig = driver.find_element(By.ID, "subjectSelect")
            # Convert the semester option box to something interactable
            list_depts_box = Select(list_depts_box_orig)
        # Select the course code from the Select box
        list_depts_box.select_by_value(str(course_number))
        time.sleep(0.5) # Just in case
        # Press the "Search Courses" button
        button_submit = driver.find_element(By.XPATH, "/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td/form/table/tbody/tr[3]/td[2]/input").click()
        time.sleep(3) # Wait for the course code index page to load

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
        table_courses_list = table_courses.find_elements(By.XPATH, ".//tr")
        # First entry is the column names (index 0)
        for num, item in enumerate(table_courses_list[1:]):
            course_info = item.find_elements(By.XPATH, ".//td")
            # course_info[0]: Course code info "LE/EECS 1001 1.00" (example)
            # course_info[1]: Course title
            # course_info[2]: URL (inside <a> element)
            # course_info[3]: Irrelevent (under "General Education Details" column)
            info_split = re.search(r"(..)\/(....) (....) (.).(..)", course_info[0].text)
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

        for num, course_entry in enumerate(arr_courses):
            if not BOOL_QUIET:
                print(f"\t  {course_entry['Code']} {course_entry['Num']} - {num+1}/{len(arr_courses)} ({int(round((num+1)/len(arr_courses)*100, 0))}%)")
            # Each individual course page
            driver.get(course_entry["URL"]) # Go to the course page
            time.sleep(3) # Wait for the page to load
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
            #   "LECT": Array of dicts for lectures in the week
            #   {
            #       "Day": Weekday (single letter, MTWRF)
            #       "Time": Start time, in 24h. Ex: 14:30 is 2:30pm
            #       "Duration": In minutes
            #       "Location": Building + Room
            #   }
            #   "TUTR": Array of dicts for tutorials in the week
            #   - NOTE: If it says "Cancelled" in the CAT column, don't add
            #   {
            #       "CAT": If there is a CAT associated to this course row
            #       "Day": Weekday (single letter, MTWRF)
            #       "Time": Start time, in 24h. Ex: 14:30 is 2:30pm
            #       "Duration": In minutes
            #       "Location": Building + Room
            #       "TA": TA of this course
            #       "Num": Tutorial number, if you want a specific tutorial
            #   }
            #   "LAB": How many labs there are in the week (LAB)
            #   - NOTE: If it says "Cancelled" in the CAT column, don't add
            #   {
            #       "CAT": If there is a CAT associated to this course row
            #       "Day": Weekday (single letter, MTWRF)
            #       "Time": Start time, in 24h. Ex: 14:30 is 2:30pm
            #       "Duration": In minutes
            #       "Location": Building + Room
            #       "TA": TA of this course
            #       "Num": Lab number, if you want a specific lab
            #   }
            #   "SEMR": How many seminars there are in the week (SEMR)
            #   - NOTE: If it says "Cancelled" in the CAT column, don't add
            #   {
            #       "CAT": If there is a CAT associated to this course row
            #       "Day": Weekday (single letter, MTWRF)
            #       "Time": Start time, in 24h. Ex: 14:30 is 2:30pm
            #       "Duration": In minutes
            #       "Location": Building + Room
            #       "TA": TA of this course
            #       "Num": Seminar number, if you want a specific seminar
            #   }
            #   "Num_Studios": How many studios there are in the week (SDIO?)
            #   - TODO: More info about SDIOs
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
                temp_section["LECT"] = []
                temp_section["TUTR"] = []
                temp_section["LAB"] = []
                temp_section["SDIO"] = []
                temp_section["SEMR"] = []
                course_section_table = course_section.find_elements(By.XPATH, ".//td/table/tbody/tr[3]/td/table/tbody/tr") # List of LECT/TUTR/Lab/etc.
                if BOOL_DEV_PRINTS:
                    print(f"\t\t\tStarting iteration for Section {temp_section['Code']}")
                    print(f"\t\t\t{len(course_section_table)} - course_section_table length")
                # for course_section_part in course_section_table[1:-1]:
                for course_section_part in course_section_table[1:]:
                    # First entry is the column names
                    table_main = course_section_part.find_elements(By.XPATH, ".//td")
                    temp_type = table_main[0].text.split(" ")[0]
                    if BOOL_DEV_PRINTS:
                        print(f"\t\t\tType: {temp_type}")
                    if temp_type in ["LECT", "LAB", "TUTR", "BLEN", "SDIO", "SEMR"]:
                        # If it's a valid type
                        subtable_location = course_section_part.find_elements(By.XPATH, ".//td[2]/table/tbody/tr")
                        if BOOL_DEV_PRINTS:
                            print(f"{str_prefix_info}\t\ttable_main:")
                            for num3, item3 in enumerate(table_main):
                                print(f"\t\t\t{num3}: {item3.text}")

                        # Calculate how many meeting times there are
                        num_meeting = (len(table_main) - 5) /4
                        if BOOL_DEV_PRINTS:
                            print(f"\t\t\t{num_meeting} meetings")
                        # However many items there are depends on the typ
                        # If LECT, as many lectures there are in that week
                        # If TUTR, likely only 1
                        # If LAB, likely only 1
                        # TODO: SDIO
                        for subtable_entry in subtable_location:
                            if table_main[-3].text != "Cancelled":
                                subtable_items = subtable_entry.find_elements(By.XPATH, ".//td")
                                temp_entry = {}
                                if BOOL_DEV_PRINTS:
                                    for test_item in subtable_items:
                                        print(f"\t\t\t - {test_item.text}")
                                temp_entry["Day"] = subtable_items[0].text
                                temp_entry["Time"] = subtable_items[1].text
                                temp_entry["Duration"] = subtable_items[2].text
                                temp_entry["Location"] = ' '.join(subtable_items[3].text.split())
                                if temp_type == "LECT":
                                    temp_section["Profs"] = table_main[-3].text.strip() # Equivalent to TA for TUTR and LAB
                                    temp_section["LECT"].append(temp_entry)
                                elif temp_type == "SDIO":
                                    # TODO
                                    temp_section["SDIO"].append(temp_entry)
                                else:
                                    # TUTR, LAB, SEMR
                                    temp_entry["CAT"] = table_main[-3].text
                                    temp_entry["TA"] = table_main[-2].text.strip()
                                    temp_entry["Num"] = table_main[0].text.split(" ")[-1]
                                    temp_section[temp_type].append(temp_entry)

                # NOTE: End of loop
                arr_courses[num]["Sections"].append(temp_section)
        arr_courses_all = arr_courses_all + arr_courses # Add the course code you just did to all course codes

    # Output JSON
    final = json.dumps(arr_courses_all, indent=4)
    open(FILENAME_OUTPUT, "w").writelines(final)

    # Cleanup
    driver.close()  # Close the browser
    options.extensions.clear() # Clear the options that were set
    sys.exit() # Exit the program

if __name__ == "__main__":
    main()
