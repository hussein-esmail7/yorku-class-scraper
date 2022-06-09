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
bool_run_in_background  = False
target_site             = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/1/wo/o8OnkyYDyavkUersg4PShg/0.3.10.21"
BOOL_DEV_PRINTS         = False
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
    options = Options()
    if bool_run_in_background:
        options.add_argument("--headless")  # Adds the argument that hides the window
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
        print(f"\t{num+1}. {item.text}")
    # Asks what semester they want to iterate.
    # If the user wants to iterate multiple semesters, they would have to run
    # this program multiple times
    num_semester = ask_int("Which semester to iterate:")

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
        course_choice = input(f"{str_prefix_q} Type 2-4 letter code to index a specific course, or ENTER to list codes: ").strip()
        if course_choice.upper() == "EXIT" or course_choice.upper() == "QUIT":
            # If the user wants to exit the program
            sys.exit()
        elif course_choice.upper() in course_codes_all:
            int_course_code_choice = course_codes_all.index(course_choice.upper())
            if int_course_code_choice != -1:
                bool_valid_input = True
        elif len(course_choice) == 0:
            for num, item in enumerate(list_depts):
                print(f"\t{item.text}")
        else:
            print(f"{str_prefix_err} '{course_choice}' is not a valid input!")

    # Select the course code from the Select box
    list_depts_box.select_by_value(str(int_course_code_choice))
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
    arr_courses = [] # Dictionary entries will be stored here
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
        print(f"{str_prefix_info} {num+1}/{len(arr_courses)} ({int(round((num+1)/len(arr_courses)*100, 0))}%) - {course_entry['Code']} {course_entry['Num']}")
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
        #   "Num_Studios": How many studios there are in the week (SDIO?)
        #   - TODO: More info about SDIOs
        # }
        for course_section in course_entry_page_table:
            # Each course section
            temp_section = {} # Temporary dict. Will add to array when done
            temp_section["Term"] = course_section.find_element(By.XPATH, ".//td/table/tbody/tr[1]/td[1]/span/span").text.split(" ")[1] # F/W/SU/etc
            temp_section["Code"] = course_section.find_element(By.XPATH, ".//td/table/tbody/tr[1]/td[1]/span").text.split(" ")[-1] # Section (A/B/C/M/N)
            temp_section["LECT"] = []
            temp_section["TUTR"] = []
            temp_section["LAB"] = []
            temp_section["SDIO"] = []
            course_section_table = course_section.find_elements(By.XPATH, ".//td/table/tbody/tr[3]/td/table/tbody/tr") # List of LECT/TUTR/Lab/etc.
            for course_section_part in course_section_table[1:-1]:
                # First entry is the column names
                table_main = course_section_part.find_elements(By.XPATH, ".//td")
                temp_type = table_main[0].text.split(" ")[0]
                if temp_type in ["LECT", "LAB", "TUTR", "BLEN", "SDIO"]:
                    # If it's a valid type
                    subtable_location = course_section_table[1].find_elements(By.XPATH, ".//td[2]/table/tbody/tr")
                    if BOOL_DEV_PRINTS:
                        print(f"{str_prefix_info}\t\ttable_main:")
                        for num3, item3 in enumerate(table_main):
                            print(f"\t\t\t{num3}: {item3.text}")

                    # Calculate how many meeting times there are
                    num_meeting = (len(table_main) - 5) /4
                    # However many items there are depends on the typ
                    # If LECT, as many lectures there are in that week
                    # If TUTR, likely only 1
                    # If LAB, likely only 1
                    # TODO: SDIO
                    for subtable_entry in subtable_location:
                        if course_section_table[3].text != "Cancelled":
                            subtable_items = subtable_entry.find_elements(By.XPATH, ".//td")
                            temp_entry = {}
                            temp_entry["Day"] = subtable_items[0].text
                            temp_entry["Time"] = subtable_items[1].text
                            temp_entry["Duration"] = subtable_items[2].text
                            temp_entry["Location"] = ' '.join(subtable_items[3].text.split())
                            if temp_type == "LECT":
                                temp_section["Profs"] = table_main[-3].text.strip() # Equivalent to TA for TUTR and LAB
                                temp_section["LECT"].append(temp_entry)
                            elif temp_type == "TUTR":
                                temp_entry["CAT"] = table_main[-3].text
                                temp_entry["TA"] = table_main[-2].text.strip()
                                temp_entry["Num"] = table_main[0].text.split(" ")[-1]
                                temp_section["TUTR"].append(temp_entry)
                            elif temp_type == "LAB":
                                temp_entry["CAT"] = table_main[-3].text
                                temp_entry["TA"] = table_main[-2].text.strip()
                                temp_entry["Num"] = table_main[0].text.split(" ")[-1]
                                temp_section["LAB"].append(temp_entry)
                            elif temp_type == "SDIO":
                                # TODO
                                temp_section["SDIO"].append(temp_entry)

            # NOTE: End of loop
            arr_courses[num]["Sections"].append(temp_section)

    # Output JSON
    final = json.dumps(arr_courses, indent=4)
    open("test.json", "w").writelines(final)
    # TODO: Let user pick file name or calculate based on the chosen course code

    # Cleanup
    driver.close()  # Close the browser
    options.extensions.clear() # Clear the options that were set
    sys.exit() # Exit the program

if __name__ == "__main__":
    main()
