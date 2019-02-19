import shapely as sh
from geopy.distance import geodesic
from shapely import geometry
import math
import numpy as np
import pandas as pd
import geopandas as gpd


def main( shape, w = 5120 ):
   
    shape = gpd.read_file(shape)
    
    covering = gpd.GeoDataFrame()
    
    for area in shape['geometry'].values: 
        
        #convert to multipolygon in case of a polygon
        if str(type(area)) == "<class 'shapely.geometry.polygon.Polygon'>":
            area = sh.geometry.MultiPolygon([area])
        
        #split the area in a western and eastern halve 
        western = sh.geometry.Polygon([ (-180, -90), (0,-90), (0,90), (-180,90)])
        eastern = sh.geometry.Polygon([ (180, -90), (0,-90), (0,90), (180,90)])
        eastern = sh.geometry.MultiPolygon([poly.difference(western) for poly in area ])
        western = sh.geometry.MultiPolygon([poly.difference(eastern) for poly in area])
    
        #cover the area with tiles
        covering = covering.append(cover( western, w ))
        covering = covering.append(cover( eastern,w))
           
    covering['id'] = np.arange(covering.shape[0])
    
    return(covering)





def cover(area,  w):
    
    if len(area) == 0:
        return(gpd.GeoDataFrame())
    
    x1, y1, x2, y2  = area.bounds
         
    #calculate the y1 and y2 of all squares
    step_y =  w/geodesic((y1,x1), (y1 + 1,x1)).meters
    
    parts_y = math.floor((y2 - y1)/ step_y + 1)
    
    y1_vec = y1 + np.arange(0, parts_y )*step_y
    y2_vec = y1 + np.arange(1, parts_y +1 )*step_y
    
    #make a dataframe of these bounding boxes
    steps_x = [    w/geodesic((y,x1), (y,x1+1)).meters  for y in y1_vec  ]
    parts_x = [math.floor( (x2-x1) /step +1 ) for step in steps_x ]      
    coords = pd.DataFrame()
    for n in np.arange(len(parts_x)):
        x1_sq = [ x1 + j*steps_x[n] for j in np.arange(0,parts_x[n]) ]
        x2_sq = [ x1 + j*steps_x[n] for j in np.arange(1, parts_x[n]+1) ]
        coords_temp = {'x1': x1_sq, 'x2': x2_sq, 'y1': y1_vec[n], 'y2':y2_vec[n]}
        coords = coords.append(pd.DataFrame(coords_temp))
    
    #make a geopandas of this covering dataframe
    cover = [geometry.Polygon([ (coords['x1'].iloc[j] , coords['y1'].iloc[j]) , (coords['x2'].iloc[j] , coords['y1'].iloc[j]), (coords['x2'].iloc[j] , coords['y2'].iloc[j]), (coords['x1'].iloc[j] , coords['y2'].iloc[j]) ]) for j in np.arange(coords.shape[0])]
    
    coords = gpd.GeoDataFrame({'geometry': cover, 'x1':coords['x1'], 'x2':coords['x2'], 'y1':coords['y1'], 'y2':coords['y2'] })

    #remove all tiles that do not intersect the area that needed covering    
    keep = [area.intersects(coords['geometry'].values[j]) for j in np.arange(coords.shape[0])]
    coords = coords[pd.Series(keep, name = 'bools').values]
    coords['id'] = np.arange(coords.shape[0])
        
    return(coords)
