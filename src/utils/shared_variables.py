# Complete with your parameters

## Not needed if you do not want to log data (Remove all influxdb code)
TOKEN = "TOKEN"
BUCKET = "BUCKET_NAME"
ORG = "ORG_NAME"
INFLUXDB_URL = "http://127.0.0.1:8086/"

## DB DATA - Configure with your folder location etc...
FOLDER_PATH = "src/database"
DB_NAME = "/server_db.db"


## NVIDIA VARIABLES
NVIDIA_HEADER = {
    "Host": "api.store.nvidia.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "Cache-Control": "max-age=0",
    "TE": "trailers",
}


NVIDIA_API_URLS = [
    "https://api.store.nvidia.com/partner/v1/feinventory?skus=ES&locale=ES",
    "https://api.store.nvidia.com/partner/v1/feinventory?skus=FR&locale=FR",
    "https://api.store.nvidia.com/partner/v1/feinventory?skus=IT&locale=IT",
]

## Better options is perform a request to the DB (not manually adding each product here)
## At the actual state, you have to manually add each product...
NVIDIA_GPU_MODEL_ID = {
    "NVGFT070_ES": 1,
    "NVGFT070_FR": 1,
    "NVGFT070_IT": 1,
    "NVGFT080_ES": 2,
    "NVGFT080_FR": 2,
    "NVGFT080_IT": 2,
}

## Better idea! -> Reuse the GPU_MODEL_ID with GPU_MODEL_ID.get(productName, False)
NVIDIA_WANTED_PRODUCTS = {
    "NVGFT070_ES": True,
    "NVGFT070_FR": True,
    "NVGFT070_IT": True,
    #
    "NVGFT080_ES": True,
    "NVGFT080_FR": True,
    "NVGFT080_IT": True,
}


BASE_LDLC_URL = "https://www.ldlc.com/es-es/ficha"
