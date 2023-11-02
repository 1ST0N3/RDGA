import contextily as cx
import pandas as pd
import matplotlib.patches as mpatches
from matplotlib import pyplot as plt
from handyFunctions import *
from pyproj import Transformer
from json import loads
from PIL import Image
import datetime

def createSocialPlot(g,offset=None):
    df = g.df

    x,y = transCoords(df.lat,df.lon)
    df["x"] = x
    df["y"] = y

    gridsize    = 100
    h_rte       = 100
    h_elv       = 40

    fig = plt.figure(figsize=(14.4,14.4))
    fig.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0,
                        hspace = 0, wspace = 0)
    gs = fig.add_gridspec(gridsize,1,wspace=0, hspace=0,width_ratios=[1])

    ax_rte,xlim,ylim = add_rte(g,fig,gs,h_rte,offset)
    ax_elv = add_elev_profile(fig,gs,gridsize,df,ax_rte,h_elv,h_rte)
    add_Inset(ax_rte,xlim,ylim)

    add_start_end(ax_rte,df)
    add_text(fig,g,ax_rte,ax_elv)
    add_cols(df,ax_rte,ax_elv)

    add_basemap(ax_rte)

    path = "Output/Figures/"+g.name+"/"
    path = path.replace(">","")
    path = path.replace(":","")
    checkDir(path)
    saveAs = path+"socialPlot.png"

    fig.savefig(saveAs, bbox_inches='tight', pad_inches=0)
    plt.close()

def transCoords(lat,lon):
    return Transformer.from_crs("EPSG:4326","EPSG:3395").transform(lat,lon)

def add_rte(g,fig,gs,h_rte,offset=None):
    df = g.df
    lat = df.lat
    lon = df.lon

    ax_rte = fig.add_subplot(gs[:h_rte, 0],zorder=0)
    ax_rte.patch.set_alpha(0.0)
    l = ax_rte.plot(df.x,df.y,color="black",lw=2)

    xRange = max(df.x)-min(df.x)
    yRange = max(df.y)-min(df.y)

    if xRange < yRange*1.2:
        u = 0.10
        l = 0.3

        upper = yRange*u/(1-u-l)
        lower = yRange*l/(1-u-l)

        ylim = [min(df.y) - lower, max(df.y) + upper]
        yLimRange = ylim[1] - ylim[0]
        xMean = min(df.x) + (max(df.x)-min(df.x))/2
        xlim = [xMean-yLimRange/2,xMean+yLimRange/2]
    else:

        u = 0.10
        l = 0.25

        upper = yRange*u/(1-u-l)
        lower = yRange*l/(1-u-l)

        xlim = [min(df.x)-0.05*xRange,max(df.x)+0.05*xRange]
        xLimRange = xlim[1] - xlim[0]
        yMean = (min(df.y) + 0.75*(max(df.y)-min(df.y))/2)

        # ylim = [max(df.y) - xLimRange,max(df.y) + upper]
        ylim = [yMean-xLimRange/2,yMean+xLimRange/2]

    if "Amstel" in g.name:
        xlim_shift = -0.1
        xRange = xlim[1] - xlim[0]
        xlim = [xlim[0]-xlim_shift*xRange,xlim[1]-xlim_shift*xRange]

    if offset is not None:
        xlim = np.array(xlim)-offset[0]
        ylim = np.array(ylim)-offset[1]


    ax_rte.set(xlim=xlim, ylim=ylim)
    ax_rte.axis('off')

    return ax_rte,xlim,ylim

