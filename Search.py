from bs4 import BeautifulSoup
import requests
import math
from firebase_setup import return_db

def delete_collection(collection):

    docs = collection.stream()

    for doc in docs:
        doc.reference.delete()



def deep_search(link):
    home= {}
    data = requests.get(link)

    html = BeautifulSoup(data.text, 'html.parser')
    details = html.find_all('span', class_ = "property-details_detailSpan__aFGW5 listing-summary_propertyDetail__uuu7e")

    for info in details:
        if info and 'data-cy' in info.attrs:
            try:
                if info['data-cy'] == 'property-beds':
                    bed = info.findChild('span', class_ = "listing-summary_propertyDetailValue__o_OaH")
                    home['Beds'] = int(bed.get_text().replace(',', ''))

                elif info['data-cy'] == 'property-baths':
                    bath = info.findChild('span', class_ = "listing-summary_propertyDetailValue__o_OaH")
                    home['Baths'] = int(bath.get_text().replace(',', ''))

                elif info['data-cy'] == 'property-sqft':
                    sqft = info.findChild('span', class_ = "listing-summary_propertyDetailValue__o_OaH")
                    home['SQFT'] = int(sqft.get_text().replace(',', ''))
                elif info["data-cy"] == "property-type":
                    house_type = info.findChildren('span', class_="")
                    for types in house_type:
                        type = str(types.get_text())
                        home["Type"] = type
                        

            except Exception:
                continue
            

    price = html.find('div', class_ = 'listing-summary_listPrice__WuHui')
    if price and 'data-cy' in price.attrs:
        if price['data-cy'] == 'property-price':
            
            home['Price'] = int(price.get_text().replace(',', '').replace('$', ""))

    road = html.find('h1', class_ = 'listing-address_root__g9lT5 listing-summary_addressWrapper__evDrd')
    
    if road:
        addrs1 = road.findChild('span', class_ = 'listing-address_splitLines__65V8g')
        addrs2 = road.findChild('span', class_ = 'listing-summary_cityLine__6r_FZ listing-address_splitLines__65V8g')
        home['Address'] = addrs1.get_text() + " " + addrs2.get_text()
    

    mls = html.find('div', class_ = 'listing-summary_mlsNum__enlps')
    if mls:
        mls = mls.get_text().replace('MLS® #: ', "").replace(',', "")
    
    h4 = html.find_all("h4", class_="bullet-section_bulletTitle__Vo_6T")
    for text in h4:
        if text.get_text() == "Basement":

            sibs = text.find_next_siblings("span")

            for s in sibs:
                if s.get_text() != ": ":
                    home['Basement'] = ["", ""]

                    if "Full" in s.get_text():
                        home["Basement"][0]= "Full "

                    elif "Partial" in s.get_text():
                        home["Basement"][0] = "Partial "

                    home['Basement'][1] = s.get_text()

                    continue
        else:
            sibs = text.find_next_siblings("span")

            for s in sibs:
                if s.get_text() != ": ":

                    if text.get_text() in home:
                        home[str(text.get_text())] = home[str(text.get_text())] + str(s.get_text())
                        continue

                    home[str(text.get_text())] = str(s.get_text())
                
    des = html.find('summary', class_="listing-description_descriptionContainer__L6RKL")
    des = des.findChild('p', class_="listing-description_descriptionContent__Eg6rp listing-description_collapsibleWrapper__UkOz9 listing-description_collapsed__5Ulc8")
    home["Description"] = (des.get_text())
    home["Link"] = link
    try:
        print(f"Address: {home["Address"]}, SQFT: {home["SQFT"]}, Beds: {home["Beds"]}, Baths: {home["Baths"]}, Type: {home["Type"]}, Subdivision: {home["Subdivision"]}")
        return home, mls
    except KeyError:
        pass

def make_data(db, city):
    city = db.collection('homes').document(city)
    
    # Create the city document with initial data (empty in this case)
    city.set({})
    
    # Reference to the city's housing collection
    return city.collection('housing')

def document_exists(collection, mls): 
    doc_ref = collection.document(mls)
    docs = doc_ref.get()
    return docs.exists

