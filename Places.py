import re

def transform_string(input_string):
    # Replace standalone "St." with "Saint"
    transformed_string = re.sub(r'\bSt\.\b', 'Saint', input_string)
    # Replace all spaces with dashes
    transformed_string = transformed_string.replace(" ", "-")
    return transformed_string

places= {}


with open("cities.txt", "r") as file:
    line = file.readlines()
    for i in line:
        for place, character in enumerate(i):
            if place == 0 and character == " ":
                i[place] == ""
            if character == ",":  
                province = i[place+1:].strip()
                city = i[:place]
                if province not in places:
                    places[province] = [transform_string(city.strip())]
                else:
                    places[province].append(transform_string(city.strip()))


def rete():
    return places
