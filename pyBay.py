from statistics import median
import argparse
from pprint import pprint
import requests
from bs4 import BeautifulSoup
from ebaysheet import ebaysheet


def accept_title(title):
    if args.exclude is not None:
        for arg in args.exclude:
            if arg.lower() in title.lower():
                return False

    if args.required is not None:
        for arg in args.required:
            if arg.lower() not in title.lower():
                return False

    return True


def price_in_range(price):
    if args.minprice is not None:
        if price < args.minprice:
            return False

    if args.maxprice is not None:
        if price > args.maxprice:
            return False

    return True


def get_listings(url_to_scrape):
    r = requests.get(url_to_scrape, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # Loop through all li's with "s-item" class AKA each listing box
    for li in soup.find_all("li", class_="s-item"):

        # Grab Title
        title_element = li.find("h3", class_="s-item__title s-item__title--has-tags")
        if title_element is None:
            continue

        title = title_element.text
        title = title.replace("New Listing", "")

        if accept_title(title) is False:
            continue

        titles.append(title)

        # Grab Link
        link_element = title_element.find_parent("a")
        link = link_element["href"]

        # Grab Price
        price_element = li.find("span", class_="s-item__price")
        if price_element is None:
            continue
        price = price_element.text
        price = price.replace("$", "").replace(",", "")

        if "Tap item to see current price" in price:
            continue

        if " to " in price:
            price_range = price.split(" to ")
            price_midpoint = (float(price_range[0]) + float(price_range[1])) / 2
            price = price_midpoint

        price = float(price)
        prices.append(price)

        # Grab Shipping
        shipping_element = li.find("span", class_="s-item__shipping s-item__logisticsCost")
        if shipping_element is None:
            continue

        shipping = shipping_element.text
        shipping = shipping.replace("shipping", "").replace("+", "").strip()

        if shipping == "Shipping not specified" or shipping == "Freight":
            continue

        if shipping != "Free":
            shipping = shipping.replace("$", "")
            shipped_price = price + float(shipping)
            shipped_price = round(shipped_price, 2)
            shipping = "$" + shipping
        elif shipping == "Free":
            shipped_price = price

        if price_in_range(shipped_price) is False:
            continue

        shipped_prices.append(shipped_price)

        # Grab Thumbnail
        thumbnail_element = li.find("img", class_="s-item__image-img")
        if thumbnail_element is None:
            continue

        img_url = thumbnail_element.attrs["src"]

        listings.append([f'=IMAGE("{img_url}")', f'=HYPERLINK("{link}", "{title}")', "$" + str(price), shipping, "$" + str(shipped_price)])

    return listings


listings = []
titles = []
prices = []
shipped_prices = []
headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
parser = argparse.ArgumentParser()
parser.add_argument("-search", "--keywords", nargs="+")
parser.add_argument("-req", "--required", nargs="+")
parser.add_argument("-exclude", "--exclude", nargs='+')
parser.add_argument("-pages", "--pages",  default=1, type=int)
parser.add_argument("-min", "--minprice", type=float)
parser.add_argument("-max", "--maxprice", type=float)
args = parser.parse_args()

keywords = args.keywords
if keywords is None:
    keywords = input("Search:")

for page in range(1, (args.pages + 1)):
    s = "+"
    url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={s.join(keywords)}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_ipg=200&_pgn={page}"
    # print(url)
    get_listings(url)

pprint(listings)
print(f"Number of Listings:{len(listings)}")
print(f"Min:{min(shipped_prices)}\nMax:{max(shipped_prices)}\nMedian:{median(shipped_prices)}")

sh = ebaysheet()
sh.values_clear("Sheet1!A2:M")
sh.values_update('Sheet1!A2', params={'valueInputOption': 'USER_ENTERED'}, body={'values': listings})
