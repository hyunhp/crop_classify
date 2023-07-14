import dotenv
import os
import numpy as np
import json
from tqdm import tqdm
import argparse
import pprint
import requests

# UPLOAD GOOGLE STREE VIEW API KEY IN ENV FILE
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)
key = "&key=" + os.environ['key']

# Test code
# python3 download_gsv.py --start_lat 33 --end_lat 33.1 --step_lat 0.1 --start_lng 122 --end_lng 122.1 --step_lng 0.05

# Function
def define_argparser():
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description = 'Download the Google Street View Images by latitude and longtitude')

    # Argument about Latitude
    parser.add_argument(
        '--start_lat', type = float,   required=True,
        help = "Start point of latitude (Included)"
    )    
    parser.add_argument(
        '--end_lat',   type = float,   required=True,
        help = "End point of latitude (Included)"
    )        
    parser.add_argument(
        '--step_lat',  type = float,   required=False, 
        # e.g., 0.001  
        # At the equator (latitude 0 degrees): 0.556 kilometers
        # At a higher latitude (e.g., latitude 30 degrees): 0.482 kilometers
        # At the poles (latitude 90 degrees): 0 kilometers
        default= 0.001,
        help = "How many steps to move from start point to end point of latitude (Default 0.001)"
    )    

    # Argument about Longitude
    parser.add_argument(
        '--start_lng', type = float,  required=True,
        help = "Start point of longitude (Included)"
    )    
    parser.add_argument(
        '--end_lng',  type = float,   required=True,
        help = "End point of longitude (Included)"
    )        
    parser.add_argument(
        '--step_lng', type = float,   required=False, 
        # 0.001 -> Distance almost 0.111 km
        # 0.01  -> Distance almost 1.111 km
        default= 0.005,
        help = "How many steps to move from start point to end point of longitude (Default 0.005)"
    )    

    parser.add_argument(
        '--download_path',  type = str,     required=False, 
        default= './download/',
        help="Output images saved location (default: ./download/)"
    )

    config = parser.parse_args()
    return config

def get_metatdata_view_image(response : json):
    pano_id = response['pano_id']           # Unique id number of image
    date    = response['date']              # e.g., 2023-04
    lat     = response['location']['lat']   # latitude of image
    lng     = response['location']['lng']   # longitude of image

    return pano_id, date, lat, lng

# Download images from Google street view
# image_response : output of requests.get(image_save_url)
# download name : YYYY-MM_latitude_longitude.jpg
def download_gsv_image(image_response, download_path, date, lat, lng):
    with open(os.path.join(download_path, f"{str(date)}_{str(lat)[:10]}_{str(lng)[:10]}.jpg"), 'wb') as f:
        f.write(image_response.content)
        print(f'saved, {str(lat)[:10]}, {str(lng)[:10]}')

def main(config):
    def print_config(config):
        pp = pprint.PrettyPrinter()
        pp.pprint(vars(config))

    print_config(config)

    start_lat = config.start_lat
    end_lat = config.end_lat
    step_lat = config.step_lat

    start_lng = config.start_lng
    end_lng = config.end_lng
    step_lng = config.step_lng

    download_path = config.download_path

    if not os.path.exists(download_path):
        os.mkdir(download_path)

    size = "&size=" + "2040x2040"
    fov = "&fov=" + str(35)
    heading = "&heading=" + str(90)

    # Start downloading google street view
    for lat in tqdm(np.arange(start_lat, end_lat, step_lat)):   # the range for Latitude
        for lng in (np.arange(start_lng, end_lng, step_lng)):   # the range for Longitude
            location = f'{lat},{lng}'
            meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={location}{key}"
            meta_requests = requests.get(meta_url)

            # To detect whether response is right
            if meta_requests.status_code != 200:
                print(f'Request {location} failed with status code:', meta_requests.status_code)
                continue
            
            meta_response = meta_requests.json()

            if meta_response["status"] == "OK":
                
                # Get metatdata from google street view image
                pano_id, date, lat, lng = get_metatdata_view_image(response=meta_response)
                pano = "&pano=" + pano_id
                
                # date[:4] is year (YYYY)
                # Too old image, hard to check this data is appropriate
                if int(date[:4]) < 2007:
                    continue
                
                base_save_url = f"https://maps.googleapis.com/maps/api/streetview?{size}{fov}{heading}"
                image_save_url = base_save_url + pano + key

                # save the image data 
                image_response = requests.get(image_save_url)
                # file name : YYYY-MM_latitude_longitude.jpg
                download_gsv_image(image_response, download_path, date, lat, lng) 
            
            else : 
                print(f'NA, {str(lat)[:10]}, {str(lng)[:10]}')

if __name__ == '__main__' :
    config = define_argparser()
    main(config)
