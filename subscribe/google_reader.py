from subscribe import SubDoc
from subscribe import SubFolder
from subscribe import SubSource
from uuid import uuid4
import xml.etree.ElementTree as ET

def parse_google_reader(file: str) -> SubDoc:
    tree = ET.parse(file)
    root = tree.getroot()
    root_sub_folder = SubFolder()
    sub_folders = []
    sub_sources = []
    parse_node(sub_folders, sub_sources, root_sub_folder, root.find("body"))

    return SubDoc(sub_folders, sub_sources)

def parse_node(sub_folders: list, sub_sources: list, parent: SubFolder, node):
    for outline in node.findall("./outline"):
        title = outline.attrib["title"]
        if "xmlUrl" not in outline.attrib:
            item = SubFolder(uuid4().hex, title)
            sub_folders.append(item)
            parse_node(sub_folders, sub_sources, item, outline)
        else:
            item = SubSource(outline.attrib["xmlUrl"], title)
            item.parent_id = parent.id
            sub_sources.append(item)

        item.parent_id = parent.id
