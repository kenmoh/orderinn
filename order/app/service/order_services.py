from decimal import Decimal
import json
import uuid

import requests
from idna import decode
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet

from ..schema.schemas import (
    CompanyPaymentConfig,
    ItemSchema,
    OrderReturnSchema,
    OrderStatus,
    PaymentProvider,
    PaymentStatus,
    PaymentType,
)
from ..models.models import Order
from ..utils.utils import UserRole
from ..config import get_settings

settings = get_settings()


class PaymentService:
    def generate_flutterwave_link(
        self, order_id: uuid.UUID, amount: Decimal, customer_email: EmailStr, sk: str
    ) -> str:
        # In real implementation, you'd use Flutterwave's SDK or API
        base_url = "https://checkout.flutterwave.com/pay"
        headers = {"Authorization": f"Bearer {sk}"}
        details = {
            "tx_ref": order_id,
            "amount": str(amount),
            "currency": "NGN",
            "redirect_url": f"{'quick_pickup_base_url'}/payment/callback",
            "customer": {
                "email": customer_email,
            },
        }

        response = requests.post(
            f"{base_url}/payments", json=details, headers=headers)
        response_data = response.json()
        link = response_data["data"]["link"]

        print(f"XXXXXXXXXXXX Payment link: {link} XXXXXXXXXXXXXXXXXX")

        return link

    def generate_paystack_link(
        self,
        order_id: uuid.UUID,
        amount: Decimal,
        # config: CompanyPaymentConfig,
        customer_email: str,
    ) -> str:
        # In real implementation, you'd use Paystack's SDK or API
        base_url = "https://checkout.paystack.com/pay"
        amount_in_kobo = int(amount * 100)  # Paystack expects amount in kobo
        return (
            f"{base_url}?"
            f"reference={order_id}&"
            f"amount={amount_in_kobo}&"
            f"email={customer_email}"
        )


