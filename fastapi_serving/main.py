import uvicorn
from fastapi import FastAPI, File

from transfer_style import (
    load_img,
    save_img,
    preprocess_img,
    run_style_predict,
    run_style_transform,
    postprocess_img,
)

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post('/style')
async def style(content_img: bytes = File(...), style_img: bytes = File(...)):
    content_img = preprocess_img(load_img(content_img), 384)
    style_img = preprocess_img(load_img(style_img), 256)

    # Calculate style bottleneck for the preprocessed style image.
    style_bottleneck = run_style_predict(style_img)

    # Stylize the content image using the style bottleneck.
    stylized_image = run_style_transform(style_bottleneck, content_img)
    stylized_image = postprocess_img(stylized_image)
    save_img(stylized_image)
    return {'image': len(stylized_image)}


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
