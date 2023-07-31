"""
Stijn van Selling

-------------------------PROGRAM TO ANALYSE GPS DATA-------------------------

Since every item in the list is documented like this:
    
    <trkpt lat="47.0128540" lon="10.2943180">
    <ele>1354.48</ele>
    <time>2018-02-10T08:31:29.998+01:00</time>
    </trkpt>
"""
import glob
import os
import pickle
import numpy as np
import pandas as pd

from GPX import GPX
from FoliumClass import FoliumClass

def add_Campings(fol):
    campingData = pd.read_csv("Data/campings.csv",delimiter=";")

    space = "&nbsp;"

    campings_pref = ["Camping Du Chalelet", # 1
                     "Camping Municipal des Thézières", # 2
                    #  "Camping Domelin - Onlycamp", # 3
                     "Camping Chantalouette", # 3
                     "Camping Huttopia Bourg Saint Maurice", # 4
                     "Camping d'Orelle", # 5
                     "Camping les 2 glaciers", # 6
                     "Camping le Planet", # 7
                     "Camping du plan d'eau", # 8
                     "CAMPING DOMAINE SAINTE MADELEINE", # 9
                     "Camping de La Laune"] # Dichtbij Nice

    for i,camping in campingData.iterrows():
        popup = "<p style='font-family:Courier;'>"
        popup += "<b>"+camping.Naam+"</b>"
        popup += "<br><b>Site"+1*space+": </b><a href='" + camping.site + "' target='_blank'>Link</a>"
        popup += "<br><b>Tel"+2*space+": </b>" + "+" + str(camping.tel)
        popup += "</p>"

        if camping.Naam in campings_pref:
            icon = "tent_special"
            group = "Campings"
            show = True
        else:
            icon = "tent"
            group = "Campings Backup"
            show = False
        fol.scatter(camping[["lat","lon"]],color="purple",group_name=group,popup=[popup],icon=icon,show=show)

def add_Supermarkets(fol):
    supermarketData  = pd.read_csv("Data/supermarkets.csv",delimiter=";",index_col=None)

    for i,supermarket in supermarketData.iterrows():
        popup = "<p style='font-family:Courier;'>"
        popup += "<b>"+supermarket.Naam+"</b>"
        popup += "</p>"

        icon = "shop"
        fol.scatter(supermarket[["lat","lon"]],group_name="Supermarkets",popup=[popup],icon=icon,show=False)

def add_Fountains(fol):
    supermarketData  = pd.read_csv("Data/waterpoints.csv",delimiter=";",index_col=None)

    for i,supermarket in supermarketData.iterrows():
        popup = "<p style='font-family:Courier;'>"
        popup += "<b>"+supermarket.Naam+"</b>"
        popup += "</p>"

        icon = "water"
        if supermarket.Naam == "WC":
            icon = "WC"
        fol.scatter(supermarket[["lat","lon"]],group_name="Waterpoints",popup=[popup],icon=icon,show=False)

def add_Cols(fol,colData):

    for i,col in colData.iterrows():
        popup = "<p style='font-family:Courier;'>"
        popup += "<a href='" + col.URL + "' target='_blank'>"+col.Naam+"</a>"
        popup += "</p>"

        icon = "CAT_" + col.Cat
        fol.scatter(col[["lat","lon"]],group_name="Cols",popup=[popup],icon=icon,show=False)

