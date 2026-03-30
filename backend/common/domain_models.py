#业务逻辑约束（这个大家不用改）
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


class BusinessRuleError(ValueError):
    """Raised when domain rules are violated."""


@dataclass
class User(ABC):
    user_id: str
    name: str
    phone: str
    password: str
    sex: str
    status: str = "active"

    def login(self, phone: str, password: str) -> bool:
        return self.status == "active" and self.phone == phone and self.password == password

    def update_profile(self, name: Optional[str] = None, phone: Optional[str] = None, sex: Optional[str] = None) -> None:
        if name:
            self.name = name
        if phone:
            self.phone = phone
        if sex:
            self.sex = sex

    def logout(self) -> bool:
        return True

    def contact_phone(self, target_phone: str) -> str:
        return target_phone

    def send_message(self, to_user_id: str, content: str) -> "Message":
        return Message(
            message_id=f"m-{int(datetime.now().timestamp())}",
            from_user_id=self.user_id,
            to_user_id=to_user_id,
            content=content,
            send_time=datetime.now(),
            read_status="unread",
        )

    def complain(self, content: str, target_user_id: Optional[str] = None, order_id: Optional[str] = None) -> "Feedback":
        return Feedback(
            feedback_id=f"f-{int(datetime.now().timestamp())}",
            from_user_id=self.user_id,
            target_user_id=target_user_id,
            order_id=order_id,
            feedback_type="complaint",
            content=content,
            status="pending",
            create_time=datetime.now(),
        )

    @classmethod
    @abstractmethod
    def register(cls, **kwargs):
        raise NotImplementedError


@dataclass
class Vehicle:
    vehicle_id: str
    owner_id: str
    brand: str
    color: str
    seats: int
    status: str = "available"

    def update(self, brand: Optional[str] = None, color: Optional[str] = None, seats: Optional[int] = None) -> None:
        if brand:
            self.brand = brand
        if color:
            self.color = color
        if seats is not None:
            self.seats = seats

    def delete(self) -> None:
        self.status = "disabled"


@dataclass
class Order:
    order_id: str
    passenger_id: str
    start_loc: str
    end_loc: str
    depart_time: datetime
    seats_needed: int
    expected_price: Decimal
    owner_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    locked_time: Optional[datetime] = None
    status: str = "CREATED"

    def update(self, start_loc: Optional[str] = None, end_loc: Optional[str] = None, depart_time: Optional[datetime] = None) -> None:
        if self.status not in {"CREATED"}:
            raise BusinessRuleError("Only created orders can be updated.")
        if start_loc:
            self.start_loc = start_loc
        if end_loc:
            self.end_loc = end_loc
        if depart_time:
            self.depart_time = depart_time

    def cancel(self) -> None:
        if self.status in {"COMPLETED", "CANCELED"}:
            raise BusinessRuleError("Order is already finished or canceled.")
        self.status = "CANCELED"

    def lock_by_owner(self, owner_id: str, vehicle_id: str) -> None:
        # Rule: owner accepts order then it is locked immediately.
        if self.status != "CREATED":
            raise BusinessRuleError("Only created orders can be locked.")
        self.owner_id = owner_id
        self.vehicle_id = vehicle_id
        self.locked_time = datetime.now()
        self.status = "LOCKED"

    def mark_completed(self) -> None:
        if self.status not in {"LOCKED", "PAID"}:
            raise BusinessRuleError("Only locked/paid orders can be completed.")
        self.status = "COMPLETED"

    def get_detail(self) -> dict:
        return {
            "orderId": self.order_id,
            "passengerId": self.passenger_id,
            "ownerId": self.owner_id,
            "vehicleId": self.vehicle_id,
            "startLoc": self.start_loc,
            "endLoc": self.end_loc,
            "departTime": self.depart_time.isoformat(),
            "status": self.status,
        }


@dataclass
class Payment:
    payment_id: str
    order_id: str
    payer_id: str
    payee_id: str
    amount: Decimal
    status: str = "UNPAID"
    pay_time: Optional[datetime] = None

    def pay(self) -> None:
        self.status = "PAID"
        self.pay_time = datetime.now()

    def refund(self) -> None:
        if self.status != "PAID":
            raise BusinessRuleError("Only paid records can be refunded.")
        self.status = "REFUNDED"

    def query_status(self) -> str:
        return self.status


@dataclass
class WithdrawRequest:
    withdraw_id: str
    owner_id: str
    amount: Decimal
    status: str = "PENDING"
    create_time: datetime = field(default_factory=datetime.now)
    review_admin_id: Optional[str] = None
    review_time: Optional[datetime] = None

    def submit(self) -> None:
        self.status = "PENDING"

    def cancel(self) -> None:
        if self.status != "PENDING":
            raise BusinessRuleError("Only pending requests can be canceled.")
        self.status = "CANCELED"

    def approve(self, admin_id: str) -> None:
        self.status = "APPROVED"
        self.review_admin_id = admin_id
        self.review_time = datetime.now()

    def reject(self, admin_id: str) -> None:
        self.status = "REJECTED"
        self.review_admin_id = admin_id
        self.review_time = datetime.now()


