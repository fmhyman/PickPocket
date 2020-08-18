from fetchTitleFromURL import fetchTitleFromURL
from bs4 import BeautifulSoup

from random import choice
from uuid import uuid1

from datetime import datetime
from notion.client import NotionClient
from notion.collection import NotionDate

PATH_POCKET_FILE = ""
NOTION_TOKEN = ""
NOTION_TABLE_ID = ""

class PocketListItem:
    title = ""
    url = ""
    tags = []
    addedOn = 0
    readStatus = None
    
    def __init__(self, title, url, tags, addedOn, readStatus):
        self.title = title
        self.url = url
        self.tags = tags
        self.addedOn = addedOn
        self.readStatus = readStatus

def retrieveAllPocketItems():
    with open(PATH_POCKET_FILE, encoding='utf8', errors='ignore') as fp:
        soup = BeautifulSoup(fp,'html.parser')
    allPocketListItems = []
    itemList = soup.h1.find_next("h1")

    # Retrieving the items from the user's Pocket List first.
    articles = itemList.find_all_previous("a")
    for eachItem in articles:
        url = eachItem['href']
        title = eachItem.get_text()
        # title = fetchTitleFromURL(url)
        tags = eachItem['tags'].split(',')
        addedOn = int(eachItem['time_added'])
        readStatus = False
        eachPocketListItemData = PocketListItem(title,url,tags,addedOn,readStatus)
        allPocketListItems.append(eachPocketListItemData)

    # Retreiving the items from the user's Archive list next.
    articles = itemList.find_all_next("a")
    for eachItem in articles:
        url = eachItem['href']
        title = eachItem.get_text()
        # title = fetchTitleFromURL(url)
        tags = eachItem['tags'].split(',')
        addedOn = int(eachItem['time_added'])
        readStatus = True
        eachPocketListItemData = PocketListItem(title,url,tags,addedOn,readStatus)
        allPocketListItems.append(eachPocketListItemData)
    return allPocketListItems    

def itemAlreadyExists(item):
    for eachRow in cv.collection.get_rows():
        if item.url == eachRow.url:
            return True
    print(f"Adding {item.url} to the list")
    return False

colors = ['default', 'gray', 'brown', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'red']

def addNewTag(cv, schema, prop, tag):
    dupe = next(
        (o for o in prop["options"] if o["value"] == tag), None
    )
    if dupe:
        raise ValueError(f'{tag} already exists in the schema!')

    prop["options"].append(
        {"id": str(uuid1()), "value": tag, "color": choice(colors)}
    )
    try:
        cv.collection.set("schema", schema)
    except (RecursionError, UnicodeEncodeError):
        pass

def setTag(page, cv, prop, new_values):
    schema = cv.collection.get("schema")
    new_values_set = set(new_values)

    if new_values == ['']:
        return []

    prop = next(
        (v for k, v in schema.items() if v["name"] == 'Tags'), None
    )

    if "options" not in prop: prop["options"] = []

    current_options_set = set(
        [o["value"] for o in prop["options"]]
    )
    intersection = new_values_set.intersection(current_options_set)

    if len(new_values_set) > len(intersection):
        difference = [v for v in new_values_set if v not in intersection]
        for d in difference:
            addNewTag(cv, schema, prop, d)    
    page.set_property('Tags', new_values)

def addToNotion():
    index = 0
    for index, eachItem in enumerate(allPocketListItems):
        if itemAlreadyExists(eachItem):
            continue
        index += 1
        row = cv.collection.add_row()
        row.title = fetchTitleFromURL(eachItem.url) if eachItem.title == eachItem.url else eachItem.title
        row.url = eachItem.url
        setTag(row, cv, 'prop', eachItem.tags)
        row.added_on = NotionDate(datetime.fromtimestamp(eachItem.addedOn))
        row.read = eachItem.readStatus
    print(f"{index}/{len(allPocketListItems)} added")


client = NotionClient(token_v2= NOTION_TOKEN)
cv = client.get_collection_view(NOTION_TABLE_ID)
print(cv.parent.views)

print("Retreiving all items from Pocket")
allPocketListItems = retrieveAllPocketItems()
print("Retreival done")
print("Inserting items as table entries in Notion database")
addToNotion()
print("Transfer successfully completed")