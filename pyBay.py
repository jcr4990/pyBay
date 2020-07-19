from statistics import median
import argparse
from pprint import pprint
import requests
from bs4 import BeautifulSoup
from ebaysheet import ebaysheet


class ExcludedWordInTitle(Exception):
    """Raised when word defined with -excluded flag appears in title to continue loop"""
    pass


def get_listings(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # Loop through all li's with "s-item" class AKA each listing box
    for li in soup.find_all("li", attrs={"class": "s-item"}):

        # Grab Title
        if li.find("h3", attrs={"class": "s-item__title s-item__title--has-tags"}) is not None:
            title = li.find("h3", attrs={"class": "s-item__title s-item__title--has-tags"}).text
            title = title.replace("New Listing", "")

            if args.required is not None:
                if args.required.lower() not in title.lower():
                    continue

            if args.exclude is not None:
                try:
                    for arg in args.exclude:
                        if arg.lower() in title.lower():
                            raise ExcludedWordInTitle
                except ExcludedWordInTitle:
                    continue

            titles.append(title)


        # Grab Price
        if li.find("span", attrs={"class": "s-item__price"}) is not None:
            price = li.find("span", attrs={"class": "s-item__price"}).text
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
        if li.find("span", attrs={"class": "s-item__shipping s-item__logisticsCost"}) is not None:
            shipping = li.find("span", attrs={"class": "s-item__shipping s-item__logisticsCost"}).text
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

            if args.minprice is not None:
                if shipped_price < args.minprice:
                    continue

            if args.maxprice is not None:
                if shipped_price > args.maxprice:
                    continue

            shipped_prices.append(shipped_price)

        # Grab Thumbnail
        if li.find("img", attrs={"class": "s-item__image-img"}) is not None:
            img_elem = li.find("img", attrs={"class": "s-item__image-img"})
            img_url = img_elem.attrs["src"]

            try:
                listings.append([f'=IMAGE("{img_url}")', title, "$" + str(price), shipping, "$" + str(shipped_price)])
            except UnboundLocalError:
                pass

    return listings


listings = []
titles = []
prices = []
shipped_prices = []
headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
parser = argparse.ArgumentParser()
parser.add_argument("-search", "--keywords")
parser.add_argument("-req", "--required")
parser.add_argument("-exclude", "--exclude", nargs='+')
parser.add_argument("-pages", "--pages", type=int)
parser.add_argument("-min", "--minprice", type=float)
parser.add_argument("-max", "--maxprice", type=float)
args = parser.parse_args()

keywords = args.keywords
if keywords is None:
    keywords = input("Search:")
keywords = keywords.replace(" ", "%20")

if args.pages is None:
    num_pages = 1
else:
    num_pages = args.pages

for page in range(num_pages):
    url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={keywords}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_ipg=200&_pgn={page}"
    get_listings(url)

pprint(listings)
print(f"Number of Listings:{len(listings)}")
print(f"Min:{min(shipped_prices)}\nMax:{max(shipped_prices)}\nMedian:{median(shipped_prices)}")

sh = ebaysheet()
sh.values_clear("Sheet1!A2:M")
sh.values_update('Sheet1!A2', params={'valueInputOption': 'USER_ENTERED'}, body={'values': listings})  # ValueInputOption = RAW