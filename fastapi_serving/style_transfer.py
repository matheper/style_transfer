# https://www.tensorflow.org/lite/models/style_transfer/overview
import io

import tensorflow as tf
from PIL import Image


style_predict = 'tf_models/magenta_arbitrary-image-stylization-v1-256_int8_prediction_1.tflite'
style_transform = 'tf_models/magenta_arbitrary-image-stylization-v1-256_int8_transfer_1.tflite'


def img_bytes_to_array(img_bytes: io.BytesIO) -> tf.Tensor:
    """Loads an image from a img bytes into a tf tensor.
    Rescales RGB [0..255] to [0..1] and adds batch dimension.
    """
    img = tf.keras.preprocessing.image.img_to_array(
        Image.open(img_bytes)
    )
    img = img / 255  # convert [0..255] to float32 between [0..1]
    img = img[tf.newaxis, :]  # add batch dimension
    return img


def array_to_img_bytes(img_array: tf.Tensor) -> io.BytesIO:
    """Loads a tf tensor image into a img bytes.
    Rescales [0..1] to RGB [0..255] and removes batch dimension.
    """
    if len(img_array.shape) > 3:  # remove batch dimension
        img_array = tf.squeeze(img_array, axis=0)
    img_array = img_array * 255  # convert [0..1] back to [0..255]
    img = tf.keras.preprocessing.image.array_to_img(img_array)
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='jpeg')
    img_buffer.seek(0)
    return img_buffer


def preprocess(img_tensor: tf.Tensor, target_dim: int) -> tf.Tensor:
    """Pre-process by resizing an central cropping it."""
    # Resize the image so the shorter dimension becomes target_dim.
    shape = tf.cast(tf.shape(img_tensor)[1:-1], tf.float32)
    short_dim = min(shape)
    scale = target_dim / short_dim
    new_shape = tf.cast(shape * scale, tf.int32)
    img = tf.image.resize(img_tensor, new_shape)

    # Central crop the image so both dimensions become target_dim.
    img = tf.image.resize_with_crop_or_pad(img, target_dim, target_dim)
    return img


def run_style_predict(style_img: tf.Tensor) -> tf.Tensor:
    """Runs style prediction on preprocessed style image."""
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


def run_style_transform(style_bottleneck: tf.Tensor,
                        content_img: tf.Tensor) -> tf.Tensor:
    """Runs style transform on preprocessed style image."""
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


def apply_style(content_image: io.BytesIO,
                style_image: io.BytesIO,
                blending_ratio: float = 1) -> io.BytesIO:
    content_img = preprocess(img_bytes_to_array(content_image), 384)
    style_img = preprocess(img_bytes_to_array(style_image), 256)
    content_style_img = preprocess(img_bytes_to_array(content_image), 256)

    style_bottleneck = run_style_predict(style_img)
    style_bottleneck_content = run_style_predict(content_style_img)
    style_bottleneck = (
        (1 - blending_ratio) * style_bottleneck_content +
        blending_ratio * style_bottleneck
    )

    stylized_image = run_style_transform(style_bottleneck, content_img)

    stylized_image = array_to_img_bytes(stylized_image)

    return stylized_image
