from os import listdir, path
from hashlib import sha3_256
from math import prod

all_file_names = [f for f in listdir("./data") if path.isfile("./data/" + f)]
files = dict().fromkeys(all_file_names)
for file_name in all_file_names:
    with open("./data/" + file_name, mode="rb") as file:
        files[file_name] = sha3_256(file.read()).hexdigest().lower()

def sorting_key(hash:str):
    digits = [int(digit, 16) + 1 for digit in hash]
    return prod(digits)

concatenated = "".join(sorted(files.values(), key=sorting_key)) + "jakubwiszniewski1234@gmail.com"
print(sha3_256(concatenated.lower().encode()).hexdigest().lower())

# print(fileContent)