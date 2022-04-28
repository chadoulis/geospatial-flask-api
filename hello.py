from flask import Flask, request
from flask_cors import CORS
import json
from markupsafe import escape
import rasterio
import numpy as np
from rasterio.windows import Window
from PIL import Image
import io
import base64

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/lets-park/<municipality>/<product>")
def me_api(municipality, product):
    with open('data.json', "r") as f:
        data = json.loads(f.read()) 
    return data[escape(municipality)][product]


@app.route("/webgis")
def webgis():

    '''
    Query Example:
    http://localhost:5000/webgis?elevation_limit_down=200&elevation_limit_up=300
    ?min_latitude=?max_latitude=?min_longitude=?max_longitude=?
    '''
    min_latitude = request.args.get('min_latitude', type=float)
    max_latitude = request.args.get('max_latitude', type=float)
    min_longitude = request.args.get('min_longitude', type=float)
    max_longitude = request.args.get('max_longitude', type=float)
    bounding_box = [min_latitude, max_latitude,max_longitude,min_longitude]
    elevation_limit_down = request.args.get('elevation_limit_down', type=int)
    elevation_limit_up = request.args.get('elevation_limit_up',type=int)
    elevation_limits = [elevation_limit_down,elevation_limit_up]
    
    clc_dir = 'blanca10.tif'
    elevation_dir = 'dem10.tif'
    
	#Loading slope layer
    clc_src = rasterio.open(clc_dir)
    clc_array = np.squeeze(np.array(clc_src.read()))
    elevation_src = rasterio.open(elevation_dir)
    elevation_array = np.squeeze(np.array(elevation_src.read()))
    
    a, b = elevation_array.shape
    with rasterio.open(elevation_dir) as dataset:
        transform = dataset.transform
        
    bbox = rasterio.transform.array_bounds(a, b, transform)
    #lon_range = abs(bbox[0]-bbox[2])
    #lat_range = abs(bbox[1]-bbox[3])
    #lon_pixel_len = lon_range/b
    #lat_pixel_len = lat_range/a

    #lon_offset = abs(min_longitude-bbox[0])//lon_pixel_len
    #lat_offset = abs(min_latitude-bbox[1])//lat_pixel_len
    #lon_offset_2 = abs(max_longitude-bbox[0])//lon_pixel_len
    #lat_offset_2 = abs(max_latitude-bbox[1])//lat_pixel_len
    #width = abs(lon_offset_2 - lon_offset)
    #height = abs(lat_offset_2 - lat_offset)
        
    with rasterio.open(elevation_dir) as src:
        w = src.read(1)
        ww = np.array(w)
        f = np.multiply(np.multiply((ww>elevation_limits[0]),(ww<elevation_limits[1])),ww)

    ri = f
    ri[np.nonzero(ri)] = 255
    ri[ri==0]=-1
    ri[ri==255]=0
    ri[ri==-1]=255
    ff = ri.astype('uint8')
    img = Image.fromarray(ff, 'L')
    ri2 = f
    ri2[np.nonzero(ri2)]=255
    ri2[ri2==0]=-1
    ri2[ri2==255]=0
    ri2[ri2==-1]=255
    ri3=ri2.astype('uint8')
    img2=Image.fromarray(ri3,"L")
    img.putalpha(img2)
    data = io.BytesIO()
    img.save(data, format='PNG')  
    
    #  Initialize the Image Size
    image_size = ff.shape

	#  Choose some Geographic Transform (Around Lake Tahoe)
    lat = [max_latitude,min_latitude]
    lon = [max_longitude,min_longitude]



    response_data = {}
    response_data['imageUrl'] = 'data:image/png;base64,'+base64.b64encode(data.getvalue()).decode('ascii')   
    response_data['imageBounds2'] = [[37.8541324176775120,-1.8487617382948298],[38.8237388514157473,-0.6113975670374805]]
    response_data['imageBounds'] = [[bbox[1],bbox[0]], [bbox[3], bbox[2]]]
    
    return response_data


if __name__ == '__main__':
    app.run(host="164.92.156.108", port=8000, debug=True)
