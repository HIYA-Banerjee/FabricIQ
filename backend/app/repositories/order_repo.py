from sqlalchemy.orm import Session
from app.models.models import Order
from typing import List, Optional

class OrderRepository:
    @staticmethod
    def get_by_id(db: Session, order_id: str, tenant_id: str) -> Optional[Order]:
        return db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()

    @staticmethod
    def get_all(db: Session, tenant_id: str) -> List[Order]:
        return db.query(Order).filter(Order.tenant_id == tenant_id).all()

    @staticmethod
    def create(db: Session, order: Order) -> Order:
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def update(db: Session, db_order: Order, update_data: dict) -> Order:
        for key, value in update_data.items():
            if value is not None:
                setattr(db_order, key, value)
        db.commit()
        db.refresh(db_order)
        return db_order

    @staticmethod
    def delete(db: Session, order_id: str, tenant_id: str) -> bool:
        db_order = db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()
        if db_order:
            db.delete(db_order)
            db.commit()
            return True
        return False
