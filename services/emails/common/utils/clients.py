import requests
from typing import Dict, Optional, Tuple, Union

from decimal import Decimal
from emails import settings
from abc import ABC


class APIClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.timeout = 5

        self.product_base_url = f"{settings.PRODUCTS_SERVICE_URL}api/products"
        self.user_base_url = f"{settings.AUTH_SERVICE_URL}api/user"

    def get_product(self, product_id: int) -> Tuple[bool, Optional[Dict]]:
        response = requests.get(
            f"{self.product_base_url}/{product_id}/",
            headers=self.headers,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            print(response)
            return False, None

        return True, response.json()

    def get_user(self, user_id: int) -> Tuple[bool, Optional[Dict]]:
        response = requests.get(
            f"{self.user_base_url}/{user_id}/",
            headers=self.headers,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            print(response)
            return False, None

        return True, response.json()