class OrderService:
    def __init__(self):
        """
        Initialize with the same Fernet key used in user service
        fernet_key should be the base64-encoded key used for encryption
        """
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
        self.payment_service = PaymentService()

    def decode_payment_config(self, encrypted_str: str) -> str:
        """Decode the Fernet-encrypted payment configuration"""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_str.encode())
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(
                f"Failed to decrypt payment configuration: {str(e)}")

    def calculate_total_amount(self, items: list[ItemSchema]) -> Decimal:
        """Calculate total amount for all items including quantities"""
        total = Decimal("0")
        for item in items:
            total += Decimal(item.price) * item.quantity
        return total

    def generate_payment_link(
        self,
        order_id: str,
        total_amount: Decimal,
        payment_provider: str,
        customer_email: EmailStr,
        sk: str,
    ) -> str:
        """Generate payment link based on company's payment provider"""

        if payment_provider == PaymentProvider.FLUTTERWAVE:
            return self.payment_service.generate_flutterwave_link(
                order_id, total_amount, customer_email, sk
            )
        elif payment_provider == PaymentProvider.PAYSTACK:
            return self.payment_service.generate_paystack_link(
                order_id, total_amount, customer_email, sk
            )
        else:
            raise ValueError(
                f"Unsupported payment provider: {
                    payment_provider}"
            )

    def check_authorization_to_order(self, role: str) -> bool:
        """
        Check if user has required role and permission for a resource
        Returns True if authorized, False otherwise
        """
        return role == UserRole.GUEST

    async def create_order(
        self,
        guest_id: str,
        company_id: str,
        room_number: str,
        sk: str,
        customer_email: EmailStr,
        payment_provider: PaymentProvider,
        payment_type: PaymentType,
        items: list[ItemSchema],
        db: AsyncSession,
    ) -> OrderReturnSchema:
        """Create a new order with payment integration"""
        if not self.check_authorization_to_order(UserRole.GUEST):
            raise PermissionError("You are not authorized to create an order.")

        try:
            # # Calculate total amount
            # total_amount = self.calculate_total_amount(items)

            # # Create order instance
            # order = Order(
            #     guest_id=guest_id,
            #     company_id=company_id,
            #     room_number=room_number,
            #     items=items,
            #     total_amount=total_amount,
            #     payment_status=PaymentStatus.PENDING,
            #     payment_type=payment_type,
            #     order_status=OrderStatus.PENDING,
            # )

            # decoded_sk = self.decode_payment_config(sk)

            # # Generate payment link
            # payment_link = self.generate_payment_link(
            #     order.id, total_amount, sk=decoded_sk, payment_provider=payment_provider, customer_email=customer_email
            # )

            # # Update order with payment link
            # order.paymen_url = payment_link

            # async with db as session:
            #     session.add(order)
            #     await session.commit()
            #     await session.refresh(order)

            # # Create return schema
            # return OrderReturnSchema(
            #     id=str(order.id),
            #     guest_id=guest_id,
            #     company_id=company_id,
            #     room_number=room_number,
            #     payment_status=order.payment_status,
            #     payment_provider=payment_provider,
            #     order_status=order.order_status,
            #     items=items,
            # )
            # Decrypt payment secret key
            decrypted_sk = self.decode_payment_config(sk)
            if not decrypted_sk:
                raise ValueError("Invalid payment configuration")

            # Convert ItemSchema to dict
            items_dict = [item.model_dump() for item in items]

            # Calculate total amount
            total_amount = self.calculate_total_amount(items)

            # Create order record
            new_order = Order(
                guest_id=str(guest_id),
                company_id=str(company_id),
                room_number=room_number,
                total_amount=total_amount,
                payment_provider=payment_provider,
                payment_type=payment_type,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                items=items_dict,
            )

            db.add(new_order)
            await db.flush()

            # Generate payment link
            # payment_link = self.generate_payment_link(
            #     order_id=new_order.id,
            #     total_amount=total_amount,
            #     payment_provider=payment_provider.value,
            #     customer_email=customer_email,
            #     sk=decrypted_sk,
            # )

            print(decrypted_sk, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX')

            new_order.payment_url = 'payment_link'

            await db.commit()
            await db.refresh(new_order)

            return OrderReturnSchema(
                id=new_order.id,
                guest_id=guest_id,
                company_id=company_id,
                room_number=room_number,
                total_amount=str(total_amount),
                payment_provider=payment_provider,
                payment_type=payment_type,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                # payment_link=payment_link,
            )

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to create order: {str(e)}")

    async def create_order2(
        self,
        guest_id: uuid.UUID,
        company_id: uuid.UUID,
        room_number: str,
        items: list[ItemSchema],
        customer_email: str,
        company_payment_config: CompanyPaymentConfig,
        db: AsyncSession,
    ) -> OrderReturnSchema:
        """Create a new order with company-specific payment integration"""
        if not self.check_authorization_to_order(UserRole.GUEST):
            raise PermissionError("You are not authorized to create an order.")

        try:
            # Calculate total amount
            total_amount = self.calculate_total_amount(items)

            # Create order instance with unique ID
            order_id = uuid.uuid4()

            # Generate payment link
            payment_link = self.generate_payment_link(
                order_id, total_amount, company_payment_config, customer_email
            )

            # Update items with payment link
            # for item in items:
            #     item.items.paymen_url = payment_link

            order = Order(
                id=order_id,
                guest_id=guest_id,
                company_id=company_id,
                room_number=room_number,
                items=items,
                total_amount=total_amount,
                payment_status=PaymentStatus.PENDING,
                order_status=OrderStatus.PENDING,
            )

            async with db as session:
                session.add(order)
                await session.commit()
                await session.refresh(order)

            return OrderReturnSchema(
                id=str(order.id),
                guest_id=guest_id,
                company_id=company_id,
                room_number=room_number,
                payment_status=order.payment_status,
                order_status=order.order_status,
                items=items,
            )

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to create order: {str(e)}")
