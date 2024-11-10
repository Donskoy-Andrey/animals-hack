import matplotlib.pyplot as plt
import tritonclient.grpc as grpcclient
# from animals.backend.config import DATA_PATH
from ultralytics import YOLO

url = "http://triton:8002/detector"
model_name = "detector"
client = grpcclient.InferenceServerClient(url=url)
CONF_THRESHOLD = 0.4
IOU_THRESHOLD = 0.5
MODEL = YOLO(url, task="detect")
import numpy as np
# from web.logger import logger


# async def call_triton(image_path: str = f"{DATA_PATH}/train_data_minprirodi/images/1011727.jpg") -> list[dict]:
def call_triton(image_path: str = f"./cat.jpg") -> list[dict]:
    # logger.info(f"call_triton {image_path=}")
    image: np.ndarray = plt.imread(image_path)  # (h, w, c)
    if image.ndim == 3:
        if image.shape[2] > 3:
            # Удаление лишних каналов (например, альфа-канала)
            image_rgb = image[:, :, :3]
        else:
            image_rgb = image
    elif image.ndim == 2:
        # Изображение в градациях серого преобразовано в 3-канальное RGB."
        image_rgb = np.stack((image,) * 3, axis=-1)
    else:
        raise ValueError("Неизвестный формат изображения.")

    images = MODEL(image_rgb)
    output = []
    for image in images:
        for box in image.boxes:
            output.append({
                "xyxy": box.xyxy.flatten().tolist(),
                "conf": float(box.conf),
                "cls": int(box.cls),
            })

    return output
