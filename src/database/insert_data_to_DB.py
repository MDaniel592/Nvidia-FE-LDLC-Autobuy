import database.db_manager as db_manager

ldlc_data = {
    "RTX 3070": {
        "url": "https://www.ldlc.com/es-es/ficha/PB78945689.html",
        "max_price": 600,
    },
    "RTX 3080": {
        "url": "https://www.ldlc.com/es-es/ficha/PB60154868.html",
        "max_price": 800,
    },
}

for data in ldlc_data:
    db_manager.update_insert(name=data, url=ldlc_data[data]["url"], max_price=ldlc_data[data]["max_price"])
