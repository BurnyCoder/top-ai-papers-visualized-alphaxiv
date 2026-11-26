"""Publication figures drawn only from the frozen coordinates and per-seed result files."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


def figures(folder, A, clusters, evaluation, threshold=100):
    folder.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,
                         "axes.spines.right":False,"figure.facecolor":"white","axes.titlelocation":"left"})
    labels=A["labels"]
    colors=np.array([clusters[str(i)]["color"] for i in labels])
    def points(ax,xy,cols,title):
        ax.scatter(xy[:,0],xy[:,1],s=7,c=cols,linewidths=0,alpha=.72,rasterized=True)
        ax.set_aspect("equal",adjustable="datalim"); ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.set_title(title,fontsize=11,color="#1a4036",fontweight="bold")
    def save(fig,name):
        fig.savefig(folder/name,dpi=160,bbox_inches="tight",pad_inches=.15)
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(10.5,5.6))
    points(ax,A["xy"],colors,"Semantic map of the eligible papers")
    groups=sorted((g for g in clusters if int(g)>=0),key=lambda g:-clusters[g]["count"])[:8]
    if "-1" in clusters: groups.append("-1")
    handles=[Line2D([],[],marker="o",linestyle="",color=clusters[g]["color"],markersize=7,
                    label=clusters[g]["name"]+" ("+str(clusters[g]["count"])+")") for g in groups]
    if handles: ax.legend(handles=handles,loc="center left",bbox_to_anchor=(1,.5),frameon=False,
                          title="Largest topics and unassigned papers",fontsize=8,title_fontsize=8)
    save(fig,"atlas.png")
    fig,axs=plt.subplots(2,2,figsize=(10,6.8),layout="constrained")
    perm=np.random.default_rng(42).permutation(len(labels))
    from matplotlib.colors import to_hex
    alt=[("#a0a59c" if g<0 else to_hex(plt.get_cmap("tab20")(int(g)%20))) for g in A["pca_labels"]]
    for ax,xy,cols,name in zip(axs.ravel(),[A["xy"],A["pca"][:,:2],A["xy"][perm],A["pca"][:,:2]],
            [colors,colors,colors,alt],["A   UMAP · primary topics","B   PCA · primary topics",
                                        "C   Shuffled positions · primary topics","D   PCA · PCA-based topic assignments"],strict=True):
        points(ax,xy,cols,name)
    save(fig,"comparisons.png")
    rows=evaluation["seeds"]; seeds=[r["seed"] for r in rows]
    fig,axs=plt.subplots(1,2,figsize=(10,3.45),layout="constrained")
    for key,name,c in [("umap_recall","UMAP","#006e59"),("pca_recall","PCA","#aa532e"),("shuffled_recall","Shuffled","#6d7280")]:
        axs[0].plot(seeds,[r[key] for r in rows],marker="o",ms=3,label=name,color=c)
    for key,name,c in [("ari_all","ARI incl. unassigned","#5653a4"),("jointly_assigned_fraction","Jointly assigned fraction","#087966")]:
        axs[1].plot(seeds,[r[key] for r in rows],marker="o",ms=3,label=name,color=c)
    axs[0].set_title("Original neighbors retained");axs[0].set_ylabel("Mean recall at 10");axs[0].set_ylim(bottom=0)
    axs[1].set_title("Cluster stability against seed 42");axs[1].set_ylim(-.03,1.05)
    for ax in axs: ax.legend(fontsize=8,frameon=False);ax.set_xlabel("UMAP seed");ax.grid(axis="y",alpha=.18)
    save(fig,"metrics.png")
    fig,ax=plt.subplots(figsize=(10,2.25));ax.axis("off");ax.set_xlim(0,1);ax.set_ylim(0,1)
    nodes=[(.09,.5,f"alphaXiv\nlikes > {threshold}"),(.32,.5,"OpenAI\ntitle + abstract"),(.58,.8,"UMAP 2D\ndisplay"),(.58,.5,"UMAP 10D\nHDBSCAN"),(.58,.2,"Original vectors\n10 neighbors"),(.85,.5,"Luna names\nand evidence")]
    for a,b in [(0,1),(1,2),(1,3),(1,4),(3,5)]:
        x,y,_=nodes[a];u,v,_=nodes[b];ax.annotate("",xy=(u-.073,v),xytext=(x+.074,y),arrowprops={"arrowstyle":"->","color":"#578374"})
    for x,y,label in nodes:
        ax.text(x,y,label,ha="center",va="center",fontsize=9,bbox={"boxstyle":"round,pad=.5","fc":"#eef4ea","ec":"#7f9b88"})
    save(fig,"architecture.png")
