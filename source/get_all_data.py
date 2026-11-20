# // -> Achtung! pip install -r requirements.txt on terminal first!

# // UTILS CLASS
class FUNCTION_UTILS:
    def importLibs(state=None):
        if state:
            global rasterio, gpd; # // GeoSpatial Libs
            global retry, openmeteo_requests, requests_cache; # // API Utils Libs
            global pds, npy; # // Main Datscie Libs
            global kind_os; # // Utils Libs

            import rasterio;
            import geopandas as gpd

            from retry_requests import retry;
            import openmeteo_requests;
            import requests_cache;

            import pandas as pds;
            import numpy as npy;

            import os as kind_os;

    def get_file(target, folder=None):
        BASE_DIR = kind_os.getcwd();
        for curr_folder, list_folders, list_files in kind_os.walk(BASE_DIR):
            if folder:
                if target in list_folders:
                    return kind_os.path.join(curr_folder, target);
                
            if target in list_files:
                return kind_os.path.join(curr_folder, target);
        return None;

# // GEOSPATIAL CLASS
class SHAPEFILE:
    def __init__(self, shape_path):
        self.shp_path = shape_path;

    def get_cords(self):
        pass;

    def get_data(self):
        pass

    def save_data(self):
        pass

    def data_to_csv(self):
        pass

class GEOTIFF:
    def __init__(self, raster_path):
        self.tiff_path = raster_path;

    def get_cords(self):
        with rasterio.open(self.tiff_path) as src:
            band = src.read(1)
            rows, cols = npy.where(band == 35)
            r, c = rows[0], cols[0]
            lon, lat = rasterio.transform.xy(src.transform, r, c, offset='center')
            
            print(f"1 Titik Sawit. Latitude: {lat}, Longitude: {lon}, Value: {band[r, c]}")
            return (lat, lon)

# // API CLASS
class API_OPEN_METEO:
    def __init__(self):
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600);
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2);
        self.openmeteo = openmeteo_requests.Client(session = retry_session);

        self.url = "https://api.open-meteo.com/v1/forecast";
        self.OUTPUT_DIR = FUNCTION_UTILS.get_file('02_cuaca_iklim', folder=True);

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
        responses = self.openmeteo.weather_api(self.url, params=params);

        response = responses[0];
        lt = f"{abs(response.Latitude())}°{'S' if response.Latitude() < 0 else 'N'}";
        lg = f"{abs(response.Longitude())}°{'W' if response.Longitude() < 0 else 'E'}";
        elev = response.Elevation();
        tmz = response.UtcOffsetSeconds();

        print(f"Coordinates: {lt} {lg}");
        print(f"Elevation: {elev} m asl");
        print(f"Timezone difference to GMT+0: {tmz}s")

        hourly = response.Hourly();
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy();

        hourly_data = {
            "date": pds.date_range(
                start = pds.to_datetime(hourly.Time(), unit = "s", utc = True),
                end =  pds.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
                freq = pds.Timedelta(seconds = hourly.Interval()),
                inclusive = "left"
            )
        };

        hourly_data["temperature_2m"] = hourly_temperature_2m;
        hourly_dataframe = pds.DataFrame(data=hourly_data);


        hourly_dataframe.to_csv(kind_os.path.join(self.OUTPUT_DIR, 'testingbrok.csv'), encoding="utf-8-sig", index=False);
        print("\nHourly data\n", hourly_dataframe);

class API_INATURALIST:
    def __init__(self):
        pass

# // MAIN CLASS
class PATH_FILE:
    def init_file(state=None):
        if state:
            global HUTAN_LINDUNG_00_SHP, HUTAN_LINDUNG_01_SHP, HUTAN_LINDUNG_02_SHP;
            global PONGO_ABELII_SHP, PONGO_PYGMAEUS_SHP, MACACA_NIGRA_SHP, MACROCEPHALON_MALEO_SHP, MANOURIA_EMYS_SHP;
            global LANDCOVER2025_TIFF;

            # // CSV File
            # // IDK
            

            # // SHP File
            # // Hutan Lindung
            dir_ht00 = FUNCTION_UTILS.get_file('WDPA_WDOECM_Nov2026_Public_IDN_shp_0', folder=True);
            dir_ht01 = FUNCTION_UTILS.get_file('WDPA_WDOECM_Nov2026_Public_IDN_shp_1', folder=True);
            dir_ht02 = FUNCTION_UTILS.get_file('WDPA_WDOECM_Nov2026_Public_IDN_shp_2', folder=True);
            HUTAN_LINDUNG_00_SHP = kind_os.path.join(dir_ht00, 'WDPA_WDOECM_Nov2026_Public_IDN_shp-points.shp');
            HUTAN_LINDUNG_01_SHP = kind_os.path.join(dir_ht01, 'WDPA_WDOECM_Nov2026_Public_IDN_shp-points.shp');
            HUTAN_LINDUNG_02_SHP = kind_os.path.join(dir_ht02, 'WDPA_WDOECM_Nov2026_Public_IDN_shp-points.shp');

            # // 5 SPESIES CR
            PONGO_ABELII_SHP = FUNCTION_UTILS.get_file('Pongo_abelii.shp');
            PONGO_PYGMAEUS_SHP = FUNCTION_UTILS.get_file('Pongo_pygmaeus.shp');
            MACACA_NIGRA_SHP = FUNCTION_UTILS.get_file('Macaca_nigra.shp');
            MACROCEPHALON_MALEO_SHP = FUNCTION_UTILS.get_file('Macrocephalon_maleo.shp');
            MANOURIA_EMYS_SHP =  FUNCTION_UTILS.get_file('Manouria_emys.shp');

            # // TIF File
            LANDCOVER2025_TIFF = FUNCTION_UTILS.get_file('LANDCOVER_2025_ADA_SAWIT.tif');

     
# // MAIN CLASS
class MAIN:
    def __init__(self, state=None):
        if state:
            self.run_main();

    def process_geopatial(self):
        TIFF = GEOTIFF(raster_path=LANDCOVER2025_TIFF);
        cords = TIFF.get_cords();
        METEO = API_OPEN_METEO();
        METEO.get_data(cords);

    def run_main(self):
        FUNCTION_UTILS.importLibs(state=True);
        PATH_FILE.init_file(state=True);

        self.process_geopatial();

# // run this main class
RUN_MAIN = MAIN(state=True);