def add_elev_profile(fig,gs,gridsize,df,ax_rte,h_elv,h_rte):
    ax_elv = fig.add_subplot(gs[(gridsize-h_elv): , 0],zorder=1)
    altRange = max(df.alt) - min(df.alt)
    l = 0.5
    vspace = altRange * l/(1-l)
    yRange = max(df.alt) - -vspace
    ylim = [-1100,3500]
    ax_elv.plot(df.totDist,df.alt,color="white")
    # ax_elv.fill_between(df.totDist,[-vspace]*len(df.alt),list(df.alt),color="black")
    ax_elv.fill_between(df.totDist,ylim[0],list(df.alt),color="black")
    # ylim = [-vspace,max(df.alt)+0.25*yRange]
    ax_elv.set(xlim=(0,max(df.totDist)),ylim=ylim)
    ax_elv.patch.set_alpha(0.0)

    ax_rte.set_aspect(1)
    x_rte = (ax_rte.get_xlim()[1]-ax_rte.get_xlim()[0])
    y_rte = (ax_rte.get_ylim()[1]-ax_rte.get_ylim()[0])
    y_elv = (ax_elv.get_ylim()[1]-ax_elv.get_ylim()[0])
    x_elv = (ax_elv.get_xlim()[1]-ax_elv.get_xlim()[0])
    ax_elv.set_aspect(h_elv/h_rte*y_rte/x_rte*x_elv/y_elv)

    ax_elv.axis("off")

    return ax_elv

def add_start_end(ax_rte,df):
    coveredDist = haversine(df[["lat","lon"]].iloc[0],
                            df[["lat","lon"]].iloc[-1])

    lat = df.lat
    lon = df.lon
    x,y = transCoords(lat,lon)

    if coveredDist < 100:
        ax_rte.scatter(x[0],y[0],color="red",zorder=10,s=100)
        ax_rte.scatter(x[0],y[0],color="green",zorder=10,s=20)
    else:
        ax_rte.scatter(x[-1],y[-1],color="red",zorder=10,s=200)
        ax_rte.scatter(x[0],y[0],color="green",zorder=10,s=200)

def add_text(fig,g,ax_rte,ax_elv):
    df = g.df
    fs = 30

    rect = mpatches.Rectangle([0,0.93],1,0.07,transform = ax_rte.transAxes,color="black",zorder=5,lw=0)
    ax_rte.add_patch(rect)

    if "Amel" in g.name:
        ax_rte.text(0.14,0.96, "AMSTEL",transform = ax_rte.transAxes,
                fontsize=fs,
                color = (238/255,39/255,34/255),
                va = "center",
                ha = "left",
                zorder=6)

        ax_rte.text(0.545,0.96, "GOLD",transform = ax_rte.transAxes,
                fontsize=fs,
                color = (248/255,156/255,14/255),
                va = "center",
                ha = "center",
                zorder=6)

        ax_rte.text(0.86,0.96, "RACE",transform = ax_rte.transAxes,
                fontsize=fs,
                color = (0/255,0/255,00/255),
                va = "center",
                ha = "right",
                zorder=6)
    else:
        title = g.name
        title = title.replace("->",u"\u2192")

        t = ax_rte.text(0.5,0.96, title,transform = ax_rte.transAxes,
                        fontsize=fs,
                        color = "white",
                        va = "center",
                        ha = "center",
                        zorder=6)
        # ax_rte.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).width*fig.dpi
        while t.get_window_extent(renderer = fig.canvas.get_renderer()).xmin < 0:
            t.set_fontsize(t.get_fontsize()-5)

    # Distance
    ax_elv.text(0.2,0.12, str(round(df.totDist.iloc[-1]/1000,1)) + " km",transform = ax_elv.transAxes,
            fontsize=25,
            color = "white",
            ha = "center",
            zorder=6)

    ax_elv.text(0.2,0.06,"Distance",transform = ax_elv.transAxes,
            fontsize=20,
            color = "white",
            ha = "center",
            zorder=6)

    # # Average
    # ax_elv.text(0.5,0.14,str(round(df.totDist.iloc[-1]/df.movingTime.iloc[-1]*3.6,1)) + " km/h",transform = ax_elv.transAxes,
    #         fontsize=25,
    #         color = "white",
    #         ha = "center",
    #         zorder=6)

    # ax_elv.text(0.5,0.06,"Average",transform = ax_elv.transAxes,
    #         fontsize=20,
    #         color = "white",
    #         ha = "center",
    #         zorder=6)

    # Moving time
    ax_elv.text(0.5,0.14,str(datetime.timedelta(seconds=df.movingTime.iloc[-1])),transform = ax_elv.transAxes,
            fontsize=25,
            color = "white",
            ha = "center",
            zorder=6)

    ax_elv.text(0.5,0.06,"Moving time",transform = ax_elv.transAxes,
            fontsize=20,
            color = "white",
            ha = "center",
            zorder=6)

    # Elevation Gain
    ax_elv.text(0.80,0.13,str(round(g.elevationGain)) + " m",transform = ax_elv.transAxes,
            fontsize=25,
            color = "white",
            ha = "center",
            zorder=6)

    ax_elv.text(0.80,0.06,"Elevation gain",transform = ax_elv.transAxes,
            fontsize=20,
            color = "white",
            ha = "center",
            zorder=6)

