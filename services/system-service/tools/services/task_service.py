"""
Task Service
Handles task operations with proper context management for multi-tenant architecture
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session
from contextlib import contextmanager

from database import get_db, get_tenant_session
from tools.models import Task
from tools.schemas import TaskCreate, TaskUpdate
from common.enums import TaskStatus, TaskPriority


class TaskService:
    """Service layer for task operations with proper context handling"""

    @staticmethod
    def validate_user_exists(tenant_slug: str, user_id: str) -> bool:
        """
        Validate that a user exists in the tenant context

        Args:
            tenant_slug: The tenant identifier
            user_id: UUID of the user to validate

        Returns:
            bool: True if user exists, False otherwise
        """
        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"
        with get_tenant_session(schema_name) as db:
            result = db.execute(
                text("SELECT EXISTS(SELECT 1 FROM users WHERE id = :user_id)"),
                {"user_id": user_id}
            )
            return result.scalar()

    @staticmethod
    def create_task(
        tenant_slug: str,
        task_data: TaskCreate,
        current_user_id: str
    ) -> Dict[str, Any]:
        """
        Create a task with proper context handling

        Args:
            tenant_slug: The tenant identifier
            task_data: Task creation data
            current_user_id: ID of the user creating the task

        Returns:
            Dict containing the created task data

        Raises:
            ValueError: If validation fails
        """
        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

        # Use a single session for all operations
        with get_tenant_session(schema_name) as db:
            # Step 1: Validate assigned user if provided
            if task_data.assigned_to:
                result = db.execute(
                    text("SELECT EXISTS(SELECT 1 FROM users WHERE id = :user_id)"),
                    {"user_id": str(task_data.assigned_to)}
                )
                if not result.scalar():
                    raise ValueError(f"Assigned user {task_data.assigned_to} not found")

            # Step 2: Validate creator exists
            if current_user_id:
                result = db.execute(
                    text("SELECT EXISTS(SELECT 1 FROM users WHERE id = :user_id)"),
                    {"user_id": current_user_id}
                )
                if not result.scalar():
                    raise ValueError(f"Creator user {current_user_id} not found")

            # Step 3: Insert task into tenant schema using raw SQL
            # Use raw SQL to insert without ORM foreign key validation
            query = text("""
                INSERT INTO tasks (
                    title, description, status, priority, due_date,
                    taskable_id, taskable_type, assigned_to, created_by,
                    created_at, updated_at
                ) VALUES (
                    :title, :description, :status, :priority, :due_date,
                    :taskable_id, :taskable_type, :assigned_to, :created_by,
                    :created_at, :updated_at
                ) RETURNING id, title, description, status, priority, due_date,
                          taskable_id, taskable_type, assigned_to, created_by,
                          created_at, updated_at
            """)

            # Prepare values
            now = datetime.utcnow()

            # Convert status and priority to uppercase for enum
            status_value = task_data.status
            if hasattr(status_value, 'value'):
                status_value = status_value.value
            status_value = str(status_value).upper()

            priority_value = task_data.priority
            if hasattr(priority_value, 'value'):
                priority_value = priority_value.value
            priority_value = str(priority_value).upper()

            params = {
                "title": task_data.title,
                "description": task_data.description,
                "status": status_value,
                "priority": priority_value,
                "due_date": task_data.due_date,
                "taskable_id": task_data.taskable_id,
                "taskable_type": task_data.taskable_type,
                "assigned_to": str(task_data.assigned_to) if task_data.assigned_to else None,
                "created_by": current_user_id,
                "created_at": now,
                "updated_at": now
            }

            result = db.execute(query, params)
            task_row = result.fetchone()
            db.commit()

            if task_row:
                return {
                    "id": task_row[0],
                    "title": task_row[1],
                    "description": task_row[2],
                    "status": task_row[3],
                    "priority": task_row[4],
                    "due_date": task_row[5],
                    "taskable_id": task_row[6],
                    "taskable_type": task_row[7],
                    "assigned_to": task_row[8],
                    "created_by": task_row[9],
                    "created_at": task_row[10],
                    "updated_at": task_row[11]
                }

            raise ValueError("Failed to create task")

    @staticmethod
    def get_task(tenant_slug: str, task_id: int) -> Optional[Task]:
        """
        Get a task by ID from tenant context

        Args:
            tenant_slug: The tenant identifier
            task_id: ID of the task

        Returns:
            Task object or None if not found
        """
        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

        with get_tenant_session(schema_name) as tenant_db:
            # We can safely use ORM for reading
            from sqlalchemy import and_
            task = tenant_db.query(Task).filter(
                and_(Task.id == task_id, Task.deleted_at.is_(None))
            ).first()

            if task:
                # Detach from session before returning
                tenant_db.expunge(task)

            return task

    @staticmethod
    def list_tasks(
        tenant_slug: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Task]:
        """
        List tasks with filtering from tenant context

        Args:
            tenant_slug: The tenant identifier
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply

        Returns:
            List of Task objects
        """
        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

        with get_tenant_session(schema_name) as tenant_db:
            query = tenant_db.query(Task).filter(Task.deleted_at.is_(None))

            # Apply filters if provided
            if filters:
                if filters.get('status'):
                    query = query.filter(Task.status == filters['status'])
                if filters.get('priority'):
                    query = query.filter(Task.priority == filters['priority'])
                if filters.get('assigned_to'):
                    query = query.filter(Task.assigned_to == filters['assigned_to'])
                if filters.get('created_by'):
                    query = query.filter(Task.created_by == filters['created_by'])
                if filters.get('due_before'):
                    query = query.filter(Task.due_date <= filters['due_before'])
                if filters.get('due_after'):
                    query = query.filter(Task.due_date >= filters['due_after'])

            # Order and paginate
            tasks = query.order_by(Task.priority.desc(), Task.due_date.asc())\
                        .offset(skip)\
                        .limit(limit)\
                        .all()

            # Detach from session before returning
            for task in tasks:
                tenant_db.expunge(task)

            return tasks

    @staticmethod
    def update_task(
        tenant_slug: str,
        task_id: int,
        task_data: TaskUpdate,
        current_user_id: str
    ) -> Optional[Task]:
        """
        Update a task

        Args:
            tenant_slug: The tenant identifier
            task_id: ID of the task to update
            task_data: Update data
            current_user_id: ID of the user updating the task

        Returns:
            Updated Task object or None if not found
        """
        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

        # Validate assigned user if changing assignment
        if task_data.assigned_to is not None:
            with get_tenant_session(schema_name) as db:
                result = db.execute(
                    text("SELECT EXISTS(SELECT 1 FROM users WHERE id = :user_id)"),
                    {"user_id": str(task_data.assigned_to)}
                )
                if not result.scalar():
                    raise ValueError(f"Assigned user {task_data.assigned_to} not found")

        with get_tenant_session(schema_name) as tenant_db:
            from sqlalchemy import and_

            task = tenant_db.query(Task).filter(
                and_(Task.id == task_id, Task.deleted_at.is_(None))
            ).first()

            if not task:
                return None

            # Update fields
            update_data = task_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)

            task.updated_at = datetime.utcnow()

            tenant_db.commit()
            tenant_db.refresh(task)

            # Detach from session before returning
            tenant_db.expunge(task)

            return task

    @staticmethod
    def delete_task(
        tenant_slug: str,
        task_id: int,
        current_user_id: str
    ) -> bool:
        """
        Soft delete a task

        Args:
            tenant_slug: The tenant identifier
            task_id: ID of the task to delete
            current_user_id: ID of the user deleting the task

        Returns:
            True if deleted, False if not found
        """
        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

        with get_tenant_session(schema_name) as tenant_db:
            from sqlalchemy import and_

            task = tenant_db.query(Task).filter(
                and_(Task.id == task_id, Task.deleted_at.is_(None))
            ).first()

            if not task:
                return False

            # Soft delete
            task.deleted_at = datetime.utcnow()

            tenant_db.commit()

            return True


# Create singleton instance
task_service = TaskService()