def main(abb, city):
    db = return_db()
    
    try:
        homes = db.collection(f"Homes").document(city).collection("Housing Data")
    except AttributeError:
        homes = make_data(city)
    c =0
    old_data = None
    
    
    for page in range(1, 20, 1):
        try:
            url = f"https://www.remax.ca/{abb}/{city}-real-estate?lang=en&pageNumber={page}&pricePerSqftMin=1&sqftMin=1&bedsMin=2&bathsMin=1&pageNumber=1&priceMin=1&priceMax=&pricePerSqftMax=&priceType=0&sqftMax=&lotSizeMin=&lotSizeMax=&bedsMax=4&featuredListings=&isRemaxListing=false&comingSoon=false&updatedInLastNumDays=&featuredLuxury=false&minImages=&house=false&townhouse=false&condo=false&rental=false&land=false&farm=false&duplex=false&cottage=false&other=false&commercial=false&commercialLease=false&vacantLand=false&hotelResort=false&businessOpportunity=false&rentalsOnly=false&commercialOnly=false&luxuryOnly=false&hasOpenHouse=false&hasVirtualOpenHouse=false&parkingSpacesMin=&parkingSpacesMax=&commercialSqftMin=&commercialSqftMax=&unitsMin=&unitsMax=&storiesMin=&storiesMax=&totalAcresMin=&totalAcresMax=&Agriculture=false&Automotive=false&Construction=false&Grocery=false&Hospitality=false&Hotel=false&Industrial=false&Manufacturing=false&Multi-Family=false&Office=false&Professional=false&Restaurant=false&Retail=false&Service=false&Transportation=false&Warehouse=false"
            data = requests.get(url)
            #print(url)
            if data == old_data:
                break
            else:
                old_data = data
        except ConnectionError:
            print("next")
            break
        except Exception as e:
            print(str(e))
            break

        html = BeautifulSoup(data.text, 'html.parser')
        houses = html.find_all('a', class_ = "listing-card_listingCard__lc4CL", limit=20)
        
        for house in houses:
            c+=1
            link = house.attrs['href']
            try:
                home_data, mls = (deep_search(link))
                if home_data and mls:
                    if not document_exists(homes, mls):  # Check if document with MLS number exists
                        homes.document(mls).set(home_data)

            except TypeError:
                pass
    
    get_ranges(homes, 15, "House")

def get_ranges(homes, percentage, Property_Type):
    ranges = []
    docs = homes.stream()
    
    for doc in docs:
        v = doc.to_dict()
        try:
            total = v['Price']
            sqf = v['SQFT']
            beds = v["Beds"]
            baths = v["Baths"]
            basement = v["Basement"]
            type = v["Type"]
            sub = v["Subdivision"]
        except KeyError:
            continue
        found = False
        for how in ranges:
            try:
                if (    
                        how['SQFT']["Min"] <= sqf and how["SQFT"]['Max'] >= sqf and 
                        how['Beds']["Min"] <=  beds and how['Beds']["Max"] >= beds and
                        how['Baths']["Min"] <= baths and how['Baths']["Max"] >= baths and
                        how["Basement"] == basement and type == Property_Type and how["Subdivision"] == sub
                    ):
                    how['Total'] += total
                    how['Count'] += 1
                    found = True
                    break  # Exit the loop once a match is found
            
            except KeyError:
                continue
        
        if not found:
            values = {
                "Basement": basement,
                "Beds": {
                    "Min": max(beds, 3),
                    "Max": min(beds + 1, 5)
                },
                "Baths": {
                    "Min": max(baths - 1, 1),
                    "Max": baths + 1
                },
                "SQFT": {
                    "Min": math.floor(sqf * 0.85),
                    "Max": math.floor(sqf * 1.15),
                },
                "Subdivision": sub,
                "Total": total,
                'Count': 1,
                "Type": type if type == "House" else "",
            }
            ranges.append(values)
    docs2 = homes.stream()
    for doc in docs2:
        f = doc.to_dict()
        for range_entry in ranges:
            try:
                average_price = range_entry["Total"] / range_entry["Count"]
                if (
                    range_entry['SQFT']["Min"] <= f["SQFT"] <= range_entry["SQFT"]['Max'] and
                    range_entry['Beds']["Min"] <= f["Beds"] <= range_entry["Beds"]['Max'] and
                    range_entry['Baths']["Min"] <= f["Baths"] <= range_entry["Baths"]['Max'] and
                    range_entry["Basement"] == f["Basement"] and f["Type"] == Property_Type and 
                    range_entry["Subdivision"] == f["Subdivision"]
                ):
                    avg_price_ratio = f["Price"] / average_price
                    if avg_price_ratio <= 1 - (percentage/100) and range_entry["Count"] >= 0:
                        print(f"{avg_price_ratio} AVG: {average_price} Price: {f['Price']}")
                        print(f"{f['Address']}\n{f['Link']}")

            except KeyError as e:
                pass
    return ranges
    
abbreviations = {
    "Alberta": "ab",
    "British Columbia": "bc",
    "Manitoba": "mb",
    "New Brunswick": "nb",
    "Newfoundland": "nl", 
    "Labrador": "lb",
    "Nova Scotia": "ns",
    "Ontario": "on",
    "Prince Edward Island": "pe",
    "Quebec": "qc",
    "Saskatchewan": "sk",
    "Northwest Territories": "nt",
    "Nunavut": "nu",
    "Yukon": "yt"
}
'''
from Places import rete
towns = rete()
for k, v in towns.items():
    abb = abbreviations[k]
    for item in v:
        print(abb,item)
        main(abb, item)
'''
for city in ["lethbridge", "calagary"]:
    pass
main("ab", "lethbridge")