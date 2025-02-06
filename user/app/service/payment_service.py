from decimal import Decimal
from beanie import PydanticObjectId
from pydantic import EmailStr
import requests

from user.app.schemas.user_schema import PaymentGatewayEnum


class PaymentService:
    def generate_payment_link(
        self,
        order_id: PydanticObjectId,
        amount: Decimal,
        customer_email: EmailStr,
        sk: str,
        payment_gateway: str
    ) -> str:
        fw_base_url = "https://checkout.flutterwave.com/pay"
        fw_headers = {"Authorization": f"Bearer {sk}"}
        fw_data = {
            "tx_ref": str(order_id),
            "amount": str(amount),
            "currency": "NGN",
            "redirect_url": f"{'quick_pickup_base_url'}/payment/callback",
            "customer": {
                "email": customer_email,
            },
        }

        # Paystack expects amount in kobo
        amount_in_kobo = str(Decimal(amount * 100))
        ps_base_url = "https://checkout.flutterwave.com/pay"
        ps_headers = {"Authorization": f"Bearer {sk}"}
        ps_data = {
            "tx_ref": str(order_id),
            "amount": str(amount_in_kobo),
            "currency": "NGN",
            "redirect_url": f"{'quick_pickup_base_url'}/payment/callback",
            "customer": {
                "email": customer_email,
            },
        }

        link = ''

        if payment_gateway == PaymentGatewayEnum.FLUTTERWAVE:

            response = requests.post(
                f"{fw_base_url}/payments", json=fw_data, headers=fw_headers)
            response_data = response.json()
            link = response_data["data"]["link"]

            print(f"XXXXXXXXXXXX Payment link: {link} XXXXXXXXXXXXXXXXXX")

        elif payment_gateway == PaymentGatewayEnum.PAYSTACK:

            response = requests.post(
                ps_base_url, json=ps_data, headers=ps_headers).json()

            print(response)
            print(f"XXXXXXXXXXXX Payment link: {link} XXXXXXXXXXXXXXXXXX")
            return response

        return link

    # def generate_paystack_link(
    #     self,
    #     order_id: PydanticObjectId,
    #     amount: Decimal,
    #     customer_email: str,
    #     sk: str
    # ) -> str:
    #     base_url = "https://api.paystack.co/charge"

    #     headers = {
    #         "Authorization": f"Bearer {sk}",
    #         "Content-Type": "application/json"
    #     }

    #     # Paystack expects amount in kobo
    #     amount_in_kobo = str(Decimal(amount * 100))
    #     data = {
    #         "email": customer_email,
    #         "amount": amount_in_kobo,
    #         "reference": str(order_id),
    #         "currency": "NGN"

    #     }

    #     response = requests.post(base_url, json=data, headers=headers).json()
    #     return response


pay = PaymentService()

# link = pay.generate_paystack_link(
#     1, 2000, 'email@example.com', 'sk_test_b86956dde1fc09a0026a5c5f425c28c04836e428')
