from decimal import Decimal
from beanie import PydanticObjectId
from bson.decimal128 import Decimal128
from cryptography.fernet import Fernet
from user.app.config import get_settings
from user.app.service.payment_service import PaymentService
from ..models.user_model import User
from ..models.order_model import Order
from ..schemas.order_schema import (
    CreateSplitSchema,
    ItemSchema,
    OrderReturnSchema,
    OrderStatus,
    PaymentProvider,
    PaymentStatus,
    SplitSchema,
)

settings = get_settings()


class OrderService:
    def __init__(self):
        """
        Initialize with the same Fernet key used in user service
        fernet_key should be the base64-encoded key used for encryption
        """
        self.fernet = Fernet(settings.ENCRYPTION_KEY)

    def decode_payment_config(self, encrypted_str: str) -> str:
        """Decode the Fernet-encrypted payment configuration"""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_str.encode())
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(
                f"Failed to decrypt payment configuration: {str(e)}")

    async def get_payment_gateway_provider(self, company_id: PydanticObjectId):
        user: User = await User.find(User.id == company_id).first_or_none()
        return user.payment_gateway

    # Create new order
    async def create_order(
        self,
        room_no: str,
        company_id: PydanticObjectId,
        items: list[ItemSchema],
        current_user: User,
    ) -> OrderReturnSchema:
        pg_provider = await self.get_payment_gateway_provider(
            company_id=items[0].item.company_id
        )

        total_amount = sum(
            [
                Decimal(str(item.quantity))
                * Decimal(
                    str(
                        item.item.price.to_decimal()
                        if isinstance(item.item.price, Decimal128)
                        else item.item.price
                    )
                )
                for item in items
            ]
        )

        try:
            decrypted_sk = self.decode_payment_config(
                pg_provider.payment_gateway_secret
            )

            if not decrypted_sk:
                raise ValueError("Invalid payment configuration")
            new_order: Order = Order(
                company_id=company_id,
                guest_id=current_user.id,
                payment_provider=pg_provider.payment_gateway_provider,
                room_number=room_no,
                order_status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                items=items,
                total_amount=total_amount,
            )

            await new_order.save()

            payment_amount = new_order.total_amount

            payment_url = PaymentService.generate_payment_link(
                order_id=new_order.id,
                amount=payment_amount,
                customer_email=current_user.email,
                sk=decrypted_sk,
                payment_gateway=new_order.payment_provider
            )
            print(payment_url)

            # Update the order with the payment URL

            new_order.payment_url = payment_url
            await new_order.save()
            print("==============================================")
            print(new_order.payment_url)
            print("====XXXXXXXXXXXXXXXXXXXXXXXXX=================")

            return new_order
        except Exception as e:
            print(e)

    # Split Bill
    async def split_bill(order_id: PydanticObjectId, current_user: User, splits: list[CreateSplitSchema]):
        order: Order = await Order.find(Order.id == order_id).first_or_none()
        company_user: User = User.find(
            User.id == order.company_id).first_or_none()

        for item in splits:
            new_split = SplitSchema(
                amount=item.amount,
                company_id=order.company_id,
                guest_id=current_user.id,
                order_id=order.id,
                payment_status=PaymentStatus.PENDING,
                payment_url=PaymentService.generate_payment_link(
                    order.order_id, item.amount,
                    customer_email=current_user.email,
                    payment_gateway=company_user.payment_gateway)
            )

            order.splits.append(new_split)

            await order.save()

            return order.splits
