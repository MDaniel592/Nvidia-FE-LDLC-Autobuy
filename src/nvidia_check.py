import asyncio
import datetime
import logging
import time

import aiohttp
import ujson

# InfluxDB
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

import src.database.db_manager as db_manager
from src.utils.shared_variables import (
    BASE_LDLC_URL,
    BUCKET,
    INFLUXDB_URL,
    NVIDIA_API_URLS,
    NVIDIA_GPU_MODEL_ID,
    NVIDIA_HEADER,
    NVIDIA_WANTED_PRODUCTS,
    ORG,
    TOKEN,
)

client = InfluxDBClient(url=INFLUXDB_URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def process_nvidia_data(product_data):
    productLink = product_data["product_url"]
    productName = product_data["fe_sku"]
    productRegion = product_data["locale"]

    if NVIDIA_WANTED_PRODUCTS.get(productName, False):
        try:
            product_id = NVIDIA_GPU_MODEL_ID[productName]
        except:
            logger.warning(f"API - {productRegion} - {productName} - Producto no identificado")
            return

        db_product = db_manager.perform_select(
            search_params={"id": product_id},
            select_params={"url", "stock", "time_stock"},
            distinct=True,
            as_dict=True,
        )[0]

        productLink = BASE_LDLC_URL + productLink[productLink.index("/PB") :]

        current_time = datetime.datetime.now().replace(microsecond=0)
        if product_data["is_active"] == "true" and len(productLink) > 22 and productLink != db_product["url"]:
            logger.warning(f"API - {productRegion} - {productName} - Tiene stock - URL: {productLink}")
            db_manager.perform_update(
                search_params={"id": product_id},
                params_to_update={"url": productLink, "stock": 1, "time_stock": current_time},
            )
        else:
            if db_product["stock"] == 1 and current_time > db_product["time_stock"] + datetime.timedelta(minutes=1):
                logger.warning(f"API - {productRegion} - {productName} - Sin stock - URL: {productLink}")
                db_manager.perform_update(search_params={"id": product_id}, params_to_update={"stock": 0})
            else:
                logger.warning(f"API - {productRegion} - {productName} - Sin Stock - No se guarda en DB")


async def check_nvidia_stock(url):
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout, headers=NVIDIA_HEADER) as session:
            async with session.get(url) as response:
                logger.warning(f"Status code: {response.status} - Region: {url[57:59]}")
                response = await response.text()

        try:
            json_response = ujson.loads(response)
        except:
            logger.error("Error JSON")
            logger.error(response)
            return

        products_data = json_response["listMap"]
        await asyncio.gather(*[process_nvidia_data(product_data) for product_data in products_data])

    except asyncio.exceptions.TimeoutError:
        logger.error("Timeout - ending the task")


async def main():
    start = time.time()
    logger.warning("The Nvidia Check Stock will start")

    await asyncio.gather(*[check_nvidia_stock(url) for url in NVIDIA_API_URLS])

    time.sleep(1)

    end = time.time()
    elapse_time = int(end) - int(start)
    logger.warning("The Nvidia Check Stock has finished, tiempo: %s segundos", elapse_time)

    actual_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    write_api.write(
        bucket=BUCKET,
        record=[
            {
                "measurement": "Autobuy",
                "tags": {"service": "Nvidia Check Stock"},
                "fields": {"Running time": elapse_time},
                "time": actual_time,
            }
        ],
    )


asyncio.run(main())
