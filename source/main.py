class FUNCTION_UTILS:
    def importLibs(state=None):
        if state:
            global rasterio, npy, kind_os, requests_cache, retry, openmeteo_requests, pds;
            import rasterio;
            import numpy as npy;
            import os as kind_os;
            import pandas as pds;
            import requests_cache;
            from retry_requests import retry;
            import openmeteo_requests;

    def get_file(target_file):
        BASE_DIR = kind_os.getcwd();
        for curr_folder, list_folders, list_files in kind_os.walk(BASE_DIR):
            if target_file in list_files:
                return kind_os.path.join(curr_folder, target_file);
        return None;

class GEOTIFF:
    def __init__(self, raster_path):
        self.tiff_path = raster_path;

    def get_cords(self):
        with rasterio.open(self.tiff_path) as src:
            band = src.read(1)
            rows, cols = npy.where(band == 35)
            r, c = rows[0], cols[0]
            lon, lat = rasterio.transform.xy(src.transform, r, c, offset='center')
            
            print(f"1 Titik Sawit -> Latitude: {lat}, Longitude: {lon}, Value: {band[r, c]}")
            return (lat, lon)

class API_OPEN_METEO:
    def __init__(self):
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        self.openmeteo = openmeteo_requests.Client(session = retry_session)

        self.url = "https://api.open-meteo.com/v1/forecast"

    def get_params(self, lat, lon):
        return {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m",
        };

    def get_data(self, cords):
        lat = cords[0];
        lon = cords[1];
        params = self.get_params(lat, lon);
        responses = self.openmeteo.weather_api(self.url, params = params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        print(f"Coordinates: {abs(response.Latitude())}°{'S' if response.Latitude() < 0 else 'N'} {abs(response.Longitude())}°{'W' if response.Longitude() < 0 else 'E'}")
        print(f"Elevation: {response.Elevation()} m asl")
        print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

        hourly_data = {
            "date": pds.date_range(
                start = pds.to_datetime(hourly.Time(), unit = "s", utc = True),
                end =  pds.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
                freq = pds.Timedelta(seconds = hourly.Interval()),
                inclusive = "left"
            )
        }

        hourly_data["temperature_2m"] = hourly_temperature_2m

        hourly_dataframe = pds.DataFrame(data = hourly_data)
        print("\nHourly data\n", hourly_dataframe)

class MAIN:
    def __init__(self, state=None):
        if state:
            self.run_main();

    def run_main(self):
        FUNCTION_UTILS.importLibs(state=True);

        raster_path = FUNCTION_UTILS.get_file('LANDCOVER_2025_ADA_SAWIT.tif');
        TIFF = GEOTIFF(raster_path=raster_path);
        cords = TIFF.get_cords();

        METEO = API_OPEN_METEO();
        METEO.get_data(cords);
  
# // run this main class
RUN_MAIN = MAIN(state=True);
