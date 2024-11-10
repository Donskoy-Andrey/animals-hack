from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


class Coordinate(BaseModel):
    x: int = Field(..., description="X координата левого верхнего угла", ge=0)
    y: int = Field(..., description="Y координата левого верхнего угла", ge=0)

    @field_validator('x', 'y')
    def validate_coordinates(cls, value, field):
        if value < 0:
            raise ValueError(f"{field.name} не может быть отрицательным")
        return value


class AnimalsBorder(BaseModel):
    animals_name: str = Field(..., description="Название животного", min_length=1)
    left_up_corner: Coordinate = Field(..., description="Координата левого верхнего угла границы животного")
    width: int = Field(..., description="Ширина границы", gt=0)
    height: int = Field(..., description="Высота границы", gt=0)

    @field_validator('width', 'height')
    def validate_dimensions(cls, value, field):
        if value <= 0:
            raise ValueError(f"{field.name} должно быть положительным числом")
        return value


class AnimalsImageRequest(BaseModel):
    filename: str = Field(..., description="Имя файла изображения", min_length=1)
    created_at: datetime = Field(..., description="Дата и время создания изображения")
    object_class: bool = Field(..., description="Класс объекта: True если хороший, иначе False")
    border: List[AnimalsBorder] = Field(..., description="Список границ животных на изображении")

    @field_validator('filename')
    def validate_filename(cls, value):
        allowed_extensions = ('.png', '.jpg', '.jpeg')
        if not value.lower().endswith(allowed_extensions):
            raise ValueError(f"Файл должен иметь одно из расширений: {', '.join(allowed_extensions)}")
        return value


class FileImageResponse(BaseModel):
    # file: UploadFile = File(...)
    created_at: int = Field(...)
    camera: str = Field(...)


class SizeThreshold(BaseModel):
    width: int = Field(default=128, gt=0)
    height: int = Field(default=128, gt=0)


class AnimalsImageResponse(BaseModel):
    count: int = Field(1, description="Количество изображений")
    # images: List[FileImageResponse]
    confidence_level: float = Field(default=0.95, description="Уровень уверенности предсказания")
    # size_threshold: str
    # size_threshold: str
    # width: int = Field(default=128, gt=0)
    # height: int = Field(default=128, gt=0)


class UidResponse(BaseModel):
    uid: str


class BodyData(TypedDict):
    filenames: list[str]
    datetimes: list[int]
    cameras: list[str]
    threshold_width: int
    threshold_height: int


class MessageBody(TypedDict):
    data: BodyData


class JobMessage(TypedDict):
    uid: str
    body: MessageBody


class ResultRequest(BaseModel):
    uid: str




class PdfRequestBody(BaseModel):
    uid: str
    confidence_level: float
