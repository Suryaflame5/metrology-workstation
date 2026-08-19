"""
Fleet Management and Inventory System for Premium Edition.

Provides comprehensive instrument lifecycle management, maintenance scheduling,
location tracking, cost analysis, and QR/barcode integration capabilities.
"""

import uuid
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from enum import Enum

from ..db import DB_PATH, get_calculation, list_calculations
from ..config import ensure_app_directories
import sqlite3
import os


class InstrumentStatus(Enum):
    """Instrument lifecycle status enumeration."""
    ACTIVE = "ACTIVE"
    CALIBRATION_DUE = "CALIBRATION_DUE"
    MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    RETIRED = "RETIRED"
    LOST = "LOST"


class InstrumentCategory(Enum):
    """Instrument category enumeration."""
    DIMENSIONAL = "DIMENSIONAL"
    ELECTRICAL = "ELECTRICAL"
    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    MASS = "MASS"
    OPTICAL = "OPTICAL"
    FORCE = "FORCE"
    OTHER = "OTHER"


class MaintenancePriority(Enum):
    """Maintenance priority levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ROUTINE = "ROUTINE"


class FleetManagementService:
    """
    Enterprise-grade fleet management system for complete instrument lifecycle tracking,
    maintenance scheduling, and inventory optimization.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._init_fleet_database()
    
    def _init_fleet_database(self):
        """Initialize fleet management database schema."""
        ensure_app_directories()
        
        # Use separate fleet database
        fleet_db_path = os.path.join(os.path.dirname(self.db_path), "metrology_fleet.db")
        
        conn = sqlite3.connect(fleet_db_path)
        cursor = conn.cursor()
        
        # Instruments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instruments (
                id TEXT PRIMARY KEY,
                asset_tag TEXT UNIQUE NOT NULL,
                serial_number TEXT,
                instrument_name TEXT NOT NULL,
                instrument_model TEXT,
                manufacturer TEXT,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                purchase_date TEXT,
                purchase_cost DECIMAL(10,2),
                location TEXT,
                department TEXT,
                custodian TEXT,
                calibration_interval_months INTEGER DEFAULT 12,
                last_calibration_date TEXT,
                next_calibration_date TEXT,
                calibration_provider TEXT,
                qr_code TEXT,
                barcode TEXT,
                specifications TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Maintenance records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id TEXT PRIMARY KEY,
                instrument_id TEXT NOT NULL,
                maintenance_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT,
                scheduled_date TEXT,
                completed_date TEXT,
                technician TEXT,
                cost DECIMAL(10,2),
                status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (instrument_id) REFERENCES instruments(id)
            )
        """)
        
        # Location history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS location_history (
                id TEXT PRIMARY KEY,
                instrument_id TEXT NOT NULL,
                location TEXT NOT NULL,
                department TEXT,
                custodian TEXT,
                transfer_date TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (instrument_id) REFERENCES instruments(id)
            )
        """)
        
        # Calibration history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_history (
                id TEXT PRIMARY KEY,
                instrument_id TEXT NOT NULL,
                calibration_date TEXT NOT NULL,
                next_due_date TEXT NOT NULL,
                calibration_provider TEXT,
                certificate_number TEXT,
                result_verdict TEXT,
                total_cost DECIMAL(10,2),
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (instrument_id) REFERENCES instruments(id)
            )
        """)
        
        # Cost tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_tracking (
                id TEXT PRIMARY KEY,
                instrument_id TEXT NOT NULL,
                cost_type TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                vendor TEXT,
                invoice_number TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (instrument_id) REFERENCES instruments(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_fleet_db_path(self) -> str:
        """Get the fleet database path."""
        return os.path.join(os.path.dirname(self.db_path), "metrology_fleet.db")
    
    def add_instrument(self, instrument_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new instrument to the fleet inventory.
        """
        instrument_id = instrument_data.get('id') or f"INST-{str(uuid.uuid4().int)[:8]}"
        asset_tag = instrument_data.get('asset_tag') or f"ASSET-{str(uuid.uuid4().int)[:6]}"
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Calculate next calibration date if interval provided
        cal_interval = instrument_data.get('calibration_interval_months', 12)
        last_cal = instrument_data.get('last_calibration_date')
        if last_cal:
            next_cal = (datetime.fromisoformat(last_cal) + timedelta(days=cal_interval*30)).isoformat()
        else:
            next_cal = (datetime.now(timezone.utc) + timedelta(days=cal_interval*30)).isoformat()
        
        # Generate QR code data (placeholder for actual QR generation)
        qr_data = f"METROLOGY:{instrument_id}:{asset_tag}"
        
        instrument_record = {
            "id": instrument_id,
            "asset_tag": asset_tag,
            "serial_number": instrument_data.get('serial_number', ''),
            "instrument_name": instrument_data['instrument_name'],
            "instrument_model": instrument_data.get('instrument_model', ''),
            "manufacturer": instrument_data.get('manufacturer', ''),
            "category": instrument_data.get('category', InstrumentCategory.OTHER.value),
            "status": instrument_data.get('status', InstrumentStatus.ACTIVE.value),
            "purchase_date": instrument_data.get('purchase_date'),
            "purchase_cost": instrument_data.get('purchase_cost'),
            "location": instrument_data.get('location', 'Main Laboratory'),
            "department": instrument_data.get('department', ''),
            "custodian": instrument_data.get('custodian', ''),
            "calibration_interval_months": cal_interval,
            "last_calibration_date": last_cal,
            "next_calibration_date": next_cal,
            "calibration_provider": instrument_data.get('calibration_provider', ''),
            "qr_code": qr_data,
            "barcode": instrument_data.get('barcode', asset_tag),
            "specifications": json.dumps(instrument_data.get('specifications', {})),
            "notes": instrument_data.get('notes', ''),
            "created_at": now,
            "updated_at": now
        }
        
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO instruments (
                    id, asset_tag, serial_number, instrument_name, instrument_model, manufacturer,
                    category, status, purchase_date, purchase_cost, location, department, custodian,
                    calibration_interval_months, last_calibration_date, next_calibration_date,
                    calibration_provider, qr_code, barcode, specifications, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instrument_record["id"], instrument_record["asset_tag"], instrument_record["serial_number"],
                instrument_record["instrument_name"], instrument_record["instrument_model"], 
                instrument_record["manufacturer"], instrument_record["category"], instrument_record["status"],
                instrument_record["purchase_date"], instrument_record["purchase_cost"], 
                instrument_record["location"], instrument_record["department"], instrument_record["custodian"],
                instrument_record["calibration_interval_months"], instrument_record["last_calibration_date"],
                instrument_record["next_calibration_date"], instrument_record["calibration_provider"],
                instrument_record["qr_code"], instrument_record["barcode"], instrument_record["specifications"],
                instrument_record["notes"], instrument_record["created_at"], instrument_record["updated_at"]
            ))
            conn.commit()
            
            # Record initial location
            self._record_location_change(instrument_id, instrument_record["location"], 
                                        instrument_record["department"], instrument_record["custodian"],
                                        "Initial instrument registration")
            
            return instrument_record
            
        except sqlite3.IntegrityError:
            raise ValueError(f"Instrument with asset tag {asset_tag} already exists")
        finally:
            conn.close()
    
    def _record_location_change(self, instrument_id: str, location: str, department: str, 
                               custodian: str, reason: str):
        """Record a location change in the history."""
        now = datetime.now(timezone.utc).isoformat()
        location_id = f"LOC-{str(uuid.uuid4().int)[:8]}"
        
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO location_history (id, instrument_id, location, department, custodian, transfer_date, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (location_id, instrument_id, location, department, custodian, now, reason, now))
        
        conn.commit()
        conn.close()
    
    def get_instrument(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve instrument details by ID."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM instruments WHERE id = ?", (instrument_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            instrument = dict(zip(columns, row))
            
            # Parse JSON fields
            if instrument.get('specifications'):
                instrument['specifications'] = json.loads(instrument['specifications'])
            
            return instrument
        
        return None
    
    def list_instruments(self, status: Optional[str] = None, 
                        category: Optional[str] = None,
                        location: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """List instruments with optional filtering."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        query = "SELECT * FROM instruments WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if location:
            query += " AND location = ?"
            params.append(location)
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        instruments = [dict(zip(columns, row)) for row in rows]
        
        # Parse JSON fields
        for instrument in instruments:
            if instrument.get('specifications'):
                instrument['specifications'] = json.loads(instrument['specifications'])
        
        conn.close()
        return instruments
    
    def update_instrument_status(self, instrument_id: str, new_status: str, 
                                reason: str = "") -> Dict[str, Any]:
        """Update instrument status with audit trail."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE instruments 
            SET status = ?, updated_at = ?, notes = CASE 
                WHEN notes IS NULL OR notes = '' THEN ?
                ELSE notes || ' | ' || ?
            END
            WHERE id = ?
        """, (new_status, now, reason, reason, instrument_id))
        
        conn.commit()
        conn.close()
        
        return self.get_instrument(instrument_id)
    
    def schedule_maintenance(self, instrument_id: str, maintenance_type: str,
                            priority: str, description: str, 
                            scheduled_date: str, technician: str = "") -> Dict[str, Any]:
        """Schedule maintenance for an instrument."""
        maintenance_id = f"MAINT-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO maintenance_records (
                id, instrument_id, maintenance_type, priority, description, 
                scheduled_date, technician, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (maintenance_id, instrument_id, maintenance_type, priority, 
              description, scheduled_date, technician, "SCHEDULED", now))
        
        conn.commit()
        conn.close()
        
        # Update instrument status if maintenance is critical
        if priority == MaintenancePriority.CRITICAL.value:
            self.update_instrument_status(instrument_id, InstrumentStatus.MAINTENANCE_REQUIRED.value,
                                         f"Critical maintenance scheduled: {maintenance_type}")
        
        return {"maintenance_id": maintenance_id, "status": "SCHEDULED"}
    
    def complete_maintenance(self, maintenance_id: str, cost: float = 0.0,
                           notes: str = "") -> Dict[str, Any]:
        """Mark maintenance as completed and record cost."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE maintenance_records 
            SET completed_date = ?, status = 'COMPLETED', cost = ?, notes = ?
            WHERE id = ?
        """, (now, cost, notes, maintenance_id))
        
        # Get instrument_id for cost tracking
        cursor.execute("SELECT instrument_id FROM maintenance_records WHERE id = ?", (maintenance_id,))
        instrument_id = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        # Record cost if provided
        if cost > 0:
            self._record_cost(instrument_id, "MAINTENANCE", cost, 
                            f"Maintenance {maintenance_id}", now)
        
        # Reset instrument status if it was maintenance required
        instrument = self.get_instrument(instrument_id)
        if instrument and instrument['status'] == InstrumentStatus.MAINTENANCE_REQUIRED.value:
            self.update_instrument_status(instrument_id, InstrumentStatus.ACTIVE.value,
                                         "Maintenance completed")
        
        return {"maintenance_id": maintenance_id, "status": "COMPLETED"}
    
    def _record_cost(self, instrument_id: str, cost_type: str, amount: float,
                    description: str, date: str, vendor: str = "", 
                    invoice_number: str = ""):
        """Record a cost for an instrument."""
        cost_id = f"COST-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cost_tracking (
                id, instrument_id, cost_type, amount, description, date, vendor, invoice_number, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cost_id, instrument_id, cost_type, amount, description, date, 
              vendor, invoice_number, now))
        
        conn.commit()
        conn.close()
    
    def transfer_instrument(self, instrument_id: str, new_location: str,
                           new_department: str = "", new_custodian: str = "",
                           reason: str = "Location transfer") -> Dict[str, Any]:
        """Transfer instrument to new location/custodian."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE instruments 
            SET location = ?, department = ?, custodian = ?, updated_at = ?
            WHERE id = ?
        """, (new_location, new_department, new_custodian, now, instrument_id))
        
        conn.commit()
        conn.close()
        
        # Record location history
        self._record_location_change(instrument_id, new_location, new_department,
                                   new_custodian, reason)
        
        return self.get_instrument(instrument_id)
    
    def get_instrument_history(self, instrument_id: str) -> Dict[str, Any]:
        """Get complete history for an instrument including maintenance, locations, and costs."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        # Maintenance history
        cursor.execute("""
            SELECT * FROM maintenance_records 
            WHERE instrument_id = ? 
            ORDER BY scheduled_date DESC
        """, (instrument_id,))
        maint_columns = [desc[0] for desc in cursor.description]
        maintenance_history = [dict(zip(maint_columns, row)) for row in cursor.fetchall()]
        
        # Location history
        cursor.execute("""
            SELECT * FROM location_history 
            WHERE instrument_id = ? 
            ORDER BY transfer_date DESC
        """, (instrument_id,))
        loc_columns = [desc[0] for desc in cursor.description]
        location_history = [dict(zip(loc_columns, row)) for row in cursor.fetchall()]
        
        # Cost history
        cursor.execute("""
            SELECT * FROM cost_tracking 
            WHERE instrument_id = ? 
            ORDER BY date DESC
        """, (instrument_id,))
        cost_columns = [desc[0] for desc in cursor.description]
        cost_history = [dict(zip(cost_columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "instrument_id": instrument_id,
            "maintenance_history": maintenance_history,
            "location_history": location_history,
            "cost_history": cost_history
        }
    
    def get_calibration_schedule(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get instruments due for calibration within specified timeframe."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()
        
        cursor.execute("""
            SELECT * FROM instruments 
            WHERE next_calibration_date <= ? 
            AND status IN ('ACTIVE', 'CALIBRATION_DUE')
            ORDER BY next_calibration_date ASC
        """, (cutoff_date,))
        
        columns = [desc[0] for desc in cursor.description]
        instruments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for instrument in instruments:
            if instrument.get('specifications'):
                instrument['specifications'] = json.loads(instrument['specifications'])
        
        conn.close()
        return instruments
    
    def update_calibration_status(self, instrument_id: str, calibration_date: str,
                                 next_due_date: str, provider: str, 
                                 certificate_number: str, verdict: str,
                                 cost: float = 0.0) -> Dict[str, Any]:
        """Update instrument calibration status after calibration."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        cal_id = f"CAL-{str(uuid.uuid4().int)[:8]}"
        
        # Update instrument
        cursor.execute("""
            UPDATE instruments 
            SET last_calibration_date = ?, next_calibration_date = ?,
                calibration_provider = ?, status = 'ACTIVE', updated_at = ?
            WHERE id = ?
        """, (calibration_date, next_due_date, provider, now, instrument_id))
        
        # Record calibration history
        cursor.execute("""
            INSERT INTO calibration_history (
                id, instrument_id, calibration_date, next_due_date, 
                calibration_provider, certificate_number, result_verdict, 
                total_cost, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cal_id, instrument_id, calibration_date, next_due_date, 
              provider, certificate_number, verdict, cost, now))
        
        conn.commit()
        conn.close()
        
        # Record calibration cost
        if cost > 0:
            self._record_cost(instrument_id, "CALIBRATION", cost,
                            f"Calibration by {provider}", calibration_date, provider, certificate_number)
        
        return self.get_instrument(instrument_id)
    
    def get_fleet_analytics(self) -> Dict[str, Any]:
        """Get comprehensive fleet analytics and statistics."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        # Total instruments by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM instruments 
            GROUP BY status
        """)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total instruments by category
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM instruments 
            GROUP BY category
        """)
        category_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Instruments by location
        cursor.execute("""
            SELECT location, COUNT(*) as count 
            FROM instruments 
            GROUP BY location
        """)
        location_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Upcoming calibrations
        upcoming_cal = self.get_calibration_schedule(30)
        
        # Overdue maintenance
        cursor.execute("""
            SELECT COUNT(*) FROM maintenance_records 
            WHERE scheduled_date < ? AND status = 'SCHEDULED'
        """, (datetime.now(timezone.utc).isoformat(),))
        overdue_maintenance = cursor.fetchone()[0]
        
        # Total fleet value
        cursor.execute("SELECT SUM(purchase_cost) FROM instruments WHERE purchase_cost IS NOT NULL")
        total_value = cursor.fetchone()[0] or 0.0
        
        # Total maintenance costs (last 12 months)
        one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        cursor.execute("""
            SELECT SUM(cost) FROM maintenance_records 
            WHERE completed_date >= ? AND cost IS NOT NULL
        """, (one_year_ago,))
        annual_maintenance_cost = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            "total_instruments": sum(status_counts.values()),
            "instruments_by_status": status_counts,
            "instruments_by_category": category_counts,
            "instruments_by_location": location_counts,
            "upcoming_calibrations": len(upcoming_cal),
            "overdue_maintenance": overdue_maintenance,
            "total_fleet_value": round(float(total_value), 2),
            "annual_maintenance_cost": round(float(annual_maintenance_cost), 2),
            "calibration_compliance_rate": self._calculate_calibration_compliance(),
            "average_instrument_age": self._calculate_average_age(),
            "utilization_rate": self._calculate_utilization_rate()
        }
    
    def _calculate_calibration_compliance(self) -> float:
        """Calculate calibration compliance rate."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM instruments 
            WHERE status IN ('ACTIVE', 'CALIBRATION_DUE')
            AND next_calibration_date >= ?
        """, (datetime.now(timezone.utc).isoformat(),))
        
        compliant = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM instruments 
            WHERE status IN ('ACTIVE', 'CALIBRATION_DUE')
        """)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return round((compliant / total * 100) if total > 0 else 0, 2)
    
    def _calculate_average_age(self) -> float:
        """Calculate average instrument age in years."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(julianday('now') - julianday(purchase_date)) / 365.25 
            FROM instruments 
            WHERE purchase_date IS NOT NULL
        """)
        
        avg_age = cursor.fetchone()[0]
        conn.close()
        
        return round(float(avg_age) if avg_age else 0, 2)
    
    def _calculate_utilization_rate(self) -> float:
        """Calculate instrument utilization rate (active vs total)."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM instruments WHERE status = 'ACTIVE'")
        active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM instruments WHERE status != 'RETIRED'")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return round((active / total * 100) if total > 0 else 0, 2)
    
    def generate_cost_analysis(self, instrument_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive cost analysis for instrument or fleet."""
        conn = sqlite3.connect(self._get_fleet_db_path())
        cursor = conn.cursor()
        
        if instrument_id:
            cursor.execute("""
                SELECT cost_type, SUM(amount) as total_cost, COUNT(*) as transaction_count
                FROM cost_tracking 
                WHERE instrument_id = ?
                GROUP BY cost_type
            """, (instrument_id,))
        else:
            cursor.execute("""
                SELECT cost_type, SUM(amount) as total_cost, COUNT(*) as transaction_count
                FROM cost_tracking 
                GROUP BY cost_type
            """)
        
        cost_by_type = {row[0]: {"total": float(row[1]), "count": row[2]} 
                       for row in cursor.fetchall()}
        
        # Calculate total cost of ownership
        cursor.execute("""
            SELECT SUM(amount) FROM cost_tracking 
            WHERE instrument_id = ? 
        """ if instrument_id else """
            SELECT SUM(amount) FROM cost_tracking
        """)
        
        params = (instrument_id,) if instrument_id else ()
        cursor.execute(cursor.lastrowid and """
            SELECT SUM(amount) FROM cost_tracking WHERE instrument_id = ?
        """ or """
            SELECT SUM(amount) FROM cost_tracking
        """, params)
        
        total_cost = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            "instrument_id": instrument_id,
            "total_cost_of_ownership": round(float(total_cost), 2),
            "cost_breakdown_by_type": cost_by_type,
            "cost_per_month": self._calculate_monthly_cost(instrument_id, total_cost)
        }
    
    def _calculate_monthly_cost(self, instrument_id: Optional[str], total_cost: float) -> float:
        """Calculate monthly cost over instrument lifetime."""
        if not instrument_id or total_cost == 0:
            return 0.0
        
        instrument = self.get_instrument(instrument_id)
        if not instrument or not instrument.get('purchase_date'):
            return 0.0
        
        purchase_date = datetime.fromisoformat(instrument['purchase_date'])
        months_owned = max(1, (datetime.now(timezone.utc) - purchase_date).days / 30)
        
        return round(total_cost / months_owned, 2)


# Singleton instance for service layer
_fleet_service = None

def get_fleet_service(db_path: Optional[str] = None) -> FleetManagementService:
    """Get or create the fleet management service singleton."""
    global _fleet_service
    if _fleet_service is None:
        _fleet_service = FleetManagementService(db_path)
    return _fleet_service

# Convenience functions for common operations
def add_instrument(instrument_data: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """Add a new instrument to the fleet."""
    service = get_fleet_service(db_path)
    return service.add_instrument(instrument_data)

def get_instrument(instrument_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get instrument details."""
    service = get_fleet_service(db_path)
    return service.get_instrument(instrument_id)

def list_instruments(status: Optional[str] = None, category: Optional[str] = None,
                    location: Optional[str] = None, limit: int = 100,
                    db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """List instruments with optional filtering."""
    service = get_fleet_service(db_path)
    return service.list_instruments(status, category, location, limit)

def schedule_maintenance(instrument_id: str, maintenance_type: str, priority: str,
                        description: str, scheduled_date: str, technician: str = "",
                        db_path: Optional[str] = None) -> Dict[str, Any]:
    """Schedule maintenance for an instrument."""
    service = get_fleet_service(db_path)
    return service.schedule_maintenance(instrument_id, maintenance_type, priority,
                                       description, scheduled_date, technician)

def get_calibration_schedule(days_ahead: int = 30, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get upcoming calibration schedule."""
    service = get_fleet_service(db_path)
    return service.get_calibration_schedule(days_ahead)

def get_fleet_analytics(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive fleet analytics."""
    service = get_fleet_service(db_path)
    return service.get_fleet_analytics()