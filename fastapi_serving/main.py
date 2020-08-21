import io

import tensorflow as tf
from PIL import Image
from fastapi import FastAPI, File


app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post('/style')
async def predict(img_bytes: bytes = File(...)):
    img = tf.keras.preprocessing.image.img_to_array(
        Image.open(io.BytesIO(img_bytes))
    )
    return {'size': len(img)}
