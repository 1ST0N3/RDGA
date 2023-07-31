import contextily as cx
import pandas as pd
import matplotlib.patches as mpatches
from matplotlib import pyplot as plt
from Modules.HandyFunctions import haversine
from pyproj import Transformer

def createSocialPlot(g):
    df = g.data_df

    x,y = transCoords(df.lat,df.lon)
    df["x"] = x
    df["y"] = y

    gridsize    = 100
    h_rte       = 100
    h_elv       = 30

    fig = plt.figure(figsize=(8,8))
    fig.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
        hspace = 0, wspace = 0)
    gs = fig.add_gridspec(gridsize,1,wspace=0, hspace=0,width_ratios=[1])

    ax_rte = add_rte(g,fig,gs,h_rte)
    ax_elv = add_elev_profile(fig,gs,gridsize,df,ax_rte,h_elv,h_rte)

    add_start_end(ax_rte,df)
    add_text(fig,g,ax_rte,ax_elv)
    add_basemap(ax_rte)
    add_cols(g,ax_rte,ax_elv)

    # fig.tight_layout(pad=0)
    save_as = g.name
    save_as = save_as.replace(">","")
    fig.savefig("app/Maps/" + save_as + ".png", bbox_inches='tight', pad_inches=0)
    plt.close()

def transCoords(lat,lon):
    return Transformer.from_crs("EPSG:4326","EPSG:3395").transform(lat,lon)

def add_rte(g,fig,gs,h_rte):
    df = g.data_df
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

    ax_rte.set(xlim=xlim, ylim=ylim)
    ax_rte.axis('off')
    
    return ax_rte

def add_elev_profile(fig,gs,gridsize,df,ax_rte,h_elv,h_rte):
    ax_elv = fig.add_subplot(gs[(gridsize-h_elv): , 0],zorder=1)
    altRange = max(df.alt) - min(df.alt)
    l = 0.5
    vspace = altRange * l/(1-l)
    ax_elv.plot(df.totDist,df.alt,color="white")
    ax_elv.fill_between(df.totDist,[-vspace]*len(df.alt),list(df.alt),color="black")
    yRange = max(df.alt) - -vspace
    ax_elv.set(xlim=(0,max(df.totDist)),ylim=[-vspace,max(df.alt)+0.25*yRange])
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
        ax_rte.scatter(x[-1],y[-1],color="red",zorder=10,s=100)
        ax_rte.scatter(x[0],y[0],color="green",zorder=10,s=20)

def add_text(fig,g,ax_rte,ax_elv):
    df = g.data_df
    fs = 30

    rect = mpatches.Rectangle([0,0.93],1,0.1,transform = ax_rte.transAxes,color="black",zorder=5)
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
        
        from matplotlib.patches import BoxStyle
        boxstyle = BoxStyle("Round", pad=1)
        props = {'boxstyle': boxstyle}

        t = ax_rte.text(0.5,0.96, g.name,transform = ax_rte.transAxes,
                        fontsize=fs,
                        color = "white",
                        va = "center",
                        ha = "center",
                        zorder=6)
        # ax_rte.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).width*fig.dpi
        while t.get_window_extent(renderer = fig.canvas.get_renderer()).xmin < 0:
            t.set_fontsize(t.get_fontsize()-5)

    ax_elv.text(0.2,0.25, str(round(df.totDist.iloc[-1]/1000,1)) + " km",transform = ax_elv.transAxes,
            fontsize=25,
            color = "white",
            ha = "center",
            zorder=6)

    ax_elv.text(0.2,0.06,"Distance",transform = ax_elv.transAxes,
            fontsize=20,
            color = "white",
            ha = "center",
            zorder=6)
    
    ax_elv.text(0.5,0.25,str(round(df.totDist.iloc[-1]/df.movingTime.iloc[-1]*3.6,1)) + " km/h",transform = ax_elv.transAxes,
            fontsize=25,
            color = "white",
            ha = "center",
            zorder=6)

    ax_elv.text(0.5,0.06,"Average",transform = ax_elv.transAxes,
            fontsize=20,
            color = "white",
            ha = "center",
            zorder=6)
    
    ax_elv.text(0.80,0.25,str(round(g.elevationGain)) + " m",transform = ax_elv.transAxes,
            fontsize=25,
            color = "white",
            ha = "center",
            zorder=6)

    ax_elv.text(0.80,0.06,"Elevation",transform = ax_elv.transAxes,
            fontsize=20,
            color = "white",
            ha = "center",
            zorder=6)

def add_basemap(ax_rte):
    # cx.add_basemap(ax_rte, crs="EPSG:3395",source=cx.providers.CartoDB.DarkMatter)
    cx.add_basemap(ax_rte, crs="EPSG:3395",source=cx.providers.Stamen.Terrain,zorder=0)

