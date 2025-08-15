"""
Business validation utilities for Booking Operations Service
Contains complex validation logic for business rules
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from common.enums import (
    BookingOverallStatus, BookingLineStatus,
    ServiceType, OperationModel, SupplierStatus
)


class BookingValidator:
    """Validation rules for bookings"""

    @staticmethod
    def validate_booking_dates(
        booking_date: datetime,
        service_date: datetime,
        advance_booking_hours: Optional[int] = None,
        cutoff_hours: Optional[int] = None
    ) -> None:
        """
        Validate booking and service dates

        Args:
            booking_date: Date of booking
            service_date: Date of service
            advance_booking_hours: Required advance booking time in hours
            cutoff_hours: Booking cutoff time in hours

        Raises:
            HTTPException: If validation fails
        """
        # Service date must be in the future
        if service_date <= booking_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service date must be after booking date"
            )

        # Check advance booking requirement
        if advance_booking_hours:
            min_booking_date = service_date - timedelta(hours=advance_booking_hours)
            if booking_date > min_booking_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Booking must be made at least {advance_booking_hours} hours in advance"
                )

        # Check cutoff time
        if cutoff_hours:
            cutoff_date = service_date - timedelta(hours=cutoff_hours)
            if booking_date > cutoff_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Booking cutoff is {cutoff_hours} hours before service"
                )

    @staticmethod
    def validate_passenger_count(
        passenger_count: int,
        min_participants: Optional[int] = None,
        max_participants: Optional[int] = None
    ) -> None:
        """
        Validate passenger count against service limits

        Args:
            passenger_count: Number of passengers
            min_participants: Minimum required participants
            max_participants: Maximum allowed participants

        Raises:
            HTTPException: If validation fails
        """
        if min_participants and passenger_count < min_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum {min_participants} participants required"
            )

        if max_participants and passenger_count > max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {max_participants} participants allowed"
            )

    @staticmethod
    def validate_booking_modification(
        booking_status: BookingOverallStatus,
        service_date: datetime,
        modification_cutoff_hours: int = 24
    ) -> None:
        """
        Validate if booking can be modified

        Args:
            booking_status: Current booking status
            service_date: Service date
            modification_cutoff_hours: Hours before service when modifications are not allowed

        Raises:
            HTTPException: If modification is not allowed
        """
        # Check status
        if booking_status in [BookingOverallStatus.cancelled, BookingOverallStatus.completed]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify booking with status: {booking_status.value}"
            )

        # Check time constraint
        cutoff_time = service_date - timedelta(hours=modification_cutoff_hours)
        if datetime.utcnow() > cutoff_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify booking within {modification_cutoff_hours} hours of service"
            )

    @staticmethod
    def calculate_cancellation_fee(
        total_amount: Decimal,
        service_date: datetime,
        cancellation_policy: Dict[str, Any]
    ) -> Decimal:
        """
        Calculate cancellation fee based on policy

        Args:
            total_amount: Total booking amount
            service_date: Service date
            cancellation_policy: Cancellation policy rules

        Returns:
            Cancellation fee amount
        """
        if not cancellation_policy:
            return Decimal(0)

        hours_until_service = (service_date - datetime.utcnow()).total_seconds() / 3600

        # Apply cancellation rules
        rules = cancellation_policy.get('cancellation_rules', [])
        for rule in sorted(rules, key=lambda x: x.get('hours_before', 0), reverse=True):
            if hours_until_service >= rule.get('hours_before', 0):
                refund_percentage = rule.get('refund_percentage', 0)
                fee_amount = rule.get('fee_amount', 0)

                # Calculate fee
                percentage_fee = total_amount * (100 - refund_percentage) / 100
                return max(percentage_fee, Decimal(fee_amount))

        # No refund if no matching rule
        return total_amount


class ServiceValidator:
    """Validation rules for services"""

    @staticmethod
    def validate_service_availability(
        db: Session,
        service_id: int,
        service_date: date,
        passenger_count: int
    ) -> Dict[str, Any]:
        """
        Check if service is available for booking

        Args:
            db: Database session
            service_id: Service ID
            service_date: Service date
            passenger_count: Number of passengers

        Returns:
            Availability information

        Raises:
            HTTPException: If service is not available
        """
        from services.models import Service, ServiceDailyCapacity

        # Get service
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service with ID {service_id} not found"
            )

        if not service.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service is not active"
            )

        # Check daily capacity
        daily_capacity = db.query(ServiceDailyCapacity).filter(
            ServiceDailyCapacity.service_id == service_id,
            ServiceDailyCapacity.service_date == service_date
        ).first()

        if daily_capacity:
            if not daily_capacity.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Service is not available on this date"
                )

            if daily_capacity.is_blocked:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service is blocked: {daily_capacity.block_reason}"
                )

            available_capacity = daily_capacity.available_capacity
            if passenger_count > available_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_capacity} spots available"
                )
        else:
            # Use default capacity
            max_capacity = service.max_participants or 999
            if passenger_count > max_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum capacity is {max_capacity}"
                )

        return {
            "service_id": service_id,
            "service_name": service.name,
            "is_available": True,
            "available_capacity": daily_capacity.available_capacity if daily_capacity else service.max_participants or 999
        }

    @staticmethod
    def validate_service_operation_model(
        service_type: ServiceType,
        operation_model: OperationModel
    ) -> None:
        """
        Validate if operation model is compatible with service type

        Args:
            service_type: Type of service
            operation_model: Operation model

        Raises:
            HTTPException: If combination is invalid
        """
        invalid_combinations = {
            # ServiceType.transfer: [OperationModel.OPEN],  # OPEN doesn't exist in OperationModel
            # ServiceType.ticket: [OperationModel.SCHEDULED, OperationModel.CHARTER]  # These don't exist either
        }

        if service_type in invalid_combinations:
            if operation_model in invalid_combinations[service_type]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Operation model {operation_model.value} is not valid for service type {service_type.value}"
                )


class SupplierValidator:
    """Validation rules for suppliers"""

    @staticmethod
    def validate_supplier_status(
        supplier_status: SupplierStatus,
        operation: str = "booking"
    ) -> None:
        """
        Validate if supplier can perform operations

        Args:
            supplier_status: Supplier status
            operation: Operation being performed

        Raises:
            HTTPException: If operation is not allowed
        """
        if supplier_status == SupplierStatus.inactive:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot perform {operation} with inactive supplier"
            )

        if supplier_status == SupplierStatus.blacklist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot perform {operation} with suspended supplier"
            )

        if supplier_status == SupplierStatus.blacklist and operation != "view":  # PENDING doesn't exist, using blacklist
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot perform {operation} with pending supplier"
            )

    @staticmethod
    def validate_supplier_certifications(
        required_certifications: List[str],
        supplier_certifications: List[str]
    ) -> None:
        """
        Validate if supplier has required certifications

        Args:
            required_certifications: Required certifications
            supplier_certifications: Supplier's certifications

        Raises:
            HTTPException: If missing required certifications
        """
        if not required_certifications:
            return

        missing = set(required_certifications) - set(supplier_certifications or [])
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier missing required certifications: {', '.join(missing)}"
            )


class PriceValidator:
    """Validation rules for pricing"""

    @staticmethod
    def validate_price_consistency(
        base_price: Decimal,
        total_price: Decimal,
        passenger_count: int,
        discount_percentage: Decimal = Decimal(0)
    ) -> None:
        """
        Validate price calculations

        Args:
            base_price: Base price per passenger
            total_price: Total price
            passenger_count: Number of passengers
            discount_percentage: Discount percentage

        Raises:
            HTTPException: If prices are inconsistent
        """
        expected_price = base_price * passenger_count
        if discount_percentage > 0:
            expected_price = expected_price * (100 - discount_percentage) / 100

        # Allow small rounding differences
        if abs(total_price - expected_price) > Decimal(0.01):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Price inconsistency: expected {expected_price}, got {total_price}"
            )

    @staticmethod
    def validate_commission(
        total_amount: Decimal,
        commission_percentage: Decimal,
        commission_amount: Decimal
    ) -> None:
        """
        Validate commission calculations

        Args:
            total_amount: Total amount
            commission_percentage: Commission percentage
            commission_amount: Commission amount

        Raises:
            HTTPException: If commission is incorrect
        """
        expected_commission = total_amount * commission_percentage / 100

        # Allow small rounding differences
        if abs(commission_amount - expected_commission) > Decimal(0.01):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Commission inconsistency: expected {expected_commission}, got {commission_amount}"
            )

    @staticmethod
    def validate_currency_conversion(
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        exchange_rate: Decimal,
        converted_amount: Decimal
    ) -> None:
        """
        Validate currency conversion

        Args:
            amount: Original amount
            from_currency: Source currency
            to_currency: Target currency
            exchange_rate: Exchange rate
            converted_amount: Converted amount

        Raises:
            HTTPException: If conversion is incorrect
        """
        if from_currency == to_currency:
            if amount != converted_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Same currency conversion should not change amount"
                )
            return

        expected_amount = amount * exchange_rate

        # Allow 1% difference for exchange rate fluctuations
        tolerance = expected_amount * Decimal(0.01)
        if abs(converted_amount - expected_amount) > tolerance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Currency conversion error: expected ~{expected_amount}, got {converted_amount}"
            )


class DateValidator:
    """Validation rules for dates"""

    @staticmethod
    def validate_date_range(
        start_date: date,
        end_date: date,
        max_days: Optional[int] = None
    ) -> None:
        """
        Validate date range

        Args:
            start_date: Start date
            end_date: End date
            max_days: Maximum allowed days

        Raises:
            HTTPException: If date range is invalid
        """
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after or equal to start date"
            )

        if max_days:
            days_diff = (end_date - start_date).days
            if days_diff > max_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Date range cannot exceed {max_days} days"
                )

    @staticmethod
    def validate_business_hours(
        booking_time: datetime,
        business_hours: Dict[str, str]
    ) -> None:
        """
        Validate if booking is within business hours

        Args:
            booking_time: Time of booking
            business_hours: Business hours configuration

        Raises:
            HTTPException: If outside business hours
        """
        if not business_hours:
            return

        day_name = booking_time.strftime('%A').lower()
        day_hours = business_hours.get(day_name)

        if not day_hours:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service not available on {day_name}"
            )

        if day_hours == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service closed on {day_name}"
            )

        # Parse hours (format: "09:00-18:00")
        try:
            open_time, close_time = day_hours.split('-')
            open_hour, open_min = map(int, open_time.split(':'))
            close_hour, close_min = map(int, close_time.split(':'))

            booking_hour = booking_time.hour
            booking_min = booking_time.minute

            if booking_hour < open_hour or (booking_hour == open_hour and booking_min < open_min):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service opens at {open_time}"
                )

            if booking_hour > close_hour or (booking_hour == close_hour and booking_min > close_min):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service closes at {close_time}"
                )
        except ValueError:
            pass  # Invalid format, skip validation


class PassengerValidator:
    """Validation rules for passengers"""

    @staticmethod
    def validate_age_requirements(
        passenger_age: int,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        service_type: Optional[ServiceType] = None
    ) -> None:
        """
        Validate passenger age requirements

        Args:
            passenger_age: Age of passenger
            min_age: Minimum age requirement
            max_age: Maximum age requirement
            service_type: Type of service

        Raises:
            HTTPException: If age requirements not met
        """
        if min_age and passenger_age < min_age:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum age is {min_age} years"
            )

        if max_age and passenger_age > max_age:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum age is {max_age} years"
            )

        # Service-specific age restrictions
        if service_type == ServiceType.ADVENTURE and passenger_age < 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adventure services require minimum age of 12"
            )

    @staticmethod
    def validate_document_requirements(
        document_type: str,
        document_number: str,
        document_expiry: Optional[date] = None,
        travel_date: Optional[date] = None
    ) -> None:
        """
        Validate passenger document requirements

        Args:
            document_type: Type of document
            document_number: Document number
            document_expiry: Document expiry date
            travel_date: Travel date

        Raises:
            HTTPException: If document requirements not met
        """
        # Check document number format
        if document_type == "passport":
            if len(document_number) < 6 or len(document_number) > 20:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid passport number format"
                )

        # Check expiry
        if document_expiry and travel_date:
            # Passport should be valid for at least 6 months after travel
            min_validity = travel_date + timedelta(days=180)
            if document_expiry < min_validity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document must be valid for at least 6 months after travel date"
                )


# Export validators
__all__ = [
    'BookingValidator',
    'ServiceValidator',
    'SupplierValidator',
    'PriceValidator',
    'DateValidator',
    'PassengerValidator'
]
