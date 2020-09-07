# https://www.tensorflow.org/lite/models/style_transfer/overview
import io

import tensorflow as tf
from PIL import Image


style_predict = 'tf_models/magenta_arbitrary-image-stylization-v1-256_int8_prediction_1.tflite'
style_transform = 'tf_models/magenta_arbitrary-image-stylization-v1-256_int8_transfer_1.tflite'


# Function to load an image from a img bytes, and add a batch dimension.
def load_img(img_bytes):
    img = tf.keras.preprocessing.image.img_to_array(
        Image.open(io.BytesIO(img_bytes))
    )
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = img[tf.newaxis, :]
    return img


# Function to load an image to a BytesIO buffer.
def buffer_img(img):
    buffer = io.BytesIO()
    img.save(buffer, format='jpeg')
    buffer.seek(0)
    return buffer


def save_img(img):
    tf.keras.preprocessing.image.save_img('stylized_image.jpg', img)
    # img = tf.keras.preprocessing.image.array_to_img(img)
    # img.save('stylized_image.jpg')


# Function to pre-process by resizing an central cropping it.
def preprocess_img(img, target_dim):
    # Resize the image so that the shorter dimension becomes 256px.
    shape = tf.cast(tf.shape(img)[1:-1], tf.float32)
    short_dim = min(shape)
    scale = target_dim / short_dim
    new_shape = tf.cast(shape * scale, tf.int32)
    img = tf.image.resize(img, new_shape)

    # Central crop the image.
    img = tf.image.resize_with_crop_or_pad(img, target_dim, target_dim)
    img = img / 255  # float32 numbers between [0..1]
    return img


def postprocess_img(img):
    if len(img.shape) > 3:
        img = tf.squeeze(img, axis=0)
    img = img * 255
    img = tf.keras.preprocessing.image.array_to_img(img)
    return img


# Function to run style prediction on preprocessed style image.
def run_style_predict(style_img):
    # Load the model.
    interpreter = tf.lite.Interpreter(model_path=style_predict)

    # Set model input.
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    interpreter.set_tensor(input_details[0]["index"], style_img)

    # Calculate style bottleneck.
    interpreter.invoke()
    output_details = interpreter.get_output_details()
    style_bottleneck = interpreter.tensor(output_details[0]["index"])()

    return style_bottleneck


# Run style transform on preprocessed style image
def run_style_transform(style_bottleneck, content_img):
    # Load the model.
    interpreter = tf.lite.Interpreter(model_path=style_transform)

    # Set model input.
    input_details = interpreter.get_input_details()
    interpreter.allocate_tensors()

    # Set model inputs.
    interpreter.set_tensor(input_details[0]["index"], content_img)
    interpreter.set_tensor(input_details[1]["index"], style_bottleneck)
    interpreter.invoke()

    # Transform content image.
    output_details = interpreter.get_output_details()
    stylized_image = interpreter.tensor(output_details[0]["index"])()

    return stylized_image
