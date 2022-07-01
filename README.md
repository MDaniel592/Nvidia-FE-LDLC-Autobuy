# Autobuy scripts for NVIDIA FOUNDER GPU (Obsolete)

This project was a done for testing purpose to check how fast a GPU could be bought (I believe the maximum delay was like 6-7 seg) 

- The project is obsolete because the api url used do not longer exits. However, there are new api urls so easily re-usable
- There is a mix of naming convention (sorry!)
- I made a few changes which I did not tested, so be cautious
- The code can be easily improved

Requeriments file is available

## How to run

The project was designed to run on Linux. Tweaks may be required for executing on Windows

- Run the db_manager.sql to create the empty DB. 
    - If not possible run db_manager.py calling sql_connection() because the server_db.db does not exists

- Add the model desired to the DB with insert_data_to_DB (The url does not matter)
    - A new entry is created, check the ID of each product on the DB and edit the shared_variables 

- Continuously run the main scripts. Use systemd or cron

## MAIN SCRIPTS

- LDLC AUTOBUY: iniciate the buy of the FE GPU once there is stock
- LOGGER: dumps the DB data to INFLUXDB
- NVIDIA CHECK: check the stock of FE GPU using NVIDIA API 


## I no longer update/support this code. Use at your own risk