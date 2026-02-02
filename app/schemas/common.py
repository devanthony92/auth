from typing import List, TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Esquema para respuestas paginadas
    """
    items: List[T]
    total: int
    page: int
    per_page: int
    size: int
    pages: int
    last_page: int
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    """
    Esquema para respuestas de mensajes simples
    """
    message: str
    
class ErrorResponse(BaseModel):
    """
    Esquema para respuestas de error
    """
    detail: str
    error_code: Optional[str] = None

