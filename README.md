# yorku-class-scraper
A Python Selenium program that converts York University course data to JSON

## Table of Contents
- [What is this?](#what-is-this)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Program](#running-the-program)
- [Arguments](#arguments)
	- [What the program asks](#what-the-program-asks)
	- [Command Arguments](#command-arguments)
- [Files in this Repository](#files-in-this-repository)
- [Donate](#donate)

## What is this?
This program outputs a JSON file that is generated by traversing York
University's course website.

## Requirements
Copy and paste this into your Terminal to install the required libraries:
```shell script
pip install bs4 ; pip install configparser
```

## Installation
You can install this program by typing
```shell script
git clone https://github.com/hussein-esmail7/yorku-class-scraper
cd yorku-class-scraper/
```

## Running the program
To use this program, you have to make sure you are in the correct directory
(using the `cd` command).

```shell script
python3 yorku-scrape.py
```

### Arguments
There are two options to input your arguments into this program:
1. When the program asks for it if it is not given in the Terminal, or
2. In the Terminal. See [Command Arguments](#command-arguments) for the ways to
   put it in.


#### What the program asks
1. `HTML File(s) Location`: Where the local HTML files are stored. With the way
   this program is structured, these files have to be offline. To do this,
   press `Ctrl+S` or `Cmd+S` while on each page in the browser, and save them
   to the folder you're going to give the program. If your outputted JSON file
   looks like it is missing courses, try redownloading your HTML files as they
   might not have fully loaded. Tip: Scroll all the way to the bottom of each
   page before you download.
2. `JSON File Name`: This is pretty self-explanatory, but what you want to name
   your output JSON file. This asks before it starts iterating through all the
   courses in case it takes a while so you don't have to sit at your computer
   waiting for it to ask you. At the moment, it only makes a JSON file in the
   same directory as the file.

#### Command Arguments
- `-h`, `--help`: Help message and exit program.
- `-o`, `--output`: Input the output JSON file name as a string.
- `-c`, `--code`: Input the course code(s) you want to get. Examples: EECS,
  ADMS, EN, ENG, etc. if you are inputting multiple, make sure to have it in
  quotations. Examples: "EECS ADMS", "EECS, WRIT"
- `-q`, `--quiet`: Quiet mode. Only display text when required (progress bars
  not included, use `--no-progress` for this).

## Files in this Repository
- `dict-format.pdf`: PDF of how the JSON is formatted in case you want to make
  your own program that uses this data (and I recommend you do! I want this
  repository to help others).
- `dict-format.tex`: LaTeX source file for `dict-format.pdf`
- `html/`: HTML files that were used to make the JSON files in `json/`
- `json/`: This folder contains JSON files I've already created by using this
  program to potentially save the next person some time.
- `yorku_scrape.py`: Main Python program

## Donate
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/husseinesmail)
