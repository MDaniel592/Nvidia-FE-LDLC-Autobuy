import asyncio
import logging
import time

# Extra
from datetime import datetime
from re import T
from socket import timeout

# InfluxDB
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from playwright._impl._api_types import TimeoutError

# Playwright
from playwright.async_api import async_playwright

import src.database.db_manager as db_manager
from src.utils.ldlc_account_data import CardNumber, Cryptogram, ExpirationDate, OwnerName, password, user
from src.utils.parse_number import parse_number
from src.utils.shared_variables import BUCKET, FOLDER_PATH, INFLUXDB_URL, ORG, TOKEN

client = InfluxDBClient(url=INFLUXDB_URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Headers
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_20_77) AppleWebKit/531.71.18 (KHTML, like Gecko) Chrome/55.1.6997.1625 Safari/532.00 Edge/36.04460"
HEADERS = {
    "User-Agent": f"{USER_AGENT}",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "*/*",
    "Connection": "keep-alive",
}


async def buy_product(browser, product):
    name = product["name"].replace(".", " ")
    max_price = product["max_price"]
    url = product["url"]

    try:
        page = await browser.new_page(extra_http_headers=HEADERS)
        page.set_default_timeout(15000)
        await page.goto(url, wait_until="domcontentloaded")

        # Inicio de sesion
        await page.click("css=#cookieConsentAcceptButton")

        await page.hover("css=span.icon.icon-user")
        await page.fill("css=#Email", user)
        await page.fill("css=#Password", password)
        await page.click("css=form#loginForm>button")
        logger.warning(f"{name} - He conseguido logearme en la cuenta")

        # Comprobar precio
        precio = await page.query_selector("css=div.saleBlock")
        precio = await precio.get_attribute("data-price")
        precio = parse_number(precio)
        if float(precio) > float(max_price):
            logger.warning(f"{name} - Precio superior al límite: {precio}")
            return

        logger.warning(f"{name} - Precio dentro del límite: {precio} - Precio máximo: {max_price}")
        # Comprar directamente o ir a la cesta (ya estaría añadido)
        comprar_ya = await page.query_selector("css=div#product-page-price>div:nth-of-type(2)>button:nth-of-type(2)")
        visible = await comprar_ya.is_visible()
        if visible:
            await comprar_ya.click()
        else:
            logger.warning("%s - Sin botón de COMPRAR YA", name)
            await page.goto("https://secure2.ldlc.com/es-es/Cart", wait_until="load")

            logger.warning("%s - Comprobar que la cesta no esté vacía", name)
            # Comprobar que la cesta no esté vacía
            cesta = await page.query_selector("css=div.empty-cart")
            if cesta:
                logger.warning("%s - La cesta está vacía")
                return

            logger.warning("%s - Comprobar que solo haya una gráfica y product", name)
            # Comprobar que solo haya una gráfica
            cantidad = await page.query_selector("css=div.input")
            cantidad = await cantidad.text_content()
            cantidad = int(cantidad.replace(" ", "").replace("\n", ""))
            # Comprobar que solo hay un product
            element = await page.query_selector("css=div.cart-product-list")
            childrens = await element.query_selector_all("xpath=child::*")

            logger.warning(
                "%s - Comprobar cesta - cantidad: %s - productos: %s",
                name,
                cantidad,
                len(childrens) - 1,
            )
            # Borrar toda la cesta y volver a empezar
            if cantidad != 1 or len(childrens) != 2:
                await page.wait_for_selector("css=span.icon.icon-trash", state="visible")
                element_handle = await page.query_selector("css=span.icon.icon-trash")
                box = await element_handle.bounding_box()
                await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

                await page.wait_for_selector("xpath=(//a[@class='button'])[1]", state="visible")
                element_handle = await page.query_selector("xpath=(//a[@class='button'])[1]")
                box = await element_handle.bounding_box()
                await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

                logger.warning("%s - Se ha borrado la cesta", name)
                return

            # Ir al pago
            await page.click("css=button.button.maxi")

        # Confirmar datos, precio y pago
        logger.warning("%s - Web para confirmar la dirección y realizar el pago", name)
        credit_cart = await page.query_selector("css=#CardNumber")
        if credit_cart:
            visible = await credit_cart.is_visible()
        else:
            visible = False

        logger.warning("%s - Credit card: %s", name, visible)
        await page.wait_for_load_state("networkidle")
        if not visible:
            logger.warning("%s - Confirmando dirección", name)
            # Dirección
            await page.wait_for_selector("css=input[data-delivery-group='classic']", state="visible")
            element_handle = await page.query_selector("css=input[data-delivery-group='classic']")
            box = await element_handle.bounding_box()
            await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await page.wait_for_load_state("networkidle")

        logger.warning("%s - Comprobando el precio", name)
        # Comprobar precio
        await page.wait_for_selector("css=p.total-costs.to-right.price", state="visible")
        precio = await page.query_selector("css=p.total-costs.to-right.price")
        precio = await precio.inner_text()
        precio = parse_number(precio)
        if float(precio) > float(max_price):
            logger.warning("%s - Precio superior al límite: %s", name, precio)
            return

        # Pagar
        logger.warning("%s - Introducir datos de la tarjeta", name)
        # Datos
        await page.fill("css=#CardNumber", CardNumber)
        await page.fill("css=#ExpirationDate", ExpirationDate)
        await page.fill("css=#OwnerName", OwnerName)
        await page.fill("css=#Cryptogram", Cryptogram)

        # Comprobar si se ha comprado el product anteriormente
        # Comprobar si se han comprado 2 graficas
        try:
            producto_buy_status = db_manager.perform_select(search_params={"url": url}, select_params={"buy"}, as_dict=True)[0]
        except:
            producto_buy_status = 0

        logger.warning(f"{name} - Intento de compra - producto_buy_status: {producto_buy_status}")
        # Finalizar compra
        if producto_buy_status == 0:
            logger.warning(f"{name} - Inicio de compra - Precio: {precio} - Link: {url}")
            # Screenshot
            actual_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            await page.screenshot(path=f"{FOLDER_PATH}/screenshots/{actual_time}_{name}_inicio_compra.png", full_page=True)

            await page.wait_for_selector("css=button[type='submit']", state="visible")
            element_handle = await page.query_selector("css=button[type='submit']")

            box = await element_handle.bounding_box()

            await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

            db_manager.perform_update(search_params={"url": url}, params_to_update={"buy": 1})
            logger.warning("%s - Compra realizada - Se ha pagado: %s", name, precio)

            # Caso BBVA - Máximo 7 min. Esperando 5 minutos para confirmar el pago en el móvil
            # Screenshot
            tiempo = 10000
            while tiempo < 300000:
                await page.wait_for_timeout(tiempo)
                await page.screenshot(
                    path=f"{FOLDER_PATH}/screenshots/{actual_time}_{name}_{tiempo/1000}sec.png",
                    full_page=True,
                )
                if tiempo != 10000:
                    tiempo += 60000
                else:
                    tiempo += 50000

            # + 15 segundos de cortesía
            await page.wait_for_timeout(15000)

            return

    except TimeoutError:
        actual_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        await page.screenshot(
            path=f"{FOLDER_PATH}/screenshots/{actual_time}_{product['name']}_ldlc_timeout.png",
            full_page=True,
        )
        logger.error("%s - LDLC TimeoutError", product)


async def main():
    start = time.time()
    logger.warning("The LDLC Autobuy will start")

    products = db_manager.perform_select(search_params={"stock": 1, "buy": 0, "active": 1}, select_params={"name", "url", "max_price"}, as_dict=True)

    if products:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await asyncio.gather(*[buy_product(browser, product) for product in products])
            await browser.close()

    end = time.time()
    elapse_time = int(end) - int(start)
    logger.warning(f"The LDLC Autobuy has finished, tiempo: {elapse_time} segundos")

    actual_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    write_api.write(
        bucket=BUCKET,
        record=[
            {
                "measurement": "Autobuy",
                "tags": {"service": "LDLC Autobuy"},
                "fields": {"Running time": elapse_time},
                "time": actual_time,
            }
        ],
    )


asyncio.run(main())
