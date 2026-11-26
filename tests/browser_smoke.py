"""Exercise the published site's normal controls in a real desktop and mobile Chromium browser."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect


def run(url,channel,shots):
    url=url.rstrip("/")+"/"
    with urlopen(urljoin(url,"atlas.json")) as r:
        data=json.load(r)
    papers=data["papers"]
    leading=max(papers,key=lambda p:p["likes"])
    abstract=leading.get("abstract")
    if data.get("abstract_chunk_size"):
        i=papers.index(leading);size=data["abstract_chunk_size"]
        with urlopen(urljoin(url,f"abstracts/{i//size}.json")) as r:abstract=json.load(r)[i%size]
    shots.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel=channel or None,headless=True)
        page=browser.new_page(viewport={"width":1440,"height":920},device_scale_factor=1)
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.goto(url)
        expect(page.locator("#visible")).to_have_text(f"{len(papers):,} visible", timeout=90000)
        threshold=data.get("threshold_exclusive",100)
        expect(page.locator("#likes")).to_have_value(str(threshold+1))
        expect(page.locator("#subtitle")).to_contain_text(f"more than {threshold} likes")
        page.screenshot(path=str(shots/"atlas-desktop.png"),full_page=True)
        search=page.get_by_role("searchbox")
        for value in (leading["title"],leading["authors"][0],leading["paper_id"]):
            search.fill(value)
            expect(page.locator("#sideBody")).to_contain_text(leading["title"])
        page.get_by_role("button",name="Fit visible papers").click()
        box=page.locator("canvas").bounding_box()
        page.mouse.click(box["x"]+box["width"]/2,box["y"]+box["height"]/2)
        expect(page.get_by_role("link",name="Open on alphaXiv")).to_have_attribute("href",urljoin("https://www.alphaxiv.org/abs/",leading["paper_id"]))
        page.get_by_text("Abstract",exact=True).click()
        expect(page.locator("details p")).to_have_text(abstract or "Title-only record",timeout=30000)
        nb=[papers[i]["title"] for i in leading["neighbors"]]
        assert page.locator("#sideBody .row").all_text_contents()==nb
        page.locator("#sideBody .row").first.click()
        expect(page.locator("#sideBody h2")).to_have_text(nb[0])
        page.reload()
        expect(page.locator("#sideBody h2")).to_have_text(nb[0])
        page.get_by_role("button",name="Reset",exact=True).click()
        expect(page.locator("#likes")).to_have_value(str(threshold+1))
        before=hashlib.sha256(page.locator("canvas").screenshot()).digest()
        page.get_by_role("button",name="Zoom in").click()
        assert hashlib.sha256(page.locator("canvas").screenshot()).digest()!=before
        page.get_by_role("button",name="Zoom out").click()
        page.get_by_role("button",name="Fit visible papers").click()
        clustered=next(p for p in papers if p["cluster"]>=0 and p["subjects"])
        g=str(clustered["cluster"]);s=clustered["subjects"][0];y=clustered["date"][:4]
        page.locator("#cluster").select_option(g)
        expect(page.get_by_role("heading",name="Evidence for Luna’s label")).to_be_visible()
        page.locator("#subject").select_option(s);page.locator("#year").select_option(y)
        page.locator("#likes").fill(str(clustered["likes"]))
        expected=sum(str(p["cluster"])==g and s in p["subjects"] and p["date"][:4]==y and p["likes"]>=clustered["likes"] for p in papers)
        expect(page.locator("#visible")).to_have_text(f"{expected:,} visible")
        search.fill("impossible-title-xxxxxxxxxxx")
        expect(page.get_by_text("No papers match these filters.")).to_be_visible()
        page.get_by_role("button",name="Reset",exact=True).click()
        with page.expect_download() as downloaded:page.get_by_role("link",name="Download CSV").click()
        assert downloaded.value.suggested_filename==data.get("csv","papers.csv")
        expect(page.get_by_role("combobox",name="Atlas edition")).to_have_value(str(threshold))
        mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True,device_scale_factor=1)
        mobile.goto(url)
        expect(mobile.locator("#visible")).to_have_text(f"{len(papers):,} visible",timeout=90000)
        assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        mobile.screenshot(path=str(shots/"atlas-mobile.png"),full_page=True)
        mobile.get_by_role("searchbox").fill(clustered["paper_id"])
        mobile.locator("#sideBody .row").first.click()
        expect(mobile.get_by_role("link",name="Open on alphaXiv")).to_be_visible()
        assert not errors,errors
        browser.close()
    print("Browser checks passed for",url,"with",len(papers),"papers")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("url");ap.add_argument("--channel",default="chrome");ap.add_argument("--shots",type=Path,default=Path("tmp/qa"))
    args=ap.parse_args();run(args.url,args.channel,args.shots)