def add_basemap(ax_rte):
    # cx.add_basemap(ax_rte, crs="EPSG:3395",source=cx.providers.CartoDB.DarkMatter)

    # src = cx.providers.Stadia.StamenTerrain
    # src["url"] = src.url + "?api_key=6af2cccf-6d29-4b28-ae30-4842f2a0133a"
    # cx.add_basemap(ax_rte, crs="EPSG:3395",source=src,zorder=0)
    # cx.add_basemap(ax_rte, crs="EPSG:3395",source=cx.providers.Esri.WorldImagery,zorder=0)
    cx.add_basemap(ax_rte, crs="EPSG:3395",source=cx.providers.OpenTopoMap,zorder=0)

def add_cols(df,ax_rte=None,ax_elv=None):

    # pointsProfile   = allPoints[(abs(allPoints.totDist.diff()) > 1E3) | (allPoints.totDist.diff().isnull())]

    allPoints = get_cols(df)
    pointsMap           = allPoints.drop_duplicates(subset=["name"])
    labels = []

    yRange = ax_elv.get_ylim()[1] - ax_elv.get_ylim()[0]
    xRange = ax_elv.get_xlim()[1] - ax_elv.get_xlim()[0]
    y = ax_elv.get_ylim()[0] + 0.90*yRange
    ymargin = y - max(df.alt)
    ymargin = 400

    y_prev = 0
    for i,point in allPoints.iterrows():
        y = point.alt+ymargin
        if abs(point["diff"]) < 0.03*xRange and y*1.1>y_prev:
            y = y_prev+0.12*yRange

        ax_elv.scatter(point.totDist,y,color="white",s=1200,zorder=2,edgecolor='black', linewidth=1,label = str(point["cat"]) + " : " + point["name"])
        l = ax_elv.text(point.totDist,y,point["cat"],va="center_baseline",ha="center",zorder=2,label = point.name,fontsize=20)
        ax_elv.plot([point.totDist,point.totDist],[y,point.alt],ls="--",color="black",lw=1,zorder=1)


        if True:
            l = ax_elv.text(point.totDist,y,"    " + point["name"],
                        fontsize=20,
                        va="center_baseline",
                        ha="left",
                        zorder=1,
                        rotation=40,
                        rotation_mode="anchor",
                        color = "white",
                        bbox=dict(facecolor='#2a2c30',pad=5,boxstyle='round,pad=0.2'))

        labels.append(l)
        y_prev = y

    if ax_rte is not None:
        for i,point in pointsMap.iterrows():
            ax_rte.scatter(point.x,point.y,color="white",s=1200,zorder=2,edgecolor='black', linewidth=1)
            ax_rte.text(point.x,point.y,point["cat"],va="center_baseline",ha="center",zorder=3,fontsize=20)

        if len(allPoints) > 6:
            h,l = ax_elv.get_legend_handles_labels()
            ax_rte.legend(h,l,loc="right",markerscale=0.5,fontsize=8.5,bbox_to_anchor=(1.006,0.607),labelcolor="white",facecolor = 'black')

    return allPoints

def get_cols(df):

    cols = loads(open("Data/cols.json",encoding="utf-8").read())
    peakPoints = []
    for col in cols.keys():
        peakPoints.append(getPeak(df,cols[col],col))

    allPoints = pd.concat(peakPoints, axis=0).sort_index()
    if len(allPoints) > 6:
        allPoints.cat = range(1,len(allPoints)+1)
    allPoints["diff"]   = allPoints.totDist.diff()

    return allPoints

