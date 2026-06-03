import numpy as np
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from PIL import Image

# Class labels matching training data
# Index 0 = bleached, Index 1 = non-bleached
CLASS_LABELS = {0: 'Bleaching', 1: 'Non-Bleaching'}

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'coral_model_v2.keras')

_model = None

def loadModel():
    global _model
    if _model is None:
        print("[ML] Loading coral classification model...")
        _model = tf.keras.models.load_model(os.path.abspath(MODEL_PATH))
        print("[ML] Model loaded successfully.")
    return _model

def classifyCoral(imagePath):
    """
    Classify a coral image as Bleaching or Non-Bleaching.
    
    Args:
        imagePath: absolute path to the image file
        
    Returns:
        dict with keys: healthName, confidenceScore
    """
    try:
        model = loadModel()

        img = Image.open(imagePath).convert('RGB')
        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        predictions = model.predict(img_array, verbose=0)
        classIndex = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][classIndex])
        healthName = CLASS_LABELS[classIndex]

        print(f"[ML] Classification: {healthName} ({confidence:.2%})")

        return {
            "healthName": healthName,
            "confidenceScore": confidence
        }

    except Exception as e:
        print(f"[ML] Classification error: {e}")
        return {
            "healthName": "Non-Bleaching",
            "confidenceScore": 0.0
        }