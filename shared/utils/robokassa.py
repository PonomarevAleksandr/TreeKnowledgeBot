"""Robokassa create invoice functions"""
import decimal
import json
import re
from dataclasses import dataclass
import hashlib
from urllib import parse


async def calculate_signature(*args) -> str:
    """
    Calculate signature
    :param args:
    :return: str
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


@dataclass
class RobokassaConfig:
    """
    Config for Robokassa
    """
    merchant_login: str
    merchant_password_1: str
    robokassa_payment_url: str = 'https://auth.robokassa.ru/Merchant/Index.aspx'
    is_test: int = 0


@dataclass
class PaymentData:
    """
    Args for PaymentData
    """
    config: RobokassaConfig
    cost: decimal.Decimal
    number: int
    description: str
    user_id: int
    period: int


def decimal_to_float(obj):
    """
    Converts Decimal objects to float for JSON serialization.
    """
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


async def generate_payment_link(payment_data: PaymentData) -> str:
    """
    Generate payment link

    :param payment_data: Экземпляр PaymentData с параметрами платежа.
    :return: URL платёжной ссылки.
    """
    config = payment_data.config
    clean_description = re.sub(r'[^\w\s.,!?:;\'"()-]', '', payment_data.description.strip())
    items = [
        {
            "name": clean_description,
            "quantity": 1,
            "sum": f"{float(payment_data.cost):.2f}",
            "payment_method": "full_payment",
            "payment_object": "service",
            "tax": "none"
        }
    ]
    receipt = {
        "sno": "osn",
        "items": items
    }
    receipt_json = json.dumps(receipt, ensure_ascii=False)
    receipt_encoded_for_signature = parse.quote(receipt_json.encode('utf-8'), safe='')
    signature_parts = [
        config.merchant_login,
        f"{float(payment_data.cost):.2f}",
        str(payment_data.number),
        receipt_encoded_for_signature,
        config.merchant_password_1
    ]
    signature = await calculate_signature(*signature_parts)
    data = {
        'MerchantLogin': config.merchant_login,
        'OutSum': f"{float(payment_data.cost):.2f}",
        'InvId': payment_data.number,
        'Description': clean_description,
        'SignatureValue': signature,
        'IsTest': config.is_test,
        'Receipt': receipt_encoded_for_signature
    }
    query_string = parse.urlencode(data, quote_via=parse.quote)
    payment_link = f"{config.robokassa_payment_url}?{query_string}"
    return payment_link
