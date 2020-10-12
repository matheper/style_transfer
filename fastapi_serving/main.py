import io

import uvicorn
from starlette.responses import StreamingResponse
from fastapi import FastAPI, File,  HTTPException

from style_transfer import apply_style

app = FastAPI()


@app.post('/style')
async def style(content_image: bytes = File(...),
                style_image: bytes = File(...),
                blending_ratio: float = 1):
    try:
        stylized_image = apply_style(
            io.BytesIO(content_image),
            io.BytesIO(style_image),
            blending_ratio,
        )
    except BaseException:
        raise HTTPException(status_code=500)

    return StreamingResponse(stylized_image, media_type="image/jpg")


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
