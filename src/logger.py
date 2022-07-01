# influxdb
from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

import src.database.db_manager as db_manager
from src.utils.shared_variables import BUCKET, INFLUXDB_URL, ORG, TOKEN

client = InfluxDBClient(url=INFLUXDB_URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


def main():
    actual_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    ####################
    # Tabla completa
    ####################
    products = db_manager.get_all_products()

    for product in products:
        write_api.write(
            bucket=BUCKET,
            record=[
                {
                    "measurement": "Autobuy",
                    "tags": {"service": product["product_name"]},
                    "fields": {
                        "max_price": product["max_price"],
                        "buy": product["buy"],
                        "stock": product["stock"],
                        "active": product["active"],
                    },
                    "time": actual_time,
                }
            ],
        )

    client.close()


main()
