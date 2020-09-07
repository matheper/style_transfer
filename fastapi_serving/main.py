import uvicorn
from starlette.responses import StreamingResponse
from fastapi import FastAPI, File

from transfer_style import (
    load_img,
    save_img,
    preprocess_img,
    run_style_predict,
    run_style_transform,
    postprocess_img,
    buffer_img,
)

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post('/style')
async def style(content_image: bytes = File(...),
                style_image: bytes = File(...),
                blending_ratio: float = 1):
    content_img = load_img(content_image)
    style_img = load_img(style_image)

    # Calculate style bottleneck for the preprocessed style image.
    style_bottleneck = run_style_predict(preprocess_img(style_img, 256))

    style_bottleneck_content = run_style_predict(
        preprocess_img(content_img, 256))

    style_bottleneck = (
        (1 - blending_ratio) * style_bottleneck_content +
        blending_ratio * style_bottleneck
    )

    # Stylize the content image using the style bottleneck.
    stylized_image = run_style_transform(
        style_bottleneck, preprocess_img(content_img, 384))
    stylized_image = postprocess_img(stylized_image)
    # save_img(stylized_image)

    return StreamingResponse(
        buffer_img(stylized_image),
        media_type="image/jpg",
    )


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
