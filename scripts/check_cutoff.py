"""Reobserve the strict feed boundary with several independent page widths."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import httpx
from atlas.collect import feed_rows
from atlas.io import RESULTS, now, save_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot");parser.add_argument("threshold",type=int)
    parser.add_argument("rank_hint",type=int);parser.add_argument("sizes",type=int,nargs="+")
    args=parser.parse_args()
    with httpx.Client(timeout=75) as client:
        def locate(size):
            page=max(0,(args.rank_hint-1)//size)
            for _ in range(30):
                rows=feed_rows(client,page,size)
                eligible=[j for j,r in enumerate(rows) if r["metrics"]["public_total_votes"]>args.threshold]
                if not eligible:page-=1;continue
                last=eligible[-1]
                lower=rows[last+1] if last+1<len(rows) else feed_rows(client,page+1,size)[0]
                if lower["metrics"]["public_total_votes"]>args.threshold:page+=1;continue
                def observation(row,rank):
                    return dict(rank=rank,id=row["paper_group_id"],likes=row["metrics"]["public_total_votes"])
                return dict(page_size=size,page=page,observed_at=now(),
                            last_above=observation(rows[last],page*size+last+1),
                            first_at_or_below=observation(lower,page*size+last+2))
            raise RuntimeError("The supplied starting rank is far from the cutoff")
        observed=list(ThreadPoolExecutor(4).map(locate,args.sizes))
    file=RESULTS/args.snapshot/"boundary-probes.json"
    save_json(file,dict(threshold_exclusive=args.threshold,observations=observed))
    print([(r["page_size"],r["last_above"]["rank"]) for r in observed])


if __name__=="__main__":main()
