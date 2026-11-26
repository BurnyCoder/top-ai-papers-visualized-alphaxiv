"""Read either layout of the public atlas in frozen snapshot order."""
from concurrent.futures import ThreadPoolExecutor
import json
from urllib.parse import urljoin
from urllib.request import urlopen
from .io import read_json


def catalog_rows(catalog,read):
    if "papers" in catalog:return catalog["papers"]
    with ThreadPoolExecutor(4) as pool:
        rows=[row for part in pool.map(read,catalog["paper_parts"]) for row in part]
    if len(rows)!=catalog["paper_count"]:raise ValueError("Incomplete map index")
    return rows


def local_catalog(folder):
    data=read_json(folder/"atlas.json")
    data["papers"]=catalog_rows(data,lambda name:read_json(folder/name))
    return data


def remote_catalog(base):
    def read(name):
        with urlopen(urljoin(base,name),timeout=120) as response:return json.load(response)
    data=read("atlas.json")
    data["papers"]=catalog_rows(data,read)
    return data
