"""Capture a short MP4 walkthrough from the actual atlas using Chrome and system FFmpeg."""
import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import urljoin
from urllib.request import urlopen
from playwright.sync_api import sync_playwright,expect


def record(url,path):
    url=url.rstrip("/")+"/"
    with urlopen(urljoin(url,"atlas.json")) as response:atlas=json.load(response)
    largest=max((g for g in atlas["clusters"] if int(g)>=0),key=lambda g:atlas["clusters"][g]["count"])
    paper=max((p for p in atlas["papers"] if str(p["cluster"])==largest),key=lambda p:p["likes"])
    path.parent.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel="chrome")
        page=browser.new_page(viewport={"width":1360,"height":920},device_scale_factor=1)
        page.goto(url);expect(page.locator("#visible")).to_contain_text("visible",timeout=90000)
        # Repeated still frames give readers time to inspect each real browser state.
        cmd=["ffmpeg","-v","error","-y","-f","image2pipe","-vcodec","mjpeg","-framerate","5","-i","pipe:0",
             "-c:v","libx264","-preset","fast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(path)]
        with subprocess.Popen(cmd,stdin=subprocess.PIPE) as encoder:
            def hold(frames):
                shot=page.screenshot(type="jpeg",quality=92)
                for _ in range(frames):encoder.stdin.write(shot)
            hold(12)
            search=page.get_by_role("searchbox")
            for value in (paper["paper_id"][:4],paper["paper_id"]):
                search.fill(value);hold(4)
            page.locator("#sideBody .row").first.click()
            expect(page.locator("#sideBody h2")).to_have_text(paper["title"])
            hold(12)
            page.get_by_text("Abstract",exact=True).click()
            expect(page.locator("details p")).not_to_have_text("Loading abstract…");hold(10)
            page.get_by_text("Abstract",exact=True).click()
            page.locator(".detailgroup").click();hold(14)
            page.get_by_role("button",name="Reset",exact=True).click();hold(8)
            encoder.stdin.close()
            if encoder.wait():raise RuntimeError("The walkthrough could not be encoded")
        browser.close()


if __name__=="__main__":
    cmd=argparse.ArgumentParser(description=__doc__);cmd.add_argument("url");cmd.add_argument("path",type=Path)
    args=cmd.parse_args();record(args.url,args.path)