def draw_on_map_folium(obj_lst, save_name="Strava_folium.html"):
    lat = obj_lst[-1].data_df.lat
    lon = obj_lst[-1].data_df.lon

    mean_lat = min(lat) + (max(lat) - min(lat)) / 2
    mean_lon = min(lon) + (max(lon) - min(lon)) / 2

    colData         = pd.read_csv("Data/cols.csv",delimiter=";",index_col=None)
    stageData       = pd.read_csv("Data/etappes.csv",delimiter=";",index_col=None).T
    stageData.columns = stageData.iloc[0]

    fol = FoliumClass("",[mean_lat, mean_lon],7)

    add_Campings(fol)
    add_Supermarkets(fol)
    add_Cols(fol,colData)
    add_Fountains(fol)

    obj_lst = [obj_lst[-1]] + obj_lst[:-3] + [obj_lst[-2]] + [obj_lst[-3]]
    space = "&nbsp;"

    for obj in obj_lst:
        if "Stage" in obj.name:
            col = "red"
            alpha = 1
            sd = stageData[stageData.Etappe == obj.name[11:]]
            startPop  = sd.Van.iloc[0]
            finishPop = sd.Naar.iloc[0]
            if not pd.isna(sd.Cols).iloc[0]:
                cols = sd.Cols.iloc[0].split(",")
                cols = ["<a href='" + colData[colData.Naam == col].URL.iloc[0] + "' target='_blank'>"+col+"</a>" for col in cols]

            popup = "<p style='font-family:Courier;'>"
            popup += "<a href='" + sd.Route.iloc[0] + "' target='_blank'><b>Stage " + obj.name[11:] + "</b></a>"
            popup += "<br><b>Start"+5*space+": </b>"+startPop
            popup += "<br><b>Finish"+4*space+": </b>"+finishPop
            popup += "<br><b>Distance"+2*space+": </b>"+sd.KM.iloc[0] + " KM"
            popup += "<br><b>Elevation"+1*space+": </b>"+sd.HM.iloc[0] + " M"
            if not pd.isna(sd.Cols).iloc[0]:
                popup += "<br><b>Cols"+6*space+": </b>"+("<br>"+space*12).join(cols)
            popup += "</p>"
        else:
            col = "black"
            alpha = 0.5
            startPop  = "Start RGDA"
            finishPop = "Finish RGDA"
            popup = "<b>" + obj.name + "</b>"
            
        fol.plot(obj.data_df[["lat","lon"]],color=col,group_name=obj.name,opacity=alpha,popup=popup)
        fol.scatter(obj.data_df[["lat","lon"]].iloc[0],color="blue",group_name=obj.name,popup=[startPop])
        fol.scatter(obj.data_df[["lat","lon"]].iloc[-1],color="green",group_name=obj.name,popup=[finishPop])

    save_dir = "Maps/"
    fol.save_map(os.path.join(save_dir, save_name),False)

def load_folder_data(folder, use_cache=True):
    def save_to_cache(source_folder, cache_data):
        # Save data to cache using a name that reflects the source folder
        # this allows easy switching between data sets
        if not os.path.exists('cache'):
            os.mkdir('cache')

        # Decompose path to gpx files into a list
        source_path_components = os.path.normpath(source_folder).split(os.sep)
        # Remove empty elements, and specific files
        source_path_components = [x.strip(":") for x in source_path_components if x != "" and "." not in x]
        cache_name = "cache\\cache__" + "-".join(source_path_components) + ".dat"

        # Dump to cache
        pickle.dump(cache_data, open(cache_name, "wb"))

    def get_cache(source_folder):
        source_path_components = os.path.normpath(source_folder).split(os.sep)
        # Remove empty elements, and specific files
        source_path_components = [x.strip(":") for x in source_path_components if x != "" and "." not in x]
        cache_name = "cache\\cache__" + "-".join(source_path_components) + ".dat"

        avail_caches = glob.glob('cache\\*.dat')

        if cache_name in avail_caches:
            cache = open(cache_name, "rb")
            data = pickle.load(cache)
            return data

        else:
            return None

    files_to_draw = []
    filenames = [g for g in os.listdir(folder) if g.endswith(".gpx")]
    files_to_draw += [os.path.join(folder, file) for file in filenames]

    file_obj_lst = None
    if use_cache:
        file_obj_lst = get_cache(folder)

    if file_obj_lst is None:
        file_obj_lst = []
        for file in files_to_draw:
            g = GPX(file)
            print(file)
            g.analyse()
            file_obj_lst.append(g)

        save_to_cache(folder, file_obj_lst)

    # update cache if new files present
    if len(file_obj_lst) < len(filenames):
        activities_cached = []
        for obj in file_obj_lst:
            activities_cached.append(obj.filename)
        for act in files_to_draw:
            if act not in activities_cached:
                g = GPX(act)
                g.analyse()
                file_obj_lst.append(g)

        # save_to_cache(folder, file_obj_lst)

    return file_obj_lst

if __name__ == '__main__':

    data_source = "Route/"
    gpx_obj_lst = load_folder_data(data_source, use_cache=True)

    draw_on_map_folium(gpx_obj_lst, save_name="RDGA")

    print("Done")


