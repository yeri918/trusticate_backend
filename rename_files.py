import os
import json 


# for file_name in os.listdir(directory_path):
#     file_path = os.path.join(directory)
# Open the JSON file
# filename = 

# with open(filename,'r') as f:
#     data = json.load(f)

# value = data['credentialSubject']['name']

# newfilename = "./" + value + ".json"
# print(newfilename)
# os.rename(filename, newfilename)
local_directory_path = './test1.json'
for file_name in os.listdir(local_directory_path):
    local_file_path = os.path.join(local_directory_path, file_name)
    print(local_file_path)
    with open(local_file_path, 'r') as f:
        data = json.load(f)
    value = data['credentialSubject']['name']
    file_name = value + ".json"
