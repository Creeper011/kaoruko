from dataclasses import dataclass
from typing import Union
from src.domain.exceptions.base_exception import ApplicationBaseException

@dataclass(frozen=True)
class Result():
    """Indicates the result of a process, can be okay or failture"""
    ok: bool
    message: str | None = None
    exception: Union[Exception, 'ApplicationBaseException'] | None = None