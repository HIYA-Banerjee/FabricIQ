from sqlalchemy.orm import Session
from app.models.models import Machine
from typing import List, Optional

class MachineRepository:
    @staticmethod
    def get_by_id(db: Session, machine_id: str, tenant_id: str) -> Optional[Machine]:
        return db.query(Machine).filter(Machine.id == machine_id, Machine.tenant_id == tenant_id).first()

    @staticmethod
    def get_all(db: Session, tenant_id: str) -> List[Machine]:
        return db.query(Machine).filter(Machine.tenant_id == tenant_id).all()

    @staticmethod
    def create(db: Session, machine: Machine) -> Machine:
        db.add(machine)
        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def update(db: Session, db_machine: Machine, update_data: dict) -> Machine:
        for key, value in update_data.items():
            if value is not None:
                setattr(db_machine, key, value)
        db.commit()
        db.refresh(db_machine)
        return db_machine
