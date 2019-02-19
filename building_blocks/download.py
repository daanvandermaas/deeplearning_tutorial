from sentinelhub import WmsRequest, MimeType, CRS, BBox, CustomUrlParam
import time
import rasterio
import os
from cv2 import imwrite
import numpy as np
#account id for which to download
INSTANCE_ID = "390ee32f-87f7-4536-ac56-5ddce307ff00"





def download(x1, x2, y1, y2,   window,  data_folder, width = 512, height = 512,  satellite_id='L1C'):

    
    box_coords_wgs84 = [x1, y1, x2, y2]
    bbox = BBox(bbox=box_coords_wgs84, crs=CRS.WGS84)

    layer = 'ALL-BANDS-L1C'
    wms_bands_request = WmsRequest(data_folder=data_folder, layer=layer, bbox=bbox,  time=window,
                                   width=width, height=height,
                                   image_format=MimeType.TIFF_d32f,
                                   instance_id=INSTANCE_ID,
                                   custom_url_params={CustomUrlParam.ATMFILTER: 'ATMCOR',
                                                      CustomUrlParam.TRANSPARENT: True,
                                                      CustomUrlParam.SHOWLOGO: False})                
    
    #request and save image    
    wms_img = wms_bands_request.get_data(save_data=True)

    #wait for tiffs to flush    
    time.sleep(5)

    
    if not wms_img: # Image extraction Failed.
        return False
    else:
        return True            # Image succesfully extracted.

    #turn tiffs into jpegs
    files = os.listdir(data_folder)
    for file in files:
        with rasterio.open(file) as im:
            r = im.read(range(2,5))
        r[r>1] = 1
        r[r<0] = 0
        r = np.transpose(r, (1,2,0))
        r = np.sqrt(r)
        r = r * 255
        imwrite(file.replace('.tiff','.jpg'), r)
        os.remove(file)