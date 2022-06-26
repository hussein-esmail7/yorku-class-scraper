# Python program to read
# json file


import json

# Opening JSON file
path = input("Path: ")
f = open(path)

# returns JSON object as
# a dictionary
data = json.load(f)

print(len(data))

# Closing file
f.close()
