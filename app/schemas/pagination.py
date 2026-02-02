
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class PaginatedResponse(GenericModel, Generic[T]):
    data: List[T]
    total: int
    last_page: int
    page: int
    per_page: int
