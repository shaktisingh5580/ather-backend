"""
Pydantic Models for the Smart Parking System API.
All request/response schemas used across the backend.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class GateType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"


class ResolvedStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"
    GUARDIAN_BLOCKED = "GUARDIAN_BLOCKED"


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    STUDENT = "student"
    GUEST = "guest"


class VehicleType(str, Enum):
    TWO_WHEELER = "2-wheeler"
    FOUR_WHEELER = "4-wheeler"


class AlertType(str, Enum):
    GUARDIAN_BLOCK = "GUARDIAN_BLOCK"
    UNKNOWN_PLATE = "UNKNOWN_PLATE"
    BLACKLIST = "BLACKLIST"
    PAGING = "PAGING"


class ZoneType(str, Enum):
    BIKE = "bike"
    CAR = "car"
    MIXED = "mixed"
    BUFFER = "buffer"


# ═══════════════════════════════════════════════════════════════
#  GATE
# ═══════════════════════════════════════════════════════════════

class GateEventPayload(BaseModel):
    """Payload from ALPR camera / mock simulator."""
    plate_number: str = Field(..., example="GJ05TK9111")
    gate_type: GateType = Field(..., example="entry")
    confidence: float = Field(0.95, ge=0, le=1)
    gate_id: str = Field("gate_2", example="gate_2")
    image_url: Optional[str] = Field(None, description="Gate camera snapshot URL")


class ManualEntryPayload(BaseModel):
    """Admin manually enters plate when OCR fails."""
    plate_number: str = Field(..., example="GJ05TK9111")
    gate_type: GateType = Field(..., example="entry")
    gate_id: str = Field("gate_2")
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    notes: Optional[str] = None


class ResolveEventPayload(BaseModel):
    """Admin resolves an UNKNOWN or GUARDIAN event."""
    action: str = Field(..., example="allow", description="allow | deny")
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════════════

class UserRegisterPayload(BaseModel):
    """New user registration via college email."""
    full_name: str = Field(..., example="Rahul Sharma")
    email: str = Field(..., example="21ce001@scet.ac.in")
    phone: str = Field(..., example="+919876543210")
    role: UserRole = Field(UserRole.STUDENT)
    default_zone: Optional[str] = Field(None, example="zone_a")


class UserLoginPayload(BaseModel):
    """Email-based login."""
    email: str = Field(..., example="21ce001@scet.ac.in")


class UserUpdatePayload(BaseModel):
    """Update user profile data."""
    user_id: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class VehicleRegistration(BaseModel):
    """Register a vehicle to a user."""
    plate_number: str = Field(..., example="GJ05TK9111")
    owner_id: str = Field(..., description="User UUID")
    vehicle_type: VehicleType = Field(VehicleType.TWO_WHEELER)
    admin_override: Optional[bool] = Field(False, description="Bypass the 1-vehicle per user limit")


class GuardianToggle(BaseModel):
    """Toggle guardian mode for a user."""
    user_id: str
    enabled: bool


class PageVehicleRequest(BaseModel):
    """Report a blocked car for paging."""
    blocked_plate: str = Field(..., example="GJ05RD6677")
    reporter_id: Optional[str] = None
    message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  VISITOR
# ═══════════════════════════════════════════════════════════════

class VisitorRegisterPayload(BaseModel):
    """Pre-register a visitor."""
    host_id: str = Field(..., description="User UUID of the host")
    visitor_name: str = Field(..., example="Visitor Singh")
    visitor_phone: Optional[str] = Field(None, example="+919876543210")
    plate_number: Optional[str] = Field(None, example="GJ05XX1234")
    expected_date: Optional[str] = Field(None, example="2026-03-07")


# ═══════════════════════════════════════════════════════════════
#  ADMIN / ZONES
# ═══════════════════════════════════════════════════════════════

class ZoneInfo(BaseModel):
    """Zone data (read from Firebase)."""
    zone_id: str
    name: str
    capacity: int
    current_count: int
    zone_type: ZoneType
    is_buffer: bool = False
    original_type: Optional[str] = None


class SystemAlert(BaseModel):
    """System alert for admin dashboard."""
    alert_id: Optional[str] = None
    type: AlertType
    plate_number: str
    message: str
    timestamp: int
    resolved: bool = False
    image_url: Optional[str] = None
