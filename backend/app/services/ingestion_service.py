import pandas as pd
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Order
from loguru import logger

class IngestionService:
    @staticmethod
    def process_file_upload(db: Session, file_contents: bytes, filename: str, tenant_id: str):
        """
        Process Excel/CSV upload of Order records, validate data quality, check for duplicate Order IDs
        within the tenant, clean fields, and commit to the database.
        Returns a dictionary summarizing success metrics and validation logs.
        """
        logger.info(f"Ingesting file {filename} for tenant {tenant_id}")
        
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(BytesIO(file_contents))
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(BytesIO(file_contents))
            else:
                return {"success": False, "errors": ["Unsupported file format. Please upload CSV or Excel."]}
        except Exception as e:
            logger.error(f"Error parsing file upload: {str(e)}")
            return {"success": False, "errors": [f"Error reading file: {str(e)}"]}
            
        validation_errors = []
        rows_to_insert = []
        duplicate_count = 0
        
        # Required columns mapping (case-insensitive conversion)
        df.columns = [col.strip().lower() for col in df.columns]
        
        required_cols = ["id", "customer", "material_type", "quantity", "start_date", "due_date"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return {"success": False, "errors": [f"Missing required columns: {', '.join(missing_cols)}"]}

        for index, row in df.iterrows():
            row_num = index + 2  # Excel row numbers start at 2
            
            # Extract attributes
            order_id = str(row["id"]).strip()
            customer = str(row["customer"]).strip()
            material_type = str(row["material_type"]).strip()
            quantity = row["quantity"]
            start_date_raw = row["start_date"]
            due_date_raw = row["due_date"]
            
            # Optional attributes
            priority = str(row.get("priority", "Medium")).strip()
            revenue = row.get("revenue", 0.0)
            status = str(row.get("status", "Pending")).strip()
            progress = row.get("progress", 0.0)

            # 1. Validation: check for empty values
            if not order_id or order_id == "nan" or not customer or not material_type:
                validation_errors.append(f"Row {row_num}: Missing primary values (ID, Customer, or Material).")
                continue
                
            # 2. Validation: check impossible quantities and revenue
            try:
                quantity = float(quantity)
                if quantity <= 0:
                    validation_errors.append(f"Row {row_num}: Impossible order quantity {quantity}. Must be > 0.")
                    continue
            except (ValueError, TypeError):
                validation_errors.append(f"Row {row_num}: Invalid order quantity format.")
                continue

            try:
                revenue = float(revenue)
                if revenue < 0:
                    validation_errors.append(f"Row {row_num}: Negative revenue value {revenue} not allowed.")
                    continue
            except (ValueError, TypeError):
                revenue = 0.0
                
            try:
                progress = float(progress)
                if not (0.0 <= progress <= 1.0):
                    validation_errors.append(f"Row {row_num}: Progress must be between 0.0 and 1.0.")
                    continue
            except (ValueError, TypeError):
                progress = 0.0

            # 3. Validation: Date parsing and logical checks
            try:
                if isinstance(start_date_raw, str):
                    start_date = pd.to_datetime(start_date_raw).to_pydatetime()
                else:
                    start_date = pd.to_datetime(start_date_raw).to_pydatetime()
                    
                if isinstance(due_date_raw, str):
                    due_date = pd.to_datetime(due_date_raw).to_pydatetime()
                else:
                    due_date = pd.to_datetime(due_date_raw).to_pydatetime()
                    
                if due_date <= start_date:
                    validation_errors.append(f"Row {row_num}: Due Date ({due_date}) must be after Start Date ({start_date}).")
                    continue
            except Exception:
                validation_errors.append(f"Row {row_num}: Invalid date formats. Use YYYY-MM-DD.")
                continue

            # 4. Duplicate checks (internal database query)
            existing_order = db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()
            if existing_order:
                duplicate_count += 1
                validation_errors.append(f"Row {row_num}: Order ID {order_id} already exists in the database. Skipped.")
                continue
                
            # Append validated object
            rows_to_insert.append(
                Order(
                    id=order_id,
                    tenant_id=tenant_id,
                    customer=customer,
                    material_type=material_type,
                    quantity=quantity,
                    start_date=start_date,
                    due_date=due_date,
                    status=status,
                    progress=progress,
                    priority=priority,
                    revenue=revenue
                )
            )

        if rows_to_insert:
            try:
                db.bulk_save_objects(rows_to_insert)
                db.commit()
                logger.info(f"Successfully ingested {len(rows_to_insert)} orders for tenant {tenant_id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Database error during ingestion: {str(e)}")
                return {"success": False, "errors": [f"Database write failure: {str(e)}"]}
                
        return {
            "success": True if not validation_errors or len(rows_to_insert) > 0 else False,
            "ingested_count": len(rows_to_insert),
            "duplicate_count": duplicate_count,
            "errors": validation_errors
        }
