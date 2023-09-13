from bs4 import BeautifulSoup
import asyncio
from pyppeteer import launch
import re
import random

# Revision Date: 9/7/2023

TO_SEARCH = 'searches.txt' # search links from r/puppysearch
MAX_FEE = 75 # in USD. I'm assuming a "rehoming fee" above this is too high. Somewhat arbitary

async def main():

    # get links from searches.txt -- taken from r/puppysearch
    with open(TO_SEARCH,'r') as fp:
        searches = fp.read().split('\n')

    browser = await launch(headless = True)
    context = await browser.createIncognitoBrowserContext()
    page = await context.newPage()

    # DEBUG
    #LINK = 'https://atlanta.craigslist.org/nat/pet/d/stockbridge-bully-pit-pups-top-quality/7659504080.html'
    #title_text, description, price = await get_page_contents(context,LINK)
    #is_BYB = evaluate_listing(title_text, description, price)
    #print('is_BYB',is_BYB)

    # clear the file
    with open('listings.txt','w') as fp:
        fp.close()

    # Get links to listings from each search
    for link in searches:
        #print(f'processing {link}...')
        try:
            
            await asyncio.sleep(
                random.randint(3,5)
            )

            await page.goto(link)
            await page.screenshot({'path': 'example.png'}) # not necessary but pyppeteer glitched when we didnt
            content = await page.content()
            listings = get_listings(content)
        
            with open('listings.txt','a') as fp:
            
                for listing in listings:
                    fp.write(listing + '\n')
        except:
            print('Skipping listing')

    print('Extracted URLs from searches.txt.')

    # parse each listing
    with open('listings.txt','r') as fp:
        all_links = fp.read().split('\n')

    # Determine if listing should be flagged 
    is_BYB_list = []
    print("Evaluating listings...")

    for link in all_links:

        try:
            title_text, description, price = await get_page_contents(context,link)
            is_BYB = evaluate_listing(title_text, description, price)
            is_BYB_list.append(is_BYB)

            # Flag BYB listings
            if is_BYB == True:
                await flag_link(context,link)
        except:
            print('Skipping listing...')

    print('Flagging complete.')
    # Write findings to a file! 
    with open('results.txt','w') as fp:
        fp.write('is_BYB\t link\n')
        for i in range(0,len(is_BYB_list)):
            fp.write('{0}\t{1}\n'.format(is_BYB_list[i],all_links[i]))

    # done!
    await browser.close()

    
def get_listings(content):

    soup = BeautifulSoup(content,'html.parser')

    results = soup.find("div",{"class": "results" }) # look at div class for results #results cl-results-page

    listings = []

    # get link for each listing
    if results is not None:
        for link in results.find_all('a',attrs={'href': re.compile("^https://")}):
            listings.append(link.get('href'))

    return listings


async def get_page_contents(context,link):

    page = await context.newPage()
    await page.goto(link)
    # await page.screenshot({'path': 'example.png'})
    content = await page.content()

    await page.close()

    return parse_page_data(content)


async def flag_link(context,link):

    page = await context.newPage()
    await page.goto(link)

    # Flag the listing
    await page.click('.flag-action > .flag')

    await asyncio.sleep(
        random.randint(3,5)
    )


def parse_page_data(content):
    soup = BeautifulSoup(content,'html.parser')

    price_section = soup.find("span",{"class":"price"})

    if price_section is not None:
        price = price_section.getText()
        price = price.replace("$","")
        price = float(price.replace(",",""))
    else: 
        price = 0 # no info
    #<span class="price">$1,500</span>


    description_section = soup.find("section",{"id":"postingbody"})
    title_section = soup.find("span",{"id":"titletextonly"})

    if title_section is None:
        title_text = ""
    else:
        title_text = title_section.getText()
    
    if description_section is None:
        description = ""
    else:
        description = description_section.getText()

    return title_text, description, price


def evaluate_listing(title_text, description,price):

    # Process Listing Price
    if price > MAX_FEE:
        return True

    # Process Listing Title

    # Title - Flagged Keywords
    title_flags = ['sale','sell','selling','exotic','micro','pocket','buy']


    for flag in title_flags:
        if flag in title_text.lower():
            #print('title keyword flag')
            return True
    
    # Look for numbers (assumed price) in title, interpret as price, flag above threshold, e.g. flags a title like "300 pitty puppy" probably means they want to sell a puppy for $300
    title_num_regex = r'(\d+)'

    result = None
    result = re.search(title_num_regex,title_text)

    if result is not None:
        title_num = result.group(1)
    else: 
        title_num = '0'

    if title_num is not None :
        for result in title_num:
            if float(result) > MAX_FEE:
                #print('title fee flag')
                return True
            
    # Process Listing Description

    # Description - Flagged keywords
    descr_flags = ['micro','pocket','selling','sell','sale','buy','not free','price','negotiate','available','exotic','deposit','reserve','obo','or best offer','serious inquiries','serious offers','buyer','buyers', 'bred']

    description = description.lower()

    for flag in descr_flags:
        if flag in description:
            #print('description keyword flag')
            return True

    # determine price from description
    descr_regex_max_fee = [
        r'$(\d+)', # $100
        r'(\d+)$', # 100$ in case of idiot
        r'(\d+.\d+)$', # 100.00$ # in case of idiot
        r'asking (\d+)', # asking 100
        r'asking (\d+.\d+)', # asking 100.00
        r'(\d+.\d+)', # 100.00
        r'$(\d+.\d+)', # $100.00
        r'boys (\d+)', # boys 100
        r'girls (\d+)', # girls 100
    ]

    # "prices listed in the thousands, e.g. 1k, 2k"
    descr_regex_k = [
        r'(\d+)(?: )?k',
        r'(\d+.\d+)(?: )?k',
    ]
        
    descr_regex_auto_reject = [
        r'three k' # arbitrary hard coded stuff
    ]

    for regex in descr_regex_max_fee:
        result = None
        result = re.search(regex,description)
        
        if result is None:
            continue

        price = float(result.group(1))

        if price > MAX_FEE:
            #print('descr price flag')
            return True
        
    for regex in descr_regex_k:
        result = None
        result = re.search(regex,description)
        
        if result is None:
            continue
        
        price = float(result.group(1))*1000
        if price > MAX_FEE:
            #print('descr price flag')
            return True
        
    for regex in descr_regex_auto_reject:
        result = None
        result = re.search(regex,description)

        if result is not None:
            #print('descr auto reject flag')
            #print('auto reject result',result)
            return True

    return False


asyncio.get_event_loop().run_until_complete(main())


