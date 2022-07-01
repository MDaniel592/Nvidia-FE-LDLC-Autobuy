import logging
import sqlite3 as db

from src.utils.shared_variables import DB_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.propagate = False


def sql_connection():
    try:
        con = db.connect(DB_NAME, check_same_thread=False)
        logger.info("Connection established")
        return con
    except db.Error as e:
        logger.warning(e)
        return None


##########
# Update functions
##########
def perform_update(search_params, params_to_update, operator="AND"):
    connection = sql_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    search_params_list = list(search_params.keys())
    where_clause = f"{search_params_list[0]} = ?"
    for search_param in search_params_list[1:]:
        where_clause = where_clause + f" {operator} " + f"{search_param} = ?"
    str_params = "=?,".join(params_to_update.keys()) + "=?"
    try:
        cursor.execute(
            f"UPDATE products SET {str_params} WHERE {where_clause}",
            (*params_to_update.values(), *search_params.values()),
        )
        connection.commit()
        logger.info(f"update ejecutado correctamente para url con url: {search_params}")
        cursor.close()
        connection.close()
        return True
    except db.Error as err:
        logger.warning(f"Error en el update de url -> {err}")
        cursor.close()
        connection.close()
        return False


##########
# Insert functions
##########
def update_insert(url, name, max_price):
    connection = sql_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO products(url, name, max_price) VALUES (?,?,?) ON CONFLICT(name) DO UPDATE SET max_price = ?",
            (
                url,
                name,
                max_price,
                max_price,
            ),
        )
        connection.commit()
        logger.info(f"update_insert ejecutado correctamente para la {url}")
        cursor.close()
        connection.close()
        return True
    except db.Error as err:
        logger.warning(f"Error en el update_insert de url -> {err}")
        cursor.close()
        connection.close()
        return False


##########
# Select functions
##########
def perform_select(select_params, search_params, operator="AND", distinct=False, as_dict=False):
    connection = sql_connection()
    data = []
    if connection is None:
        return data
    search_params_list = list(search_params.keys())
    where_clause = f"{search_params_list[0]} = ?"
    for search_param in search_params_list[1:]:
        where_clause = where_clause + f" {operator} " + f"{search_param} = ?"
    select_clause = ",".join(select_params)
    if distinct:
        distinct = "distinct"
    else:
        distinct = ""
    if as_dict:
        connection.row_factory = db.Row
    try:
        with connection:
            cursor = connection.execute(
                f"SELECT {distinct} {select_clause} FROM products WHERE {where_clause}",
                [*search_params.values()],
            ).fetchall()
            if as_dict:
                for row in cursor:
                    data.append(dict(row))
            else:
                data = cursor
        connection.close()
        logger.info(f"perform_select en products ejecutado correctamente.")
        return data
    except db.Error as err:
        logger.warning(f"Error en el perform_select de productos -> {err}")
        connection.close()
        return data


##########
# Remove functions
##########
def remove_product(url):
    connection = sql_connection()
    if connection is None:
        return False

    connection.execute("PRAGMA foreign_keys = 1")

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE url = ?", (url,))
        connection.commit()
        logger.info(f"remove_all_products ejecutado correctamente con url -> {url}")
        cursor.close()
        connection.close()
        return True
    except db.Error as err:
        logger.warning(f"Error en remove_all_products -> {err}")
        cursor.close()
        connection.close()
        return False


##########
# Custom functions
##########
def get_all_products():
    connection = sql_connection()
    if connection is None:
        return False

    connection.execute("PRAGMA foreign_keys = 1")

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM products")
        connection.commit()
        logger.info(f"get_all_products ejecutado correctamente")
        cursor.close()
        connection.close()
        return True
    except db.Error as err:
        logger.warning(f"Error en get_all_products -> {err}")
        cursor.close()
        connection.close()
        return False
