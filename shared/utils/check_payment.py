"""Worker functions"""
import hashlib
from xml.etree.ElementTree import ParseError
from xml.etree import ElementTree
import asyncio
import aiohttp


async def check_payment_status(merchant_login, invoice_id, password2):
    """
    Function to check payment status asynchronously.
    :param merchant_login: Merchant's login
    :param invoice_id: Invoice ID
    :param password2: Second password for signature
    :return: payment_status: code
    """
    signature_string = f"{merchant_login}:{invoice_id}:{password2}"
    signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()

    url = "https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt"
    params = {
        "MerchantLogin": merchant_login,
        "InvoiceID": invoice_id,
        "Signature": signature
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()

                try:
                    root = ElementTree.fromstring(content)
                    namespace = {'ns': 'http://merchant.roboxchange.com/WebService/'}
                    state_code = root.find('.//ns:State/ns:Code', namespace)
                    if state_code is not None:
                        return int(state_code.text)

                    return None
                except ParseError as e:
                    print(f"XML parsing error: {e}")
                    return None

        except asyncio.TimeoutError:
            print("Request timed out.")
            return None
        except aiohttp.ClientError as e:
            print(f"Request error: {e}")
            return None
