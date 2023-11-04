import contextily as cx
import pandas as pd
import matplotlib.patches as mpatches
from matplotlib import pyplot as plt
from handyFunctions import *
from pyproj import Transformer
from json import loads
from PIL import Image
import datetime


class SocialPlot():

    def __init__(self,g,plotSpecs=None):
        self.name           = g.name
        self.df             = g.df
        self.elevationGain  = g.elevationGain
        self.ps             = plotSpecs

        x,y = transCoords(self.df.lat,self.df.lon)
        self.df["x"] = x
        self.df["y"] = y

        self.gridsize    = 100
        self.h_rte       = 100
        self.h_elv       = 40

        self.fraq_text    = 0.15
        self.margin       = 0.05
        self.topBarHeight = self.fraq_text - self.margin

        self.fig_height = 14.4
        self.fig_width = 14.4

        self.fig = plt.figure(figsize=(self.fig_height,self.fig_width))
        self.fig.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0,
                                 hspace = 0, wspace = 0)
        self.gs = self.fig.add_gridspec(self.gridsize,1,wspace=0, hspace=0,width_ratios=[1])

        self.add_rte()
        self.add_elev_profile()

        self.add_start_end()
        self.add_text()
        self.add_cols()
        self.add_Inset()

        self.add_basemap()

        path = "Output/Figures/SocialPlots/"
        checkDir(path)
        saveAs = path+self.name+".png"
        saveAs = saveAs.replace(">","")
        saveAs = saveAs.replace(":","")

        self.fig.savefig(saveAs, bbox_inches='tight', pad_inches=0)
        plt.close()

    def add_rte(self):
        self.ax_rte = self.fig.add_subplot(self.gs[:self.h_rte, 0],zorder=0)
        self.ax_rte.patch.set_alpha(0.0)
        l = self.ax_rte.plot(self.df.x,self.df.y,color="black",lw=4)

        xRange = max(self.df.x)-min(self.df.x)
        yRange = max(self.df.y)-min(self.df.y)

        if xRange < yRange*1.2:
            u = self.fraq_text
            l = 0.3

            upper = yRange*u/(1-u-l)
            lower = yRange*l/(1-u-l)

            self.ylim = [min(self.df.y) - lower, max(self.df.y) + upper]
            yLimRange = self.ylim[1] - self.ylim[0]
            xMean = min(self.df.x) + (max(self.df.x)-min(self.df.x))/2
            self.xlim = [xMean-yLimRange/2,xMean+yLimRange/2]
        else:

            u = self.fraq_text
            l = 0.25

            upper = yRange*u/(1-u-l)
            lower = yRange*l/(1-u-l)

            self.xlim = [min(self.df.x)-0.05*xRange,max(self.df.x)+0.05*xRange]
            xLimRange = self.xlim[1] - self.xlim[0]
            yMean = (min(self.df.y) + 0.75*(max(self.df.y)-min(self.df.y))/2)

            self.ylim = [yMean-xLimRange/2,yMean+xLimRange/2]

        if "Amstel" in self.name:
            xlim_shift = -0.1
            xRange = self.xlim[1] - self.xlim[0]
            self.xlim = [self.xlim[0]-xlim_shift*xRange,self.xlim[1]-xlim_shift*xRange]

        if self.ps is not None and not np.isnan(self.ps.offset_x): self.xlim = np.array(self.xlim)-self.ps.offset_x
        if self.ps is not None and not np.isnan(self.ps.offset_y): self.ylim = np.array(self.ylim)-self.ps.offset_y

        self.ax_rte.set(xlim=self.xlim, ylim=self.ylim)
        self.ax_rte.axis('off')

    def add_elev_profile(self):
        self.ax_elv = self.fig.add_subplot(self.gs[(self.gridsize-self.h_elv): , 0],zorder=1)
        altRange = max(self.df.alt) - min(self.df.alt)
        l = 0.5
        vspace = altRange * l/(1-l)
        yRange = max(self.df.alt) - -vspace
        ylim = [-1100,3500]
        self.ax_elv.plot(self.df.totDist,self.df.alt,color="white")
        # ax_elv.fill_between(df.totDist,[-vspace]*len(df.alt),list(df.alt),color="black")
        self.ax_elv.fill_between(self.df.totDist,ylim[0],list(self.df.alt),color="black")
        # ylim = [-vspace,max(df.alt)+0.25*yRange]
        self.ax_elv.set(xlim=(0,max(self.df.totDist)),ylim=ylim)
        self.ax_elv.patch.set_alpha(0.0)

        self.ax_rte.set_aspect(1)
        x_rte = (self.ax_rte.get_xlim()[1]-self.ax_rte.get_xlim()[0])
        y_rte = (self.ax_rte.get_ylim()[1]-self.ax_rte.get_ylim()[0])
        y_elv = (self.ax_elv.get_ylim()[1]-self.ax_elv.get_ylim()[0])
        x_elv = (self.ax_elv.get_xlim()[1]-self.ax_elv.get_xlim()[0])
        self.ax_elv.set_aspect(self.h_elv/self.h_rte*y_rte/x_rte*x_elv/y_elv)

        self.ax_elv.axis("off")

    def add_start_end(self):
        coveredDist = haversine(self.df[["lat","lon"]].iloc[0],
                                self.df[["lat","lon"]].iloc[-1])

        size = 300

        lat = self.df.lat
        lon = self.df.lon
        x,y = transCoords(lat,lon)

        if coveredDist < 100:
            self.ax_rte.scatter(x[0],y[0],color="red",zorder=10,s=size)
            self.ax_rte.scatter(x[0],y[0],color="green",zorder=10,s=size/5)
        else:
            self.ax_rte.scatter(x[-1],y[-1],color="red",zorder=10,s=size)
            self.ax_rte.scatter(x[0],y[0],color="green",zorder=10,s=size)

    def add_text(self):
        fsTop = 38
        fsBottom1 = 33
        fsBottom2 = 28

        rect = mpatches.Rectangle([0,1-self.topBarHeight],1,self.topBarHeight,transform = self.ax_rte.transAxes,color="black",zorder=5,lw=0)
        self.ax_rte.add_patch(rect)

        yTopText = 1-self.topBarHeight*0.55
        yBottomText1 = 0.12
        yBottomText2 = 0.04

        if "Amel" in self.name:
            self.ax_rte.text(0.14,yTopText, "AMSTEL",transform = self.ax_rte.transAxes,
                    fontsize=fsTop,
                    color = (238/255,39/255,34/255),
                    va = "center",
                    ha = "left",
                    zorder=6)

            self.ax_rte.text(0.545,yTopText, "GOLD",transform = self.ax_rte.transAxes,
                    fontsize=fsTop,
                    color = (248/255,156/255,14/255),
                    va = "center",
                    ha = "center",
                    zorder=6)

            self.ax_rte.text(0.86,yTopText, "RACE",transform = self.ax_rte.transAxes,
                    fontsize=fsTop,
                    color = (0/255,0/255,00/255),
                    va = "center",
                    ha = "right",
                    zorder=6)
        else:
            title = self.name
            title = title.replace("->",u"\u2192")

            t = self.ax_rte.text(0.5,yTopText, title,transform = self.ax_rte.transAxes,
                            fontsize=fsTop,
                            color = "white",
                            va = "center",
                            ha = "center",
                            zorder=6)
            # ax_rte.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).width*fig.dpi
            if t.get_window_extent(renderer = self.fig.canvas.get_renderer()).xmin < 0:
                sTitle = title.split(" ")
                cutIdx = 3
                titleTop = " ".join(sTitle[:cutIdx])
                titleBottom = " ".join(sTitle[cutIdx:])
                title = titleTop + "\n" + titleBottom
                t.set_text(title)

        # Distance
        self.ax_elv.text(0.2,yBottomText1, str(round(self.df.totDist.iloc[-1]/1000,1)) + " km",transform = self.ax_elv.transAxes,
                         fontsize=fsBottom1,
                         color = "white",
                         ha = "center",
                         zorder=6)

        self.ax_elv.text(0.2,yBottomText2,"Distance",transform = self.ax_elv.transAxes,
                         fontsize=fsBottom2,
                         color = "white",
                         ha = "center",
                         zorder=6)

        # # Average
        # ax_elv.text(0.5,0.14,str(round(df.totDist.iloc[-1]/df.movingTime.iloc[-1]*3.6,1)) + " km/h",transform = ax_elv.transAxes,
        #         fontsize=fsBottom1,
        #         color = "white",
        #         ha = "center",
        #         zorder=6)

        # ax_elv.text(0.5,0.06,"Average",transform = ax_elv.transAxes,
        #         fontsize=fsBottom2,
        #         color = "white",
        #         ha = "center",
        #         zorder=6)

        # Moving time
        self.ax_elv.text(0.5,yBottomText1,str(datetime.timedelta(seconds=self.df.movingTime.iloc[-1])),transform = self.ax_elv.transAxes,
                         fontsize=fsBottom1,
                         color = "white",
                         ha = "center",
                         zorder=6)

        self.ax_elv.text(0.5,yBottomText2,"Moving time",transform = self.ax_elv.transAxes,
                         fontsize=fsBottom2,
                         color = "white",
                         ha = "center",
                         zorder=6)

        # Elevation Gain
        self.ax_elv.text(0.80,yBottomText1,str(round(self.elevationGain)) + " m",transform = self.ax_elv.transAxes,
                         fontsize=fsBottom1,
                         color = "white",
                         ha = "center",
                         zorder=6)

        self.ax_elv.text(0.80,yBottomText2,"Elevation gain",transform = self.ax_elv.transAxes,
                         fontsize=fsBottom2,
                         color = "white",
                         ha = "center",
                         zorder=6)

    def add_basemap(self):
        # cx.add_basemap(self.ax_rte, crs="EPSG:3395",source=cx.providers.CartoDB.DarkMatter)

        # src = cx.providers.Stadia.StamenTerrain
        # src["url"] = src.url + "?api_key=6af2cccf-6d29-4b28-ae30-4842f2a0133a"
        # cx.add_basemap(self.ax_rte, crs="EPSG:3395",source=src,zorder=0)
        # cx.add_basemap(self.ax_rte, crs="EPSG:3395",source=cx.providers.Esri.WorldImagery,zorder=0)
        cx.add_basemap(self.ax_rte, crs="EPSG:3395",source=cx.providers.OpenTopoMap,zorder=0,zoom=11)

    def add_cols(self):

        # pointsProfile   = allPoints[(abs(allPoints.totDist.diff()) > 1E3) | (allPoints.totDist.diff().isnull())]

        allPoints = get_cols(self.df)
        pointsMap           = allPoints.drop_duplicates(subset=["name"])
        labels = []

        yRange = self.ax_elv.get_ylim()[1] - self.ax_elv.get_ylim()[0]
        xRange = self.ax_elv.get_xlim()[1] - self.ax_elv.get_xlim()[0]
        y = self.ax_elv.get_ylim()[0] + 0.90*yRange
        ymargin = y - max(self.df.alt)
        ymargin = 400

        y_prev = 0
        for i,point in allPoints.iterrows():
            y = point.alt+ymargin
            if abs(point["diff"]) < 0.03*xRange and y*1.1>y_prev:
                y = y_prev+0.12*yRange

            self.ax_elv.scatter(point.totDist,y,color="white",s=1200,zorder=2,edgecolor='black', linewidth=1,label = str(point["cat"]) + " : " + point["name"])
            l = self.ax_elv.text(point.totDist,y,point["cat"],va="center_baseline",ha="center",zorder=2,label = point.name,fontsize=20)
            self.ax_elv.plot([point.totDist,point.totDist],[y,point.alt],ls="--",color="black",lw=1,zorder=1)


            if True:
                l = self.ax_elv.text(point.totDist,y,"    " + point["name"],
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

        if self.ax_rte is not None:
            for i,point in pointsMap.iterrows():
                self.ax_rte.scatter(point.x,point.y,color="white",s=1200,zorder=2,edgecolor='black', linewidth=1)
                self.ax_rte.text(point.x,point.y,point["cat"],va="center_baseline",ha="center",zorder=3,fontsize=20)

            if len(allPoints) > 6:
                h,l = self.ax_elv.get_legend_handles_labels()
                self.ax_rte.legend(h,l,loc="right",markerscale=0.5,fontsize=8.5,bbox_to_anchor=(1.006,0.607),labelcolor="white",facecolor = 'black')

    def add_Inset(self):
        xlimCust = [600000, 1100000]
        ylimCust = [5030000,6050000]
        xRange = xlimCust[1] - xlimCust[0]
        yRange = ylimCust[1] - ylimCust[0]

        insetHeight = 0.5-self.topBarHeight

        width = xRange/yRange*insetHeight

        # topleft default pos
        xpos = 0
        ypos = 0.5

        if self.ps is not None and not np.isnan(self.ps.insetPosition_x) and self.ps.insetPosition_x == "right": xpos = 1-width
        if self.ps is not None and not np.isnan(self.ps.insetPosition_y): ypos = self.ps.insetPosition_y

        self.ax_inset = self.ax_rte.inset_axes([xpos, ypos, width, insetHeight], xlim=xlimCust, ylim=ylimCust, xticklabels=[], yticklabels=[])
        self.ax_inset.plot([self.xlim[0],self.xlim[1],self.xlim[1],self.xlim[0],self.xlim[0]],
                           [self.ylim[0],self.ylim[0],self.ylim[1],self.ylim[1],self.ylim[0]],color="k")

        # src = cx.providers.Stadia.StamenTerrain
        # src["url"] = src.url + "?api_key=6af2cccf-6d29-4b28-ae30-4842f2a0133a"

        # src = cx.providers.CartoDB.DarkMatterNoLabels

        # src = cx.providers.CartoDB.PositronNoLabels
        src = cx.providers.CartoDB.Voyager
        # src = cx.providers.CartoDB.Positron
        cx.add_basemap(self.ax_inset, crs="EPSG:3395",source=src,zorder=0)
        self.ax_inset.texts[-1].remove()

        self.ax_inset.axis('off')

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

def transCoords(lat,lon):
    return Transformer.from_crs("EPSG:4326","EPSG:3395").transform(lat,lon)
