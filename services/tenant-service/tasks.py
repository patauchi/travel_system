from celery import Celery
from celery.utils.log import get_task_logger
import os
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure Celery
celery_app = Celery(
    'tenant_service',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Get logger
logger = get_task_logger(__name__)

# Redis client for caching
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

@celery_app.task(bind=True, max_retries=3)
def provision_tenant_resources(self, tenant_id: str, schema_name: str) -> Dict[str, Any]:
    """
    Provision resources for a new tenant
    """
    try:
        logger.info(f"Starting provisioning for tenant {tenant_id}")

        # Step 1: Initialize tenant directories in storage
        storage_path = f"/app/storage/tenants/{tenant_id}"
        directories = ['documents', 'uploads', 'exports', 'backups']

        for directory in directories:
            dir_path = f"{storage_path}/{directory}"
            # In production, this would create S3 buckets or cloud storage
            logger.info(f"Creating directory: {dir_path}")

        # Step 2: Set up default data in tenant schema
        logger.info(f"Setting up default data for schema {schema_name}")

        # Step 3: Configure tenant-specific services
        services_config = {
            'email_quota': 1000,
            'api_rate_limit': 10000,
            'storage_quota_gb': 10,
            'backup_enabled': 'true',  # Convert boolean to string
            'backup_frequency': 'daily'
        }

        # Store configuration in Redis (convert all values to strings)
        redis_config = {k: str(v) for k, v in services_config.items()}
        redis_client.hset(
            f"tenant_config:{tenant_id}",
            mapping=redis_config
        )

        # Step 4: Send welcome email (mock)
        logger.info(f"Sending welcome email for tenant {tenant_id}")

        # Step 5: Schedule initial backup
        schedule_tenant_backup.apply_async(
            args=[tenant_id, schema_name],
            eta=datetime.utcnow() + timedelta(hours=24)
        )

        # Step 6: Update provisioning status
        redis_client.setex(
            f"tenant_provision_status:{tenant_id}",
            3600,
            json.dumps({
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat()
            })
        )

        logger.info(f"Successfully provisioned resources for tenant {tenant_id}")
        return {
            'tenant_id': tenant_id,
            'status': 'success',
            'provisioned_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error provisioning tenant {tenant_id}: {str(e)}")

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying provisioning for tenant {tenant_id}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        # Update status to failed
        redis_client.setex(
            f"tenant_provision_status:{tenant_id}",
            3600,
            json.dumps({
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        )

        raise

@celery_app.task(bind=True, max_retries=3)
def cleanup_tenant_resources(self, tenant_id: str) -> Dict[str, Any]:
    """
    Clean up resources when a tenant is deleted
    """
    try:
        logger.info(f"Starting cleanup for tenant {tenant_id}")

        # Step 1: Backup data before deletion
        backup_path = f"/app/storage/archive/{tenant_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating final backup at {backup_path}")

        # Step 2: Remove storage directories
        storage_path = f"/app/storage/tenants/{tenant_id}"
        logger.info(f"Removing storage at {storage_path}")

        # Step 3: Clear Redis cache
        cache_keys = [
            f"tenant_config:{tenant_id}",
            f"tenant:{tenant_id}:*",
            f"api_calls:{tenant_id}:*",
            f"feature:{tenant_id}:*"
        ]

        for pattern in cache_keys:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys for pattern {pattern}")

        # Step 4: Cancel scheduled tasks
        logger.info(f"Canceling scheduled tasks for tenant {tenant_id}")

        # Step 5: Send notification email
        logger.info(f"Sending deletion confirmation for tenant {tenant_id}")

        logger.info(f"Successfully cleaned up resources for tenant {tenant_id}")
        return {
            'tenant_id': tenant_id,
            'status': 'success',
            'cleaned_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error cleaning up tenant {tenant_id}: {str(e)}")

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying cleanup for tenant {tenant_id}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        raise

@celery_app.task
def schedule_tenant_backup(tenant_id: str, schema_name: str) -> Dict[str, Any]:
    """
    Perform scheduled backup of tenant data
    """
    try:
        logger.info(f"Starting backup for tenant {tenant_id}")

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_path = f"/app/storage/backups/{tenant_id}/{timestamp}.sql"

        # In production, this would use pg_dump or similar
        logger.info(f"Creating backup at {backup_path}")

        # Update last backup timestamp
        redis_client.hset(
            f"tenant_config:{tenant_id}",
            "last_backup",
            datetime.utcnow().isoformat()
        )

        # Schedule next backup
        schedule_tenant_backup.apply_async(
            args=[tenant_id, schema_name],
            eta=datetime.utcnow() + timedelta(days=1)
        )

        return {
            'tenant_id': tenant_id,
            'backup_path': backup_path,
            'timestamp': timestamp
        }

    except Exception as e:
        logger.error(f"Error backing up tenant {tenant_id}: {str(e)}")
        raise

@celery_app.task
def send_tenant_email(
    tenant_id: str,
    recipient: str,
    subject: str,
    body: str,
    template: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email to tenant users
    """
    try:
        logger.info(f"Sending email to {recipient} for tenant {tenant_id}")

        if os.getenv("EMAIL_ENABLED", "false").lower() != "true":
            logger.info("Email sending is disabled, skipping")
            return {
                'status': 'skipped',
                'reason': 'Email disabled in configuration'
            }

        # Get SMTP configuration
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("EMAIL_FROM_ADDRESS", "noreply@multitenant.com")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = recipient
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(body, 'html' if template else 'plain'))

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Successfully sent email to {recipient}")
        return {
            'status': 'sent',
            'recipient': recipient,
            'subject': subject
        }

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise

@celery_app.task
def update_tenant_usage_metrics(tenant_id: str) -> Dict[str, Any]:
    """
    Update usage metrics for a tenant
    """
    try:
        logger.info(f"Updating usage metrics for tenant {tenant_id}")

        # Calculate storage usage (mock)
        storage_used_gb = 2.5  # This would be calculated from actual storage

        # Get API calls for today
        today = datetime.utcnow().date()
        api_calls_key = f"api_calls:{tenant_id}:{today}"
        api_calls = int(redis_client.get(api_calls_key) or 0)

        # Get active users count (mock)
        active_users = 10  # This would query the database

        # Update metrics in Redis
        metrics = {
            'storage_used_gb': storage_used_gb,
            'api_calls_today': api_calls,
            'active_users': active_users,
            'updated_at': datetime.utcnow().isoformat()
        }

        redis_client.hset(
            f"tenant_metrics:{tenant_id}",
            mapping={k: json.dumps(v) if not isinstance(v, str) else v
                    for k, v in metrics.items()}
        )

        logger.info(f"Updated metrics for tenant {tenant_id}: {metrics}")
        return metrics

    except Exception as e:
        logger.error(f"Error updating metrics for tenant {tenant_id}: {str(e)}")
        raise

@celery_app.task
def check_tenant_limits(tenant_id: str) -> Dict[str, Any]:
    """
    Check if tenant is approaching or exceeding limits
    """
    try:
        logger.info(f"Checking limits for tenant {tenant_id}")

        # Get tenant configuration
        config = redis_client.hgetall(f"tenant_config:{tenant_id}")
        metrics = redis_client.hgetall(f"tenant_metrics:{tenant_id}")

        warnings = []

        # Check storage limit
        storage_limit = float(config.get('storage_quota_gb', 10))
        storage_used = float(metrics.get('storage_used_gb', 0))

        if storage_used > storage_limit * 0.9:
            warnings.append({
                'type': 'storage',
                'message': f'Storage usage at {storage_used:.1f}GB of {storage_limit}GB',
                'severity': 'high' if storage_used >= storage_limit else 'medium'
            })

        # Check API rate limit
        api_limit = int(config.get('api_rate_limit', 10000))
        api_calls = int(metrics.get('api_calls_today', 0))

        if api_calls > api_limit * 0.8:
            warnings.append({
                'type': 'api_calls',
                'message': f'API calls at {api_calls} of {api_limit}',
                'severity': 'high' if api_calls >= api_limit else 'medium'
            })

        # Send notifications if there are warnings
        if warnings:
            logger.warning(f"Tenant {tenant_id} has limit warnings: {warnings}")

            # Store warnings in Redis
            redis_client.setex(
                f"tenant_warnings:{tenant_id}",
                3600,
                json.dumps(warnings)
            )

            # Send notification email (in production)
            if any(w['severity'] == 'high' for w in warnings):
                logger.info(f"Sending limit warning email for tenant {tenant_id}")

        return {
            'tenant_id': tenant_id,
            'warnings': warnings,
            'checked_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking limits for tenant {tenant_id}: {str(e)}")
        raise

@celery_app.task
def expire_trial_tenants() -> Dict[str, Any]:
    """
    Check and expire trial tenants that have passed their trial period
    """
    try:
        logger.info("Checking for expired trial tenants")

        # This would query the database for trial tenants
        # For now, return mock result
        expired_count = 0

        logger.info(f"Expired {expired_count} trial tenants")
        return {
            'expired_count': expired_count,
            'checked_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error expiring trial tenants: {str(e)}")
        raise

# Celery Beat Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'expire-trial-tenants': {
        'task': 'tasks.expire_trial_tenants',
        'schedule': timedelta(hours=6),  # Run every 6 hours
    },
    'update-all-tenant-metrics': {
        'task': 'tasks.update_all_tenant_metrics',
        'schedule': timedelta(hours=1),  # Run every hour
    },
}
