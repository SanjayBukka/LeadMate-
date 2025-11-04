"""
Validation Utilities
Common validation functions for API requests
"""
import re
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status
from bson import ObjectId


def validate_object_id(id_str: str, field_name: str = "ID") -> ObjectId:
    """
    Validate and convert string to ObjectId
    
    Args:
        id_str: String to validate
        field_name: Name of field for error messages
    
    Returns:
        ObjectId if valid
    
    Raises:
        HTTPException if invalid
    """
    if not id_str or not isinstance(id_str, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required and must be a string"
        )
    
    if not ObjectId.is_valid(id_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )
    
    return ObjectId(id_str)


def validate_project_id(project_id: str) -> ObjectId:
    """Validate project ID"""
    return validate_object_id(project_id, "Project ID")


def validate_startup_id(startup_id: str) -> ObjectId:
    """Validate startup ID"""
    return validate_object_id(startup_id, "Startup ID")


def validate_file_size(file_size: int, max_size_mb: int = 50) -> None:
    """
    Validate file size
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB
    
    Raises:
        HTTPException if file too large
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {max_size_mb}MB"
        )


def validate_file_extension(filename: str, allowed_extensions: Optional[list] = None) -> None:
    """
    Validate file extension
    
    Args:
        filename: Name of file
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.docx'])
                          If None, uses default allowed extensions
    
    Raises:
        HTTPException if extension not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.docx', '.txt', '.doc']
    
    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple:
    """
    Validate password strength
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and special characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Remove special characters except dots, dashes, underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = Path(filename).stem[:240], Path(filename).suffix
        filename = name + ext
    
    return filename


def validate_project_title(title: str) -> None:
    """
    Validate project title
    
    Args:
        title: Project title
    
    Raises:
        HTTPException if invalid
    """
    if not title or not isinstance(title, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project title is required"
        )
    
    title = title.strip()
    
    if len(title) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project title must be at least 2 characters"
        )
    
    if len(title) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project title must be less than 200 characters"
        )


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size
    
    Returns:
        Tuple of (normalized_page, normalized_page_size)
    
    Raises:
        HTTPException if invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be greater than 0"
        )
    
    if page_size > max_page_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size cannot exceed {max_page_size}"
        )
    
    return page, page_size