def getPeak(df,peak,colname,range=0.002):

    lat_lower = peak["lat"]-range
    lat_upper = peak["lat"]+range
    lon_lower = peak["lon"]-range
    lon_upper = peak["lon"]+range

    mask = (lat_lower < df.lat) & (df.lat < lat_upper) & (lon_lower < df.lon) & (df.lon < lon_upper)

    points = df[mask].copy()
    points = points.sort_values(by=['alt'], ascending=False)

    df_new = pd.DataFrame(columns=df.keys())

    for i,point in points.iterrows():
        if len(df_new) == 0 or sum((point.totDist-3E3 < df_new.totDist) & (df_new.totDist < point.totDist+3E3)) == 0:
            df_new.loc[len(df_new)] = point

    df_new["cat"] = peak["cat"]
    df_new["name"] = colname

    return df_new

def add_Inset(ax_rte,xlim,ylim):
    # xrange = xlim[1]-xlim[0]
    # yrange = ylim[1]-ylim[0]

    zoom = 15
    # xlimCust = [xlim[0]-zoom*xrange,xlim[1]+zoom*xrange]
    # ylimCust = [ylim[0]-zoom*yrange,ylim[1]+zoom*yrange]

    xlimCust = [600000, 1000000]
    ylimCust = [5342020,5862488]

    xRange = xlimCust[1] - xlimCust[0]
    yRange = ylimCust[1] - ylimCust[0]

    width = xRange/yRange*0.43

    ax_inset = ax_rte.inset_axes([0, 0.5, width, 0.43], xlim=xlimCust, ylim=ylimCust, xticklabels=[], yticklabels=[])

    # src = cx.providers.Stadia.StamenTerrain
    # src["url"] = src.url + "?api_key=6af2cccf-6d29-4b28-ae30-4842f2a0133a"

    # src = cx.providers.CartoDB.DarkMatterNoLabels
    # src = cx.providers.CartoDB.PositronNoLabels
    ax_inset.plot([xlim[0],xlim[1],xlim[1],xlim[0],xlim[0]],
                  [ylim[0],ylim[0],ylim[1],ylim[1],ylim[0]],color="k")


    src = cx.providers.CartoDB.Positron
    cx.add_basemap(ax_inset, crs="EPSG:3395",source=src,zorder=0)
    ax_inset.texts[-1].remove()

    ax_inset.axis('off')

def createElevPlotInsta(obj):
    fig,ax = plt.subplots(figsize=(14.4,14.4))

    ax_rte = fig.add_subplot(111)

    ymin = -800
    fontsize = 20

    ax.fill_between(obj.df.totDist,[ymin]*len(obj.df.alt),obj.df.alt,color="#2a2c30")
    ax.plot(obj.df.totDist,obj.df.alt,color="white")
    ax.set_xlim(0,obj.df.totDist.iloc[-1])
    ax.set_ylim(ymin,8000)

    allCols = get_cols(obj.df)

    yRange = ax.get_ylim()[1] - ax.get_ylim()[0]
    ymargin = 0.04*yRange

    for i,col in allCols.iterrows():
        y = col.alt+ymargin
        ax.scatter(col.totDist,y,color="white",s=1200,zorder=2,edgecolor='black', linewidth=1,label = str(col["cat"]) + " : " + col["name"])
        l = ax.text(col.totDist,y,col["cat"],va="center_baseline",ha="center",zorder=2,label = col["name"],fontsize=fontsize)
        ax.plot([col.totDist,col.totDist],[y,col.alt],ls="--",color="black",lw=1,zorder=1)

        l = ax.text(col.totDist,y,"    " + col["name"],
                    fontsize=fontsize,
                    va="center_baseline",
                    ha="left",
                    zorder=1,
                    rotation=40,
                    rotation_mode="anchor",
                    color = "white",
                    bbox=dict(facecolor='#2a2c30',pad=5,boxstyle='round,pad=0.2'))


    im = Image.open('Data/Icons/mountain.png')
    height = im.size[1]
    fig.figimage(im, 0, fig.bbox.ymax - height)

    ax.axis('off')
    path = "Output/ElevPlot/"
    checkDir(path)
    saveAs = path+obj.name+".png"
    saveAs = saveAs.replace(">","")
    saveAs = saveAs.replace(":","")
    fig.tight_layout(pad=0, w_pad=0, h_pad=0)
    fig.savefig(saveAs, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()