def add_cols(g,ax_rte,ax_elv):
    df = g.data_df

    yRange = ax_elv.get_ylim()[1] - ax_elv.get_ylim()[0]
    xRange = ax_elv.get_xlim()[1] - ax_elv.get_xlim()[0]
    y = ax_elv.get_ylim()[0] + 0.90*yRange
    ymargin = y - max(df.alt)

    cols = {
        "Adsteeg"           : {"lat" : 50.932, "lon" :  5.799,  "cat" : "4" },
        "Alpe d'Huez"       : {"lat" : 45.095, "lon" :  6.071,  "cat" : "HC"},
        "Col d'Aspin"       : {"lat" : 42.942, "lon" :  0.328,  "cat" : "2" },
        "Col d'Aubisque"    : {"lat" : 42.977, "lon" : -0.340,  "cat" : "HC"},
        "Col du Galibier"   : {"lat" : 45.064, "lon" :  6.408,  "cat" : "HC"},
        "Col du Glandon"    : {"lat" : 45.240, "lon" :  6.176,  "cat" : "HC"},
        "Bemelerberg"       : {"lat" : 50.845, "lon" :  5.773,  "cat" : "4" },
        "Bergseweg"         : {"lat" : 50.854, "lon" :  5.945,  "cat" : "4" },
        "Brocon"            : {"lat" : 46.119, "lon" : 11.689,  "cat" : "1" },
        "Bukel"             : {"lat" : 50.795, "lon" :  5.765,  "cat" : "4" },
        "Camerig"           : {"lat" : 50.765, "lon" :  5.960,  "cat" : "4" },
        "Cauberg"           : {"lat" : 50.860, "lon" :  5.823,  "cat" : "4" },
        "Eyserbosweg"       : {"lat" : 50.831, "lon" :  5.926,  "cat" : "4" },
        "Fromberg"          : {"lat" : 50.851, "lon" :  5.896,  "cat" : "4" },
        "Geulhemmerberg"    : {"lat" : 50.864, "lon" :  5.777,  "cat" : "4" },
        "Heiweg"            : {"lat" : 50.773, "lon" :  5.748,  "cat" : "4" },
        "Hellebeuk"         : {"lat" : 50.881, "lon" :  5.862,  "cat" : "4" },
        "Hommert"           : {"lat" : 50.933, "lon" :  5.914,  "cat" : "4" },
        "Hulsberg"          : {"lat" : 50.842, "lon" :  5.976,  "cat" : "4" },
        "Keunestraat"       : {"lat" : 50.828, "lon" :  5.771,  "cat" : "4" },
        "Keutenberg"        : {"lat" : 50.836, "lon" :  5.870,  "cat" : "4" },
        "Koulenberg"        : {"lat" : 50.866, "lon" :  5.879,  "cat" : "4" },
        "Kruisberg"         : {"lat" : 50.818, "lon" :  5.943,  "cat" : "4" },
        "Lange Raarberg"    : {"lat" : 50.886, "lon" :  5.776,  "cat" : "4" },
        "Loorberg"          : {"lat" : 50.774, "lon" :  5.873,  "cat" : "4" },
        "Maasberg"          : {"lat" : 50.941, "lon" :  5.757,  "cat" : "4" },
        "Passo Gobbera"     : {"lat" : 46.148, "lon" : 11.758,  "cat" : "3" },                           
        "Passo Manghen"     : {"lat" : 46.175, "lon" : 11.439,  "cat" : "HC"},
        "Passo Rolle"       : {"lat" : 46.296, "lon" : 11.786,  "cat" : "1" },
        "Telegraphe"        : {"lat" : 45.203, "lon" :  6.444,  "cat" : "1" },
        "Tourmalet"         : {"lat" : 42.908, "lon" :  0.145,  "cat" : "HC"},
        "Schweiberg"        : {"lat" : 50.773, "lon" :  5.885,  "cat" : "4" },
        "Soulor"            : {"lat" : 42.961, "lon" : -0.261,  "cat" : "HC"},
        "Sweikhuizerberg"   : {"lat" : 50.952, "lon" :  5.855,  "cat" : "4" },
        "Vaalserberg"       : {"lat" : 50.758, "lon" :  6.017,  "cat" : "4" },
    }

    peakPoints = []

    for col in cols.keys():
        peakPoints.append(getPeak(df,cols[col],col))

    allPoints = pd.concat(peakPoints, axis=0).sort_index()
    if len(allPoints) > 6:
        allPoints.cat = range(1,len(allPoints)+1)
    allPoints["diff"]   = allPoints.totDist.diff()
    pointsMap           = allPoints.drop_duplicates(subset=["name"])
    # pointsProfile   = allPoints[(abs(allPoints.totDist.diff()) > 1E3) | (allPoints.totDist.diff().isnull())]
    
    labels = []

    y_prev = 0
    for i,point in allPoints.iterrows():
        y = point.alt+ymargin
        if point["diff"] < 0.03*xRange and y*1.1>y_prev:
            y = y_prev+0.12*yRange

        ax_elv.scatter(point.totDist,y,color="white",s=300,zorder=2,edgecolor='black', linewidth=1,label = str(point["cat"]) + " : " + point["name"])
        l = ax_elv.text(point.totDist,y,point["cat"],va="center_baseline",ha="center",zorder=2,label = point.name)
        ax_elv.plot([point.totDist,point.totDist],[y,point.alt],ls="--",color="black",lw=1,zorder=1)

        labels.append(l)
        y_prev = y

    for i,point in pointsMap.iterrows():
        ax_rte.scatter(point.x,point.y,color="white",s=300,zorder=2,edgecolor='black', linewidth=1)
        ax_rte.text(point.x,point.y,point["cat"],va="center_baseline",ha="center",zorder=3)

    if len(allPoints) > 6:
        h,l = ax_elv.get_legend_handles_labels()
        ax_rte.legend(h,l,loc="right",markerscale=0.5,fontsize=8.5,bbox_to_anchor=(1.006,0.607),labelcolor="white",facecolor = 'black')

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
            df_new = df_new.append(point)

    df_new["cat"] = peak["cat"]
    df_new["name"] = colname

    return df_new




