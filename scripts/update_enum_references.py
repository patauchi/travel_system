#!/usr/bin/env python3
"""
Script to update all enum references from uppercase to lowercase
after the enum definition changes
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Define all the enum mappings that need to be updated
ENUM_MAPPINGS = {
    # booking-operations-service/common/enums.py
    'SupplierType': {
        'INDIVIDUAL': 'individual',
        'COMPANY': 'company',
        'GOVERNMENT': 'government',
    },
    'SupplierStatus': {
        'ACTIVE': 'active',
        'INACTIVE': 'inactive',
        'BLACKLIST': 'blacklist',
    },
    'ServiceType': {
        'ACCOMMODATION': 'accommodation',
        'TRANSFER': 'transfer',
        'TOUR': 'tour',
        'TRANSPORT': 'transport',
        'RESTAURANT': 'restaurant',
        'TICKET': 'ticket',
        'GUIDE': 'guide',
        'EQUIPMENT': 'equipment',
        'OTHER': 'other',
    },
    'OperationModel': {
        'NO_DEFINED': 'no_defined',
        'DIRECT': 'direct',
        'RESALE': 'resale',
        'WHITE_LABEL': 'white_label',
        'HYBRID': 'hybrid',
    },
    'TransferType': {
        'PRIVATE': 'private',
        'SHARED': 'shared',
        'SHUTTLE': 'shuttle',
        'EXECUTIVE': 'executive',
        'LUXURY': 'luxury',
    },
    'VehicleType': {
        'SEDAN': 'sedan',
        'SUV': 'suv',
        'VAN': 'van',
        'MINIBUS': 'minibus',
        'BUS': 'bus',
        'LIMOUSINE': 'limousine',
        'HELICOPTER': 'helicopter',
        'BOAT': 'boat',
        'OTHER': 'other',
    },
    'TourType': {
        'PRIVATE': 'private',
        'GROUP': 'group',
        'REGULAR': 'regular',
        'VIP': 'vip',
    },
    'DurationType': {
        'HOURS': 'hours',
        'HALF_DAY': 'half_day',
        'FULL_DAY': 'full_day',
        'MULTI_DAY': 'multi_day',
    },
    'BookingOverallStatus': {
        'PENDING': 'pending',
        'IN_PROGRESS': 'in_progress',
        'CONFIRMED': 'confirmed',
        'PARTIALLY_CANCELLED': 'partially_cancelled',
        'CANCELLED': 'cancelled',
        'COMPLETED': 'completed',
        'ARCHIVED': 'archived',
    },
    'BookingLineStatus': {
        'PENDING': 'pending',
        'CONFIRMING': 'confirming',
        'CONFIRMED': 'confirmed',
        'WAITLISTED': 'waitlisted',
        'MODIFIED': 'modified',
        'CANCELLED': 'cancelled',
        'FAILED': 'failed',
        'EXPIRED': 'expired',
        'COMPLETED': 'completed',
        'NO_SHOW': 'no_show',
    },
    'RiskLevel': {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'CRITICAL': 'critical',
    },
    'ServiceOperationStatus': {
        'PLANNED': 'planned',
        'READY': 'ready',
        'IN_PROGRESS': 'in_progress',
        'COMPLETED': 'completed',
        'CANCELLED': 'cancelled',
        'DELAYED': 'delayed',
        'INCIDENT': 'incident',
    },
    'OperationalAlert': {
        'NONE': 'none',
        'WEATHER': 'weather',
        'TRAFFIC': 'traffic',
        'SUPPLIER_ISSUE': 'supplier_issue',
        'PASSENGER_ISSUE': 'passenger_issue',
        'DOCUMENTATION': 'documentation',
        'PAYMENT': 'payment',
        'OTHER': 'other',
    },
    'PassengerGender': {
        'MALE': 'male',
        'FEMALE': 'female',
        'OTHER': 'other',
    },
    'DocumentType': {
        'PASSPORT': 'passport',
        'NATIONAL_ID': 'national_id',
        'DRIVER_LICENSE': 'driver_license',
        'BIRTH_CERTIFICATE': 'birth_certificate',
        'OTHER': 'other',
        'ID_CARD': 'id_card',
        'VISA': 'visa',
        'VACCINATION': 'vaccination',
        'INSURANCE': 'insurance',
    },
    'LoyaltyTier': {
        'BRONZE': 'bronze',
        'SILVER': 'silver',
        'GOLD': 'gold',
        'PLATINUM': 'platinum',
    },
    'RateType': {
        'STANDARD': 'standard',
        'SEASONAL': 'seasonal',
        'PROMOTIONAL': 'promotional',
        'SPECIAL': 'special',
        'CONTRACT': 'contract',
        'PACKAGE': 'package',
    },
    'PricingModel': {
        'PER_PERSON': 'per_person',
        'PER_GROUP': 'per_group',
        'PER_VEHICLE': 'per_vehicle',
        'PER_ROOM': 'per_room',
        'PER_HOUR': 'per_hour',
        'PER_DAY': 'per_day',
        'PER_UNIT': 'per_unit',
        'TIERED': 'tiered',
        'DYNAMIC': 'dynamic',
    },
    'SeasonType': {
        'LOW': 'low',
        'SHOULDER': 'shoulder',
        'HIGH': 'high',
        'PEAK': 'peak',
    },
    'CancellationPolicyType': {
        'FLEXIBLE': 'flexible',
        'MODERATE': 'moderate',
        'STRICT': 'strict',
        'SUPER_STRICT': 'super_strict',
        'NON_REFUNDABLE': 'non_refundable',
        'CUSTOM': 'custom',
    },
    'PassengerType': {
        'ADULT': 'adult',
        'CHILD': 'child',
        'INFANT': 'infant',
        'SENIOR': 'senior',
        'STUDENT': 'student',
    },

    # booking-operations-service/utils/audit.py
    'AuditAction': {
        'CREATE': 'create',
        'UPDATE': 'update',
        'DELETE': 'delete',
        'SOFT_DELETE': 'soft_delete',
        'RESTORE': 'restore',
        'STATUS_CHANGE': 'status_change',
        'CANCEL': 'cancel',
        'CONFIRM': 'confirm',
        'APPROVE': 'approve',
        'REJECT': 'reject',
        'LOGIN': 'login',
        'LOGOUT': 'logout',
        'EXPORT': 'export',
        'IMPORT': 'import',
    },

    # communication-service/common/enums.py
    'ChannelType': {
        'WHATSAPP': 'whatsapp',
        'MESSENGER': 'messenger',
        'INSTAGRAM': 'instagram',
        'EMAIL': 'email',
        'WEB': 'web',
        'TWILIO_WHATSAPP': 'twilio_whatsapp',
        'TWILIO_CALL': 'twilio_call',
        'WHATSAPP_BUSINESS': 'whatsapp_business',
        'FACEBOOK_MESSENGER': 'facebook_messenger',
        'PERSONAL_WHATSAPP': 'personal_whatsapp',
        'GMAIL': 'gmail',
        'ZENDESK': 'zendesk',
    },
    'ConversationStatus': {
        'NEW': 'new',
        'OPEN': 'open',
        'REPLIED': 'replied',
        'QUALIFIED': 'qualified',
        'ARCHIVED': 'archived',
    },
    'Priority': {
        'HIGH': 'high',
        'NORMAL': 'normal',
        'LOW': 'low',
    },
    'MessageDirection': {
        'IN': 'in_direction',
        'OUT': 'out',
    },
    'MessageType': {
        'TEXT': 'text',
        'IMAGE': 'image',
        'DOCUMENT': 'document',
        'AUDIO': 'audio',
        'VIDEO': 'video',
        'LOCATION': 'location',
    },
    'MessageStatus': {
        'PENDING': 'pending',
        'SENT': 'sent',
        'DELIVERED': 'delivered',
        'READ': 'read',
        'FAILED': 'failed',
    },
    'ChatChannelType': {
        'PUBLIC': 'public',
        'PRIVATE': 'private',
        'DIRECT': 'direct',
    },
    'MemberRole': {
        'ADMIN': 'admin',
        'MODERATOR': 'moderator',
        'MEMBER': 'member',
    },
    'NotificationLevel': {
        'ALL': 'all',
        'MENTIONS': 'mentions',
        'NONE': 'none',
    },
    'EntryType': {
        'MESSAGE': 'message',
        'JOIN': 'join',
        'LEAVE': 'leave',
        'SYSTEM': 'system',
    },
    'MentionType': {
        'USER': 'user',
        'EVERYONE': 'everyone',
        'HERE': 'here',
    },
    'CommunicationType': {
        'EMAIL': 'email',
        'SMS': 'sms',
        'WHATSAPP': 'whatsapp',
        'PUSH': 'push',
        'IN_APP': 'in_app',
    },
    'CommunicationStatus': {
        'PENDING': 'pending',
        'SENDING': 'sending',
        'SENT': 'sent',
        'DELIVERED': 'delivered',
        'READ': 'read',
        'FAILED': 'failed',
        'BOUNCED': 'bounced',
        'COMPLAINED': 'complained',
    },
    'TemplateType': {
        'WELCOME': 'welcome',
        'VERIFICATION': 'verification',
        'RESET_PASSWORD': 'reset_password',
        'BOOKING_CONFIRMATION': 'booking_confirmation',
        'BOOKING_REMINDER': 'booking_reminder',
        'PAYMENT_RECEIPT': 'payment_receipt',
        'PROMOTIONAL': 'promotional',
        'TRANSACTIONAL': 'transactional',
        'NOTIFICATION': 'notification',
    },
    'WebhookEvent': {
        'MESSAGE_RECEIVED': 'message_received',
        'MESSAGE_SENT': 'message_sent',
        'MESSAGE_DELIVERED': 'message_delivered',
        'MESSAGE_READ': 'message_read',
        'MESSAGE_FAILED': 'message_failed',
        'CONVERSATION_CREATED': 'conversation_created',
        'CONVERSATION_UPDATED': 'conversation_updated',
        'CONVERSATION_ARCHIVED': 'conversation_archived',
        'CHANNEL_CREATED': 'channel_created',
        'CHANNEL_UPDATED': 'channel_updated',
        'CHANNEL_DELETED': 'channel_deleted',
        'MEMBER_JOINED': 'member_joined',
        'MEMBER_LEFT': 'member_left',
        'ENTRY_CREATED': 'entry_created',
        'ENTRY_EDITED': 'entry_edited',
        'ENTRY_DELETED': 'entry_deleted',
    },

    # crm-service/core/enums.py
    'ActorType': {
        'LEAD': 'lead',
        'CONTACT': 'contact',
        'ACCOUNT_BUSINESS': 'account_business',
        'ACCOUNT_PERSON': 'account_person',
    },
    'TravelFrequency': {
        'OCCASIONAL': 'occasional',
        'FREQUENT': 'frequent',
        'BUSINESS_REGULAR': 'business_regular',
    },
    'Rating': {
        'ONE': 'one',
        'TWO': 'two',
        'THREE': 'three',
        'FOUR': 'four',
        'FIVE': 'five',
    },
    'LeadStatus': {
        'NEW': 'new',
        'CONTACTED': 'contacted',
        'QUALIFIED': 'qualified',
        'CONVERTED': 'converted',
        'DISQUALIFIED': 'disqualified',
    },
    'InterestLevel': {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
    },
    'ContactStatus': {
        'ACTIVE': 'active',
        'INACTIVE': 'inactive',
        'DO_NOT_CONTACT': 'do_not_contact',
    },
    'Gender': {
        'MALE': 'male',
        'FEMALE': 'female',
        'OTHER': 'other',
        'PREFER_NOT_TO_SAY': 'prefer_not_to_say',
    },
    'PreferredCommunication': {
        'EMAIL': 'email',
        'PHONE': 'phone',
        'SMS': 'sms',
        'WHATSAPP': 'whatsapp',
    },
    'AccountType': {
        'BUSINESS': 'business',
        'PERSON': 'person',
    },
    'AccountStatus': {
        'ACTIVE': 'active',
        'INACTIVE': 'inactive',
        'PROSPECT': 'prospect',
        'CUSTOMER': 'customer',
        'PARTNER': 'partner',
    },
    'PaymentMethod': {
        'CREDIT_CARD': 'credit_card',
        'BANK_TRANSFER': 'bank_transfer',
        'CHECK': 'check',
        'CASH': 'cash',
        'DEBIT_CARD': 'debit_card',
        'PAYPAL': 'paypal',
        'STRIPE': 'stripe',
        'WIRE_TRANSFER': 'wire_transfer',
        'OTHER': 'other',
    },
    'OpportunityStage': {
        'PROSPECTING': 'prospecting',
        'QUALIFICATION': 'qualification',
        'NEEDS_ANALYSIS': 'needs_analysis',
        'VALUE_PROPOSITION': 'value_proposition',
        'DECISION_MAKING': 'decision_making',
        'PERCEPTION_ANALYSIS': 'perception_analysis',
        'QUOTES': 'quotes',
        'NEGOTIATION': 'negotiation',
        'CLOSED_WON': 'closed_won',
        'CLOSED_LOST': 'closed_lost',
    },
    'TravelType': {
        'LEISURE': 'leisure',
        'BUSINESS': 'business',
        'CORPORATE': 'corporate',
        'HONEYMOON': 'honeymoon',
        'FAMILY': 'family',
        'ADVENTURE': 'adventure',
        'LUXURY': 'luxury',
        'CULTURAL': 'cultural',
        'EDUCATIONAL': 'educational',
        'MEDICAL': 'medical',
        'RELIGIOUS': 'religious',
        'BACKPACKING': 'backpacking',
        'VOLUNTEER': 'volunteer',
        'SPORTS': 'sports',
        'WELLNESS': 'wellness',
        'PERSONAL': 'personal',
        'ECOTOURISM': 'ecotourism',
        'OTHER': 'other',
    },
    'BudgetLevel': {
        'ECONOMY': 'economy',
        'STANDARD': 'standard',
        'PREMIUM': 'premium',
        'LUXURY': 'luxury',
    },
    'QuoteStatus': {
        'DRAFT': 'draft',
        'SENT': 'sent',
        'ACCEPTED': 'accepted',
        'REJECTED': 'rejected',
        'EXPIRED': 'expired',
        'CONVERTED': 'converted',
    },
    'Currency': {
        'USD': 'usd',
        'EUR': 'eur',
        'GBP': 'gbp',
        'JPY': 'jpy',
        'PEN': 'pen',
        'COP': 'cop',
        'ARS': 'ars',
        'CLP': 'clp',
        'MXN': 'mxn',
        'BOL': 'bol',
    },
    'QuoteLineType': {
        'FLIGHT': 'flight',
        'HOTEL': 'hotel',
        'TRANSFER': 'transfer',
        'TOUR': 'tour',
        'CRUISE': 'cruise',
        'INSURANCE': 'insurance',
        'VISA': 'visa',
        'OTHER': 'other',
        'PACKAGE': 'package',
        'ACTIVITY': 'activity',
        'CAR_RENTAL': 'car_rental',
        'TRAIN': 'train',
        'BUS': 'bus',
    },

    # financial-service/common/enums.py
    'OrderStatus': {
        'PENDING': 'pending',
        'CONFIRMED': 'confirmed',
        'IN_PROGRESS': 'in_progress',
        'COMPLETED': 'completed',
        'CANCELLED': 'cancelled',
        'REFUNDED': 'refunded',
    },
    'PaymentStatus': {
        'PENDING': 'pending',
        'PARTIAL': 'partial',
        'PAID': 'paid',
        'OVERDUE': 'overdue',
        'CANCELLED': 'cancelled',
        'REFUNDED': 'refunded',
    },
    'OrderLineType': {
        'FLIGHT': 'flight',
        'HOTEL': 'hotel',
        'TRANSFER': 'transfer',
        'TOUR': 'tour',
        'CRUISE': 'cruise',
        'INSURANCE': 'insurance',
        'VISA': 'visa',
        'OTHER': 'other',
        'PACKAGE': 'package',
        'ACTIVITY': 'activity',
        'CAR_RENTAL': 'car_rental',
        'TRAIN': 'train',
        'BUS': 'bus',
        'FEE': 'fee',
        'TAX': 'tax',
        'DISCOUNT': 'discount',
    },
    'InvoiceStatus': {
        'DRAFT': 'draft',
        'SENT': 'sent',
        'PARTIAL_PAID': 'partial_paid',
        'PAID': 'paid',
        'OVERDUE': 'overdue',
        'CANCELLED': 'cancelled',
    },
    'PaymentType': {
        'DEPOSIT': 'deposit',
        'PARTIAL': 'partial',
        'FULL': 'full',
        'REFUND': 'refund',
        'ADJUSTMENT': 'adjustment',
    },
    'TransactionType': {
        'PAYMENT': 'payment',
        'REFUND': 'refund',
        'CREDIT': 'credit',
        'DEBIT': 'debit',
        'ADJUSTMENT': 'adjustment',
    },
    'ExpenseStatus': {
        'PENDING': 'pending',
        'APPROVED': 'approved',
        'REJECTED': 'rejected',
        'PAID': 'paid',
        'REIMBURSED': 'reimbursed',
        'CANCELLED': 'cancelled',
    },
    'ExpenseType': {
        'TRAVEL': 'travel',
        'ACCOMMODATION': 'accommodation',
        'MEALS': 'meals',
        'TRANSPORTATION': 'transportation',
        'SUPPLIES': 'supplies',
        'UTILITIES': 'utilities',
        'MARKETING': 'marketing',
        'OFFICE': 'office',
        'ENTERTAINMENT': 'entertainment',
        'PROFESSIONAL_FEES': 'professional_fees',
        'INSURANCE': 'insurance',
        'TAXES': 'taxes',
        'OTHER': 'other',
    },
    'PettyCashTransactionType': {
        'DEPOSIT': 'deposit',
        'WITHDRAWAL': 'withdrawal',
        'EXPENSE': 'expense',
        'REIMBURSEMENT': 'reimbursement',
        'ADJUSTMENT': 'adjustment',
    },
    'PettyCashStatus': {
        'OPEN': 'open',
        'CLOSED': 'closed',
        'RECONCILED': 'reconciled',
    },
    'AccountsReceivableStatus': {
        'OPEN': 'open',
        'PARTIAL': 'partial',
        'PAID': 'paid',
        'OVERDUE': 'overdue',
        'WRITTEN_OFF': 'written_off',
    },
    'AccountsPayableStatus': {
        'OPEN': 'open',
        'PARTIAL': 'partial',
        'PAID': 'paid',
        'OVERDUE': 'overdue',
        'DISPUTED': 'disputed',
    },
    'AgingBucket': {
        'CURRENT': 'current',
        'DAYS_30': 'days_30',
        'DAYS_60': 'days_60',
        'DAYS_90': 'days_90',
        'DAYS_120_PLUS': 'days_120_plus',
    },
    'CollectionStatus': {
        'NORMAL': 'normal',
        'WARNING': 'warning',
        'COLLECTION': 'collection',
        'LEGAL': 'legal',
    },
    'VoucherStatus': {
        'DRAFT': 'draft',
        'PENDING': 'pending',
        'APPROVED': 'approved',
        'PAID': 'paid',
        'CANCELLED': 'cancelled',
    },
    'VoucherType': {
        'PAYMENT': 'payment',
        'RECEIPT': 'receipt',
        'JOURNAL': 'journal',
        'CONTRA': 'contra',
    },
    'PayeeType': {
        'EMPLOYEE': 'employee',
        'SUPPLIER': 'supplier',
        'CUSTOMER': 'customer',
        'OTHER': 'other',
    },

    # system-service/common/enums.py
    'UserStatus': {
        'ACTIVE': 'active',
        'INACTIVE': 'inactive',
        'SUSPENDED': 'suspended',
        'PENDING': 'pending',
    },
    'PermissionAction': {
        'CREATE': 'create',
        'READ': 'read',
        'UPDATE': 'update',
        'DELETE': 'delete',
        'EXECUTE': 'execute',
        'APPROVE': 'approve',
        'EXPORT': 'export',
        'IMPORT': 'import_action',
    },
    'ResourceType': {
        'USER': 'user',
        'ROLE': 'role',
        'PROJECT': 'project',
        'DOCUMENT': 'document',
        'REPORT': 'report',
        'SETTING': 'setting',
        'AUDIT': 'audit',
        'API': 'api',
        'WEBHOOK': 'webhook',
        'WORKFLOW': 'workflow',
    },
    'TaskStatus': {
        'PENDING': 'pending',
        'IN_PROGRESS': 'in_progress',
        'COMPLETED': 'completed',
        'CANCELLED': 'cancelled',
    },
    'TaskPriority': {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'URGENT': 'urgent',
    },
    'NotePriority': {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'URGENT': 'urgent',
    },
    'CallType': {
        'INCOMING': 'incoming',
        'OUTGOING': 'outgoing',
    },
    'CallStatus': {
        'ANSWERED': 'answered',
        'MISSED': 'missed',
        'BUSY': 'busy',
        'NO_ANSWER': 'no_answer',
        'FAILED': 'failed',
    },
    'DiskType': {
        'PUBLIC': 'public',
        'AWS': 'aws',
    },
    'EventStatus': {
        'SCHEDULED': 'scheduled',
        'COMPLETED': 'completed',
        'CANCELLED': 'cancelled',
        'POSTPONED': 'postponed',
    },
    'AssignmentRule': {
        'ROUND_ROBIN': 'round_robin',
        'LOAD_BALANCED': 'load_balanced',
        'MANUAL': 'manual',
        'BY_SKILL': 'by_skill',
    },

    # tenant-service/models.py
    'UserRole': {
        'SUPER_ADMIN': 'super_admin',
        'TENANT_ADMIN': 'tenant_admin',
    },
    'TenantStatus': {
        'ACTIVE': 'active',
        'SUSPENDED': 'suspended',
        'TRIAL': 'trial',
        'EXPIRED': 'expired',
        'PENDING': 'pending',
    },
}

def update_file(file_path: Path, replacements: List[Tuple[str, str]]) -> bool:
    """
    Update a single file with the given replacements

    Args:
        file_path: Path to the file to update
        replacements: List of (old, new) tuples to replace

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        for old_text, new_text in replacements:
            # Use word boundaries to ensure we're replacing exact matches
            pattern = r'\b' + re.escape(old_text) + r'\b'
            content = re.sub(pattern, new_text, content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def get_all_replacements() -> List[Tuple[str, str]]:
    """
    Generate all replacement tuples from the enum mappings

    Returns:
        List of (old, new) replacement tuples
    """
    replacements = []

    for enum_name, mappings in ENUM_MAPPINGS.items():
        for old_value, new_value in mappings.items():
            # Add the enum reference replacement (e.g., EnumName.OLD_VALUE -> EnumName.new_value)
            replacements.append((f"{enum_name}.{old_value}", f"{enum_name}.{new_value}"))

    return replacements

def find_python_files(root_dir: Path) -> List[Path]:
    """
    Find all Python files in the services directory

    Args:
        root_dir: Root directory to search

    Returns:
        List of Python file paths
    """
    return list(root_dir.glob("services/**/*.py"))

def main():
    """Main function to run the enum reference updates"""

    # Get the project root directory (assuming script is in travel_system/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print("Starting enum reference updates...")
    print(f"Project root: {project_root}")

    # Get all replacements
    replacements = get_all_replacements()
    print(f"Generated {len(replacements)} replacement patterns")

    # Find all Python files
    python_files = find_python_files(project_root)
    print(f"Found {len(python_files)} Python files to process")

    # Process each file
    modified_files = []
    for file_path in python_files:
        # Skip the enum definition files themselves
        if file_path.name == "enums.py" or "enum" in str(file_path):
            continue

        if update_file(file_path, replacements):
            modified_files.append(file_path)
            print(f"✓ Modified: {file_path.relative_to(project_root)}")

    print(f"\nUpdate complete!")
    print(f"Modified {len(modified_files)} files")

    if modified_files:
        print("\nModified files:")
        for file_path in modified_files:
            print(f"  - {file_path.relative_to(project_root)}")

if __name__ == "__main__":
    main()
