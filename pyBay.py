import requests
from bs4 import BeautifulSoup
from statistics import median
import argparse
from ebaysheet import ebaysheet

# TODO:
# median from python script based on price not shipped price
# add min/max price args
# replace exc_skip flag with try/except and custom exception when exc word found via raise exceptionname


def get_listings(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    for li in soup.find_all("li", attrs={"class": "s-item"}):
        exc_skip = 0
        if li.find("h3", attrs={"class": "s-item__title s-item__title--has-tags"}) is not None:
            title = li.find(
                "h3", attrs={"class": "s-item__title s-item__title--has-tags"}).text
            title = title.replace("New Listing", "")

            if args.required is not None:
                if args.required.lower() not in title.lower():
                    # print(f"Required keyword not in '{title}'")
                    continue

            if args.exclude is not None:
                for arg in args.exclude:
                    if arg.lower() in title.lower():
                        exc_skip = 1
                        break

            if exc_skip == 1:
                continue

            titles.append(title)

        if li.find("span", attrs={"class": "s-item__price"}) is not None:
            price = li.find("span", attrs={"class": "s-item__price"}).text
            price = price.replace("$", "").replace(",", "")

            if "Tap item to see current price" in price:
                continue

            if " to " in price:
                price_range = price.split(" to ")
                price_midpoint = (
                    float(price_range[0]) + float(price_range[1])) / 2
                price = price_midpoint

            price = float(price)
            prices.append(price)

        if li.find("span", attrs={"class": "s-item__shipping s-item__logisticsCost"}) is not None:
            shipping = li.find(
                "span", attrs={"class": "s-item__shipping s-item__logisticsCost"}).text
            shipping = shipping.replace(
                "shipping", "").replace("+", "").strip()

            if shipping == "Shipping not specified" or shipping == "Freight":
                continue

            if shipping != "Free":
                shipping = shipping.replace("$", "")
                shipped_price = price + float(shipping)
                shipped_price = round(shipped_price, 2)
                shipping = "$" + shipping
            elif shipping == "Free":
                shipped_price = price

        if li.find("img", attrs={"class": "s-item__image-img"}) is not None:
            img_elem = li.find("img", attrs={"class": "s-item__image-img"})
            img_url = img_elem.attrs["src"]

            # listings.append([title, "$" + str(price), shipping, "$" + str(shipped_price), f'=IMAGE("{img_url}")'])
            try:
                listings.append(
                    [f'=IMAGE("{img_url}")', title, "$" + str(price), shipping, "$" + str(shipped_price)])
            except UnboundLocalError:
                pass

    return listings, titles, prices


listings = []
titles = []
prices = []
parser = argparse.ArgumentParser()
parser.add_argument("-search", "--keywords")
parser.add_argument("-req", "--required")
parser.add_argument("-exclude", "--exclude", nargs='+')
# parser.add_argument("-pages", "--pages")
args = parser.parse_args()

keywords = args.keywords
if keywords == None:
    keywords = input("Search:")
keywords = keywords.replace(" ", "%20")
headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}

for page in range(1):
    # &_pgn=1
    url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={keywords}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_ipg=200&_pgn={page}"
    get_listings(url)

# Debug/Test Prints
# print(f"Number of Titles:{len(titles)}")
# print(f"Number of Prices:{len(prices)}")
print(f"Number of Listings:{len(listings)}")
print(f"Min:{min(prices)}\nMax:{max(prices)}\nMedian:{median(prices)}")


sh = ebaysheet()
sh.values_clear("Sheet1!A2:M")

sh.values_update('Sheet1!A2', params={'valueInputOption': 'USER_ENTERED'}, body={'values': listings})  # ValueInputOption = RAW
