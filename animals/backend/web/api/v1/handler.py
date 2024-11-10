# Основные API
import contextlib
import json
import os
from typing import Any
from uuid import uuid4

import msgpack
import pandas as pd
from aio_pika import Message
from aio_pika.abc import DeliveryMode, ExchangeType
from fastapi import Depends, UploadFile, Form, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import JSONResponse, FileResponse
from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError

from consumer.handlers.utils.reports import ImageReportPDF
from web.config.settings import settings
from web.logger import logger
from web.storage.db import get_db
from web.storage.rabbit import channel_pool
from .router import router
from .schemas import *
from .schemas import JobMessage
from .utils import get_stats
from ...models.jobs import Jobs
from ...models.jobs_images import JobsImages

TIME_FORMAT: str = '%Y-%m-%dT%H:%M:%S'
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/gif"]
DIRECTORY = "/data/raw"


# api на загрузку файла

@router.post("/upload_images",
             responses={
                 400: {"description": "Неверный запрос"},
                 500: {"description": "Ошибка сервера"}
             },
             tags=["API для загрузки фото животных видео на Фронтенд-Сервере"],
             summary="Загрузить несколько изображений животных")
async def upload_images(body: AnimalsImageResponse = Depends(),
                        images: List[UploadFile] = File(...),
                        created_at: List[str] = Form(...),
                        camera: List[str] = Form(...),
                        size_threshold: str = Form(...),
                        session: AsyncSession = Depends(get_db)):
    # добавляем запись о задаче
    current_id = str(uuid4())
    db_job = Jobs(uid=current_id)
    session.add(db_job)
    await session.commit()
    size_threshold = json.loads(size_threshold)
    logger.info(f"{size_threshold=}")
    os.makedirs(DIRECTORY, exist_ok=True)

    uploaded_files_name = []
    created_at_time = []
    valid_camera = []
    # скачиваем файл
    image_info = zip(images, camera, created_at)
    for index, (file, camera, created_at) in enumerate(image_info):
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(f"Недопустимый тип файла: {file.filename} ({file.content_type})")
        try:
            if '/' in file.filename:
                file.filename = str(file.filename).split('/')[-1]

            logger.info(f"{file.filename=}")
            path = os.path.join(DIRECTORY, f"{current_id}_hash_{file.filename}")
            # Асинхронно считываем содержимое файла
            with open(path, "wb+") as file_object:
                file_object.write(file.file.read())
            uploaded_files_name.append(f"{current_id}_hash_{file.filename}")
            created_at_time.append(created_at)
            valid_camera.append(camera)
        except Exception as e:
            logger.error(f"Ошибка при чтении и сохранении файла {current_id}_hash_{file.filename}: {e}")
            continue
    # собираем всю информацию
    msg: JobMessage = {
        "uid": current_id,
        "body":
            {"data":
                {
                    "filenames": uploaded_files_name,
                    "datetimes": created_at_time,
                    "cameras": valid_camera,
                    "threshold_width": size_threshold['width'],
                    "threshold_height": size_threshold['height']
                }

            }
    }
    # отправляем в очередь
    await publish_message(msg)

    return JSONResponse({"uid": current_id}, status_code=200)

# API на получение результата работы задачи с номером uid
@router.post("/get_result")
async def get_result(body: UidResponse, session: AsyncSession = Depends(get_db), ):
    uid = body.uid
    logger.info(f"uid: {uid}")
    # собираем данные о соответствиях
    jobs_images = (await session.scalars(
        select(JobsImages).
        where(JobsImages.job_id == uid).
        options(joinedload(JobsImages.image))
    )).all()
    logger.info(jobs_images)
    if len(jobs_images) == 0:
        return JSONResponse({}, status_code=200)
    # проверяем готовность задачи
    for job in jobs_images:
        if not job.status:
            return JSONResponse({}, status_code=200)

    # формируем ответ
    def form_payload_borders(current_job):
        payload_borders = []
        job_idx = hash(current_job.image.image_path)
        job_borders = current_job.image.border
        job_object_cls = current_job.image.object_class
        for i in range(len(job_borders)):
            current_border = {}
            current_border["id"] = job_idx
            current_border["object_class"] = job_object_cls[i]
            current_border["left_up_corner"] = {"x": job_borders[i][0], "y": job_borders[i][1]}
            current_border["width"] = job_borders[i][2]
            current_border["height"] = job_borders[i][3]
            payload_borders.append(current_border)

        return payload_borders

    result = {
        "error_message": "",
        "images": [{"filename": str(job.image.image_path).split("/")[-1].split("_hash_")[-1],
                    "created_at": f"{job.image.datetime}", "camera": job.image.camera,
                    "border": form_payload_borders(job)

                    } for job in jobs_images],
        "stats": get_stats(jobs_images)
    }

    return JSONResponse(result)

# API получения отчета в формате пдф
@router.post('/get_result_report')
async def get_result(body: PdfRequestBody, session: AsyncSession = Depends(get_db), ):
    uid = body.uid
    conf_lvl = body.confidence_level

    # селект по uid задачи
    jobs_images = (await session.scalars(
        select(JobsImages).
        where(JobsImages.job_id == uid, JobsImages.status == True).
        options(joinedload(JobsImages.image))
    )).all()

    # функции приведения к нужному формату данных для формирования пдф
    def reformat_bbox(bbox: list[int]):
        res = ""
        for i, cord in enumerate(bbox):
            if i == len(bbox) - 1:
                res += str(int(cord))
            else:
                res += str(int(cord)) + ","
        return res

    def convert_class_obj(class_obg: int):
        if class_obg >= conf_lvl:
            return 1
        else:
            return 0

    filenames = [str(job.image.image_path).split("/")[-1].split("_hash_")[-1] for job in jobs_images]
    borders = [job.image.border for job in jobs_images]
    obj_class = [job.image.object_class for job in jobs_images]
    logger.info(borders)

    # приводим данные к df
    data = pd.DataFrame({
        "Name": [],
        "Bbox": [],
        "Class": [],
    })
    for i, filename in enumerate(filenames):
        for k, border in enumerate(borders[i]):
            data = pd.concat([data, pd.DataFrame({
                "Name": filenames[i],
                "Bbox": reformat_bbox(border),
                "Class": convert_class_obj(obj_class[i][k]),
            }, index=[i+k])], ignore_index=True)

    logger.info(data)

    # создаем пдф
    pdf = ImageReportPDF(f"/data/{uid}_report.pdf", data)
    pdf_file = pdf.generate()

    # возвращаем на фронт в виде файлоа
    return FileResponse(f"/data/{uid}_report.pdf")

# отправка сообщений в очередь
async def publish_message(body: dict[str, Any]) -> None:
    logger.info("Sending message: %s", body)
    async with channel_pool.acquire() as channel:  # type: Channel
        exchange = await channel.declare_exchange(
            settings.EXCHANGE,
            type=ExchangeType.TOPIC,
            durable=True,
        )

        message_info = {
            "body": msgpack.packb(body),
            "delivery_mode": DeliveryMode.PERSISTENT,
        }

        with contextlib.suppress(ContextDoesNotExistError):
            if correlation_id := context.get("X-Correlation-ID"):
                message_info["correlation_id"] = correlation_id

        await exchange.publish(
            Message(**message_info),
            routing_key=settings.QUEUE,
        )
