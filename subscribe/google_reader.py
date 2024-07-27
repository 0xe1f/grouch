from subscribe import Category
from subscribe import Subscription
import xml.etree.ElementTree as ET

def parse_gr(file: str):
    tree = ET.parse(file)
    root = tree.getroot()
    cat = Category()
    parse_node(cat, root.find('body'))

    return cat

def parse_node(cat: Category, node):
    for outline in node.findall('./outline'):
        title = outline.attrib["title"]
        if 'xmlUrl' not in outline.attrib:
            item = Category(title)
            parse_node(item, outline)
        else:
            item = Subscription(title, outline.attrib['xmlUrl'])

        cat.add(item)
