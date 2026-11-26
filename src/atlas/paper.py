"""Generate the PDF from measured results. Bibliographic source links are included at the point of use."""
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from matplotlib import get_data_path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from .io import GITHUB, HUB
from .editions import above_threshold, edition_path


def pct(v):
    return "n/a" if v is None else f"{100*v:.2f}%"


def make_paper(path,manifest,evaluation,clusters,figdir):
    """Report reportable units, comparators and uncertainty on fixed-layout pages."""
    path.parent.mkdir(parents=True,exist_ok=True)
    fonts=Path(get_data_path())/"fonts/ttf"
    for alias,name in [("AtlasSans","DejaVuSans.ttf"),("AtlasSerif","DejaVuSerif.ttf"),("AtlasBold","DejaVuSans-Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(alias,str(fonts/name)))
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="PaperTitle",fontName="AtlasSerif",fontSize=26,leading=32,textColor=colors.HexColor("#143f35"),spaceAfter=9))
    styles.add(ParagraphStyle(name="SectionTitle",fontName="AtlasSerif",fontSize=20,leading=25,spaceAfter=9,textColor=colors.HexColor("#143f35")))
    styles.add(ParagraphStyle(name="Sub",fontName="AtlasBold",fontSize=10.4,leading=13,spaceBefore=6,spaceAfter=3,textColor=colors.HexColor("#245646")))
    styles.add(ParagraphStyle(name="Copy",fontName="AtlasSans",fontSize=9.0,leading=13.3,spaceAfter=6))
    styles.add(ParagraphStyle(name="CaptionText",fontName="AtlasSans",fontSize=8,leading=11,spaceAfter=6,textColor=colors.HexColor("#435b50")))
    story=[]
    def p(value,style="Copy"): story.append(Paragraph(value,styles[style]))
    def image(name,height):
        obj=Image(str(figdir/name));obj._restrictSize(166*mm,height*mm);story.append(obj)
    def table(rows,widths):
        data=[[Paragraph(escape(str(v)),styles["CaptionText"]) for v in row] for row in rows]
        obj=Table(data,colWidths=[w*mm for w in widths],hAlign="LEFT",repeatRows=1)
        obj.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaf1e6")),
                ("VALIGN",(0,0),(-1,-1),"TOP"),("LINEBELOW",(0,0),(-1,-1),.3,colors.HexColor("#d1d9ce")),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),2)]));story.extend([obj,Spacer(1,6)])
    def link(url,title): return '<link color="#006c5b" href="'+escape(url)+'">'+escape(title)+'</link>'
    primary=evaluation["primary"];rows=evaluation["seeds"];r=rows[0];alt=evaluation["pca_ablation"]
    def avg(key):return sum(row[key] for row in rows)/len(rows)
    def pp(v):return f"{100*v:.2f}"
    threshold=manifest["threshold_exclusive"]
    protocol_dir=(Path("reports")/edition_path(threshold)).as_posix()
    n=manifest["count"];first=manifest["passes"][-2];date=datetime.fromisoformat(manifest["ended_at"]).strftime("%d %B %Y")
    p("A semantic atlas of highly liked alphaXiv papers","PaperTitle")
    p("Libor “Burny” Burian · "+date,"CaptionText")
    p("Abstract","Sub")
    p(f"We collected {n:,} unique research papers with more than {threshold} public likes from alphaXiv. We embedded their titles and abstracts, projected them for display, and grouped them in a separate ten-dimensional space. Across {len(rows)} seeds, two-dimensional UMAP preserved {pct(avg('umap_recall'))} of each paper’s ten original neighbors on average. PCA preserved {pct(r['pca_recall'])}. The paired difference was {pp(primary['mean_difference'])} percentage points, with a 95% seed interval of {pp(primary['ci95'][0])} to {pp(primary['ci95'][1])}. At the display seed, {r['unassigned']:,} papers remained unassigned.")
    p("Motivation and contribution","Sub")
    p("A ranked feed answers which papers attracted attention. A researcher looking for related work also needs to know which papers discuss similar ideas and how much a two-dimensional view distorts those relationships. This release combines a verified selection boundary, source-space recommendations and inspectable topic labels in a downloadable atlas. The contribution is the audited collection and evaluation of this map.")
    image("atlas.png",102)
    p("Figure 1. One point represents one paper. The legend lists the largest assigned groups and the unassigned set. Distances between distant regions have no calibrated interpretation.","CaptionText")
    story.append(PageBreak())
    p("Collection and methods","SectionTitle")
    p("Census","Sub")
    p(f"The two accepted passes ran between {escape(first['started_at'])} and {escape(manifest['ended_at'])}. We sorted by all-time public votes, disabled both blog flags, and removed records explicitly marked as external posts. The first accepted pass encountered {sum(map(above_threshold,first['pages'])):,} entries above the threshold, excluded {first['excluded_blogs']} marked posts and deduplicated {first['duplicates']} group occurrences. The independent pass reproduced the eligible IDs. {manifest['title_only']} papers used the title-only fallback. "+link("https://api-dev.alphaxiv.org/api.json","alphaXiv API specification"))
    p("Representation and algorithms","Sub")
    p("The hosted text-embedding-3-large encoder received the title, a blank line and the abstract. We normalized its vectors and calculated exact cosine neighbors, excluding each paper itself. UMAP used 30 neighbors and cosine distance. Display coordinates used two dimensions and minimum distance 0.1. A separate ten-dimensional fit used minimum distance zero, followed by Euclidean excess-of-mass HDBSCAN with minimum cluster size 20 and minimum samples 5, including the point. Seed 42 determined the public map. "+" · ".join([link("https://developers.openai.com/api/docs/guides/embeddings","OpenAI embeddings"),link("https://umap-learn.readthedocs.io/en/latest/clustering.html","UMAP clustering guide"),link("https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html","HDBSCAN implementation")]))
    image("architecture.png",41)
    p("Figure 2. Display positions, group assignments and nearest-paper recommendations use three different transformations of the same hosted vectors.","CaptionText")
    p("Primary analysis","Sub")
    p("For each paper we divided the intersection of its original and displayed ten nearest neighbors by ten. We averaged across papers and calculated the UMAP minus PCA difference for seeds 42–51. The two-sided Student t interval uses seed-level differences. The shuffled-position control randomly reassigned the UMAP coordinates to paper IDs once per seed. The ablation replaced ten-dimensional UMAP with ten principal components while retaining the clustering settings. "+link(f"{GITHUB}/blob/main/{protocol_dir}/preregistration.md","Preregistered analysis")+" · "+link("https://www.nature.com/articles/s42003-022-03628-x","Huang et al. on neighborhood preservation"))
    p("Labeling","Sub")
    p("Luna received distinctive TF–IDF phrases and excerpts from members nearest their cluster centroid in the original vector space. Each displayed name links to supporting member IDs validated against the prompt. These are generated descriptions. "+link("https://arxiv.org/html/2511.02601v1","Murray et al. on labeling scientific documents"))
    story.append(PageBreak())
    p("Results and controls","SectionTitle")
    table([["Projection / assignment","Recall at 10","Clusters","Unassigned","Shared subject*"],
           ["UMAP / UMAP–HDBSCAN",pct(r["umap_recall"]),r["clusters"],pct(r["unassigned_fraction"]),pct(r["tag_agreement"]["fraction"])],
           ["PCA / primary assignments",pct(r["pca_recall"]),r["clusters"],pct(r["unassigned_fraction"]),pct(r["tag_agreement"]["fraction"])],
           ["Shuffled / primary assignments",pct(r["shuffled_recall"]),r["clusters"],pct(r["unassigned_fraction"]),pct(r["tag_agreement"]["fraction"])],
           ["PCA / PCA–HDBSCAN",pct(r["pca_recall"]),alt["clusters"],pct(alt["unassigned_fraction"]),pct(alt["tag_agreement"]["fraction"])]],[56,25,19,30,36])
    p(f"Table 1. Display seed {r['seed']}. *Fraction of tagged within-cluster pairs sharing an arXiv category. The shuffled-tag control for primary assignments was {pct(r['shuffled_tag_agreement']['fraction'])}. Tags were available for {evaluation['tagged']:,} of {n:,} papers. The middle two rows reuse the primary labels to isolate changes in projection.","CaptionText")
    image("comparisons.png",102)
    p("Figure 3. Panels A–C retain topic identity while changing screen coordinates. Panel D shows the assignments recovered by clustering PCA coordinates. Colors in D identify its own groups.","CaptionText")
    p("What the map loses","Sub")
    p(f"Even with the primary projection, a mean of {pct(1-avg('umap_recall'))} of the original ten neighbors fell outside the ten closest displayed points. The neighbor list exposes those relationships directly. The directional primary hypothesis was {primary['conclusion']} under the preregistered criterion.")
    story.append(PageBreak())
    p("Stability, limitations and reproducibility","SectionTitle")
    image("metrics.png",59)
    p("Figure 4. Each marker is one full-corpus run. The two stability series measure agreement with seed 42 and the fraction jointly assigned. Seed 42 compares with itself.","CaptionText")
    sensitivity=rows[1:]
    p(f"Across the other seeds, adjusted Rand agreement including unassigned points ranged from {min(s['ari_all'] for s in sensitivity):.3f} to {max(s['ari_all'] for s in sensitivity):.3f}. The original and permuted subject agreement estimates pool within-cluster pairs, giving larger groups more weight. Cross-listed subjects are a coarse, incomplete external reference.")
    p("Example topics","Sub")
    leaders=sorted((g for g in clusters.values() if g.get("evidence")),key=lambda g:-g["count"])[:3]
    for g in leaders:
        evidence=" · ".join(link("https://www.alphaxiv.org/abs/"+i,i) for i in g["evidence"][:2])
        p(escape(g["name"])+f" ({g['count']} papers). "+evidence,"CaptionText")
    p("Scope and limitations","Sub")
    if threshold==50:
        p("The two threshold editions use independent layouts. UMAP adjusts its default optimization budget to corpus size, so differences between editions can reflect both the population and the optimizer. "+link("https://umap-learn.readthedocs.io/en/latest/_modules/umap/umap_.html#simplicial_set_embedding","UMAP implementation"))
    p("The census represents public feed membership during the recorded window. Likes condition selection on platform attention. Older papers, topic popularity and exposure can affect inclusion. The analysis is descriptive and transductive. The interval quantifies variation from projection seeds conditional on these inputs. It does not estimate uncertainty across future papers. Hosted model revisions may alter a fresh run, so the exact vectors and returned labels accompany the release.")
    p("Reproduction and review","Sub")
    p("Restore the dated snapshot and run the offline build to reproduce tables, figures and the website. The archive includes checksums, paper metadata, embeddings, coordinates, supporting label IDs and per-seed scores. "+" · ".join([link(HUB,"Dataset and numerical artifacts"),link(GITHUB,"Code and instructions"),link(f"{GITHUB}/blob/main/{protocol_dir}/planned-runs.md","Run matrix")]))
    p("AI statement","Sub")
    p("A human provided the exact specification. Codex wrote the codebase and this paper to execute it. Human cleanup and rewriting are in progress.","CaptionText")
    def footer(canvas,doc):
        canvas.setFont("AtlasSans",8);canvas.setFillColor(colors.HexColor("#51685b"))
        canvas.drawString(22*mm,12*mm,"PAPER ATLAS   /   "+manifest["snapshot"])
        canvas.drawRightString(A4[0]-22*mm,12*mm,str(doc.page))
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=16*mm,bottomMargin=21*mm,
              title="A semantic atlas of highly liked alphaXiv papers",author="Libor “Burny” Burian",invariant=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
