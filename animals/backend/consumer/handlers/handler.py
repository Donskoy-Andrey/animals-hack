import os.path

from sqlalchemy import insert, update

from consumer.handlers.utils import call_triton
from web.api.v1.schemas import JobMessage
from web.logger import logger
from web.models.images import Images
from web.models.jobs_images import JobsImages
from web.storage.db import async_session


async def process_images(message: JobMessage) -> None:
    image_pathes = message["body"]["data"]["filenames"]
    datetimes = message["body"]["data"]["datetimes"]
    cameras = message["body"]["data"]["cameras"]
    threshold_width = message["body"]["data"]["threshold_width"]
    threshold_height = message["body"]["data"]["threshold_height"]
    logger.info(f"{threshold_width=}")
    logger.info(f"{threshold_height=}")
    image_ids = []

    async with async_session() as session:
        image_ids = (await session.scalars(
            insert(Images).
            values([
                {"datetime": datetime_, "image_path": image_path, "camera": camera_}
                for image_path, datetime_, camera_ in zip(image_pathes, datetimes, cameras)
            ]).
            returning(Images.id)
        )).all()

        await session.commit()

        await session.execute(insert(JobsImages).values([
            {"job_id": message["uid"], "image_id": image_id, "status": False}
            for image_id in image_ids
        ]))

        await session.commit()

        #######################
        # do smth with pictures here
        #######################
        logger.info(f"0000")

        for index, image_id in enumerate(image_ids):

            await session.execute(
                update(JobsImages).
                where(JobsImages.job_id == message["uid"], JobsImages.image_id == image_id).
                values(status=True)
            )

            logger.info(f"11111111")

            orders = call_triton(os.path.join('/data/raw', image_pathes[index]))
            logger.info(f"{orders=}")
            for order in orders:
                logger.info(f"{order=}")
                left, top, right, bottom = order["xyxy"]
                order["xyxy"] = [left, top, right - left, bottom - top]
                logger.info(f'{order["xyxy"]}, {order["conf"]}')

            res_borders = []
            res_cls = []
            for order in orders:
                logger.info(f" второй цикла {order=}")
                logger.info(f" второй цикла {threshold_width=}")
                logger.info(f" второй цикла {threshold_height=}")
                if float(order["xyxy"][2]) >= float(threshold_width) and float(order["xyxy"][3]) >= float(
                        threshold_height):

                    logger.info(f" Условие выполнено {order=}")
                    res_borders.append(order["xyxy"])
                    res_cls.append(order["conf"])

            # res_borders = [order["xyxy"] for order in orders]
            # res_cls = [order["conf"] for order in orders]

            # res = [
            #         {"border": order["xyxy"], "object_class": order["conf"]}
            #         {"border": [100, 200, 300, 100], "object_class": 0}
            # for order in orders
            # ]
            logger.info("Пишем в базу")
            await session.execute(
                update(Images).
                where(Images.id == image_id).
                values(border=res_borders, object_class=res_cls)
            )
            await session.commit()

            # logger.info(f"{image_pathes=}")
            # logger.info(f"{image_pathes[index]=}")
            # orders = await asyncio.to_thread(call_triton, image_pathes[index])

            # await session.execute(
            #     update(Images).
            #     where(Images.id == image_id).
            #     # values(border=, object_class=orders['cls'])
            #     values([
            #         # {"border": order["xyxy"], "object_class": order["conf"]}
            #         {"border": [100, 200, 300, 100], "object_class": 0}
            #         # for order in orders
            #     ])
            #
            # )

            # session.commit()
        # await session.execute(
        #     update(Images).
        #     where(Images.id == example_id).
        #     values(border=[1, 2, 3, 4], object_class=1)
        # )
        # await session.commit()
        # job_row = await session.execute(select(Jobs).filter_by(uid=message["uid"]))
        # job = job_row.scalar_one()
        # session.refresh(job)
        #
        # await session.commit()
        #
        # row_check_obj = await session.execute(select(Jobs.is_processed).where(Jobs.uid == message["uid"]))
        # row_check = row_check_obj.scalar_one()
        # session.refresh(row_check)

        # logger.info(f"Finish work with queued job; Processed: {row_check}")
