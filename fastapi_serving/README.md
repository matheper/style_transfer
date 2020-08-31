# Style Transfer

Artistic Style Transfer with Flutter, TensorFlow and FastAPI.


## Install

Create virtual env and install requirements.
```
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```


## Serving

Start FastAPI Server using uvicorn. Use --reload for development purpose.
```
uvicorn main:app --reload
```