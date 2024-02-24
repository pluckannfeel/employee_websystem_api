from typing import List
from pydantic import BaseModel, EmailStr
from typing import List


class FilesToDelete(BaseModel):
    files: List[str]


class FilesToDownload(BaseModel):
    files: List[str]
