# // -> Achtung! pip install -r requirements.txt on terminal first!

# // UTILS CLASS
class FUNCTION_UTILS:
    def importLibs(state=None):
        if state:
            # // GeoSpatial Libs
            global rasterio, gpd; 
            # // API Utils Libs
            global retry, openmeteo_requests, requests_cache, req; 
            # // Main Datscie Libs
            global pds, npy; 
             # // Utils Libs
            global kind_os, json, time, datetime, relativedelta;

            import rasterio;
            import geopandas as gpd;
            from retry_requests import retry;
            import openmeteo_requests;
            import requests_cache;
            import requests as req;
            import pandas as pds;
            import numpy as npy;
            import os as kind_os;
            import json;
            import time;
            from datetime import datetime
            from dateutil.relativedelta import relativedelta


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
        with rasterio.open(self.tiff_path) as dataset:
            mask = dataset.dataset_mask();
            # Extract feature shapes and values from the array.
            for geom, val in rasterio.features.shapes(mask, transform=dataset.transform):
                # Transform shapes from the dataset's own coordinate
                # reference system to CRS84 (EPSG:4326).
                geom = rasterio.warp.transform_geom(dataset.crs, 'EPSG:4326', geom, precision=6);
                # Print GeoJSON shapes to stdout.
                print(geom);
                return geom['coordinates'];

# // API CLASS
class API_OPEN_METEO:
    def __init__(self):
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600);
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2);
        self.openmeteo = openmeteo_requests.Client(session=retry_session);

        self.url = "https://api.open-meteo.com/v1/forecast";
        self.OUTPUT_DIR = FUNCTION_UTILS.get_file('02_cuaca_iklim', folder=True);

    def min_one_day(date):
        date = datetime.strptime(date, "%Y-%m-%d");
        prev_day = date - relativedelta(days=1);
        return prev_day.strftime("%Y-%m-%d");

    def get_params(self, lat, lon, start_date):
        return {
            "latitude": lat,
            "longitude": lon,
            "start_date": self.min_one_day(start_date),
            "end_date": start_date,
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "wind_speed_10m", "weather_code", "soil_temperature_0_to_7cm", "soil_temperature_7_to_28cm", "soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm", "pressure_msl", "apparent_temperature"],
        };

    def get_data(self, cords):
        lat = cords[0];
        lon = cords[1];
        params = self.get_params(lat, lon);
        responses = self.openmeteo.weather_api(self.url, params=params);

        response = responses[0];
        # lt = f"{abs(response.Latitude())}°{'S' if response.Latitude() < 0 else 'N'}";
        # lg = f"{abs(response.Longitude())}°{'W' if response.Longitude() < 0 else 'E'}";
        # elev = response.Elevation();
        # tmz = response.UtcOffsetSeconds();

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
        self.url = "https://api.inaturalist.org/v1/observations";
        self.OUTPUT_DIR = FUNCTION_UTILS.get_file('01_inaturalist', folder=True);

    def get_params(self, taxon, index):
        return {
            "taxon_name": taxon,
            "geo": True,
            "quality_grade": "research",
            "per_page": 1,
            "page": index
        };

    def get_data_perspesies(self, key, val):
        all_observations = [];
        cords_none = 0;
        for i in range(1, val+1):
            params = self.get_params(taxon=key, index=i);
            respons = req.get(self.url, params=params);
            data = respons.json();

            # // debug
            print(f"[ON] Request ke-{i} untuk spesies {key} dari total {val} obs");
            persen = (i * 100) / val;
            print(f"[ON] Proses untuk spesies ini baru: {persen:.2f}% atau {i}/{val}\n");

            for obs in data["results"]:
                geojson = obs.get("geojson");
                coords = geojson.get("coordinates") if geojson else None;

                if not coords:
                    cords_none += 1;
                    continue;
                
                observation = {
                    "observation_id": obs["id"],
                    "taxon_id": obs["taxon"]["id"],
                    "species": obs["taxon"]["name"],
                    "latitude": coords[1],
                    "longitude": coords[0],
                    "observed_on": obs["observed_on"], # / ini g detail
                    "time_observed_at": obs["time_observed_at"],
                    "quality_grade": obs["quality_grade"],
                    "positional_accuracy": obs["positional_accuracy"],
                    "obscured": obs["obscured"]
                };
                all_observations.append(observation);
            time.sleep(1.5);
        
        # // debug
        if val == len(all_observations):
            print(f"[SUCCESS] Banyak data obs tuk spesies {key}: {len(all_observations)}");
        else:
            print(f"[WARNING] Banyak data obs tuk spesies {key}: {len(all_observations)}");
            print(f"[WARNING] Ada data obs coord yg None: {cords_none} data");
        print('Request harus dijeda 0.9 detik dulu...\n');

        df = pds.DataFrame(all_observations);
        self.save_to_csv(df, key);

    def save_to_csv(self, df, spesies):
        sp_list = spesies.split();
        spesies_ = "_".join(word for word in sp_list);
        filename = kind_os.path.join(self.OUTPUT_DIR, spesies_+'.csv');
        df.to_csv(filename, index=False);

    def get_data(self):
        for key, val in spesies_json.items():
            self.get_data_perspesies(key, val);
            time.sleep(0.9);

# // MAIN CLASS
class PATH_FILE:
    def init_file(state=None):
        if state:
            global HUTAN_LINDUNG_00_SHP, HUTAN_LINDUNG_01_SHP, HUTAN_LINDUNG_02_SHP;
            global PONGO_ABELII_SHP, PONGO_PYGMAEUS_SHP, MACACA_NIGRA_SHP, MACROCEPHALON_MALEO_SHP, MANOURIA_EMYS_SHP;
            global LANDCOVER2025_TIFF;
            global LANDCOVER2025_JSON, MAKANAN_JSON, SPESIES_CR_JSON;
            global HUTAN_LINDUNG_00_XLSX, HUTAN_LINDUNG_01_XLSX, HUTAN_LINDUNG_02_XLSX

            # // CSV and XLSX File
            HUTAN_LINDUNG_00_XLSX = FUNCTION_UTILS.get_file('hutan_lindung_00.xlsx');
            HUTAN_LINDUNG_01_XLSX = FUNCTION_UTILS.get_file('hutan_lindung_01.xlsx');
            HUTAN_LINDUNG_02_XLSX = FUNCTION_UTILS.get_file('hutan_lindung_02.xlsx');
            
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

            # // JSON File
            LANDCOVER2025_JSON = FUNCTION_UTILS.get_file('label_landcover.json'); 
            MAKANAN_JSON = FUNCTION_UTILS.get_file('makanan.json'); 
            SPESIES_CR_JSON = FUNCTION_UTILS.get_file('spesies_cr.json'); 
                
     
# // MAIN CLASS
class MAIN:
    def __init__(self, state=None):
        if state:
            self.run_main();

    def process_geopatial(self):
        # TIFF = GEOTIFF(raster_path=LANDCOVER2025_TIFF);
        # cords = TIFF.get_cords();
        # METEO = API_OPEN_METEO();
        # METEO.get_data(cords);
        pass

    def process_api_inaturalist(self):
        INATURALIST = API_INATURALIST();
        INATURALIST.get_data();

    def process_json(self):
        global lc25_json, makanan_json, spesies_json;

        lc25_json = None;
        with open(LANDCOVER2025_JSON, mode='r', encoding='utf-8') as lc25:
            lc25_json =  json.load(lc25);
        
        makanan_json = None;
        with open(MAKANAN_JSON, mode='r', encoding='utf-8') as mkn:
            makanan_json =  json.load(mkn);
    
        spesies_json = None;
        with open(SPESIES_CR_JSON, mode='r', encoding='utf-8') as scr:
            spesies_json =  json.load(scr);
    
    def process_csv_xlsx(self):
        pass

    def run_main(self):
        FUNCTION_UTILS.importLibs(state=True);
        PATH_FILE.init_file(state=True);

        self.process_json();
        self.process_geopatial();
        self.process_csv_xlsx();
        self.process_api_inaturalist();

# // run this main class
RUN_MAIN = MAIN(state=True);