@dataclass
class Message:
    message_id: str
    from_user_id: str
    to_user_id: str
    content: str
    send_time: datetime
    read_status: str = "unread"

    def send(self) -> None:
        self.send_time = datetime.now()

    def mark_read(self) -> None:
        self.read_status = "read"

    @staticmethod
    def get_history(messages: List["Message"], user_a: str, user_b: str) -> List["Message"]:
        return [
            m
            for m in messages
            if {m.from_user_id, m.to_user_id} == {user_a, user_b}
        ]


@dataclass
class Feedback:
    feedback_id: str
    from_user_id: str
    target_user_id: Optional[str]
    order_id: Optional[str]
    feedback_type: str
    content: str
    status: str
    create_time: datetime
    admin_reply: Optional[str] = None
    reply_time: Optional[datetime] = None

    def submit(self) -> None:
        self.status = "pending"

    def update_status(self, status: str) -> None:
        self.status = status

    def reply(self, reply_text: str) -> None:
        self.admin_reply = reply_text
        self.reply_time = datetime.now()
        self.status = "replied"

    def delete(self) -> None:
        self.status = "deleted"


@dataclass
class Owner(User):
    vehicle_list: List[Vehicle] = field(default_factory=list)
    balance: Decimal = Decimal("0")

    @classmethod
    def register(cls, **kwargs) -> "Owner":
        return cls(**kwargs)

    def publish_vehicle(self, vehicle: Vehicle) -> None:
        if vehicle.owner_id != self.user_id:
            raise BusinessRuleError("Vehicle owner mismatch.")
        self.vehicle_list.append(vehicle)

    def update_vehicle(self, vehicle_id: str, **kwargs) -> None:
        vehicle = next((v for v in self.vehicle_list if v.vehicle_id == vehicle_id), None)
        if not vehicle:
            raise BusinessRuleError("Vehicle not found.")
        vehicle.update(**kwargs)

    def accept_order(self, order: Order, vehicle_id: str) -> None:
        # Rule: owners can only accept, never publish orders.
        vehicle = next((v for v in self.vehicle_list if v.vehicle_id == vehicle_id and v.status == "available"), None)
        if not vehicle:
            raise BusinessRuleError("No available vehicle for this owner.")
        order.lock_by_owner(self.user_id, vehicle_id)

    def view_accepted_orders(self, orders: List[Order]) -> List[Order]:
        return [o for o in orders if o.owner_id == self.user_id]

    def withdraw(self, amount: Decimal) -> WithdrawRequest:
        if amount <= 0 or self.balance < amount:
            raise BusinessRuleError("Insufficient balance.")
        return WithdrawRequest(withdraw_id=f"w-{int(datetime.now().timestamp())}", owner_id=self.user_id, amount=amount)

    def view_wallet(self) -> Decimal:
        return self.balance


@dataclass
class Passenger(User):
    credit_score: int = 100

    @classmethod
    def register(cls, **kwargs) -> "Passenger":
        return cls(**kwargs)

    def search_orders(self, orders: List[Order]) -> List[Order]:
        return [o for o in orders if o.status in {"CREATED", "LOCKED"}]

    def publish_order(self, order_id: str, start_loc: str, end_loc: str, depart_time: datetime, seats_needed: int, expected_price: Decimal) -> Order:
        if self.credit_score < 60:
            raise BusinessRuleError("Credit score too low to publish order.")
        return Order(
            order_id=order_id,
            passenger_id=self.user_id,
            start_loc=start_loc,
            end_loc=end_loc,
            depart_time=depart_time,
            seats_needed=seats_needed,
            expected_price=expected_price,
        )

    def cancel_order(self, order: Order) -> None:
        if order.passenger_id != self.user_id:
            raise BusinessRuleError("Cannot cancel others' orders.")
        order.cancel()

    def pay_order(self, order: Order, amount: Decimal) -> Payment:
        if order.status != "LOCKED" or not order.owner_id:
            raise BusinessRuleError("Order must be locked before payment.")
        payment = Payment(
            payment_id=f"p-{int(datetime.now().timestamp())}",
            order_id=order.order_id,
            payer_id=self.user_id,
            payee_id=order.owner_id,
            amount=amount,
        )
        payment.pay()
        order.status = "PAID"
        return payment

    def view_orders(self, orders: List[Order]) -> List[Order]:
        return [o for o in orders if o.passenger_id == self.user_id]

    def rate_or_feedback(self, content: str, order_id: Optional[str] = None, target_user_id: Optional[str] = None) -> Feedback:
        return self.complain(content=content, target_user_id=target_user_id, order_id=order_id)


@dataclass
class Admin(User):
    @classmethod
    def register(cls, **kwargs):
        raise BusinessRuleError("Admin cannot be registered from public flow.")

    def manage_users(self, users: List[User]) -> List[User]:
        return users

    def manage_orders(self, orders: List[Order]) -> List[Order]:
        return orders

    def manage_feedbacks(self, feedbacks: List[Feedback]) -> List[Feedback]:
        return feedbacks

    def review_withdraw(self, request: WithdrawRequest, approve: bool) -> None:
        if approve:
            request.approve(self.user_id)
        else:
            request.reject(self.user_id)

    def view_statistics(self, users: List[User], orders: List[Order]) -> dict:
        return {
            "userCount": len(users),
            "orderCount": len(orders),
            "activeOrderCount": len([o for o in orders if o.status in {"CREATED", "LOCKED", "PAID"}]),
        }
