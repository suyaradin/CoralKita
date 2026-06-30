"""
Coral Classifier Module
=======================
Handles coral image classification using a pre-trained TensorFlow model.
Classifies images as either 'Bleaching' or 'Non-Bleaching' with confidence scores.
"""

import numpy as np
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from PIL import Image

# ============================================================================
# 1. CONSTANTS & CONFIGURATION
# ============================================================================

# Class labels matching training data
# Index 0 = bleached, Index 1 = non-bleaching
CLASS_LABELS = {0: 'Bleaching', 1: 'Non-Bleaching'}

# Model path relative to this file
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'coral_model_v2.keras')

# Global model instance (singleton pattern)
_model = None


# ============================================================================
# 2. MODEL LOADING
# ============================================================================

def loadModel():
    """
    Load the coral classification model.
    Uses singleton pattern to avoid reloading the model multiple times.
    
    Returns:
        Loaded TensorFlow model
    """
    global _model
    if _model is None:
        import tensorflow as tf
        print("[ML] Loading coral classification model...")
        model_path = os.path.abspath(MODEL_PATH)
        if not os.path.exists(model_path):
            print(f"[ML] WARNING: Model not found at {model_path}")
            return None
        _model = tf.keras.models.load_model(model_path)
        print("[ML] Model loaded successfully.")
    return _model


# ============================================================================
# 3. CLASSIFICATION FUNCTION
# ============================================================================

def classifyCoral(imagePath):
    """
    Classify a coral image as Bleaching or Non-Bleaching.
    
    Args:
        imagePath: absolute path to the image file (local file system)
        
    Returns:
        dict with keys:
            - healthName: 'Bleaching' or 'Non-Bleaching'
            - confidenceScore: float between 0 and 1
    """
    try:
        import tensorflow as tf
        model = loadModel()
        
        # Check if model loaded successfully
        if model is None:
            print("[ML] Model not available. Returning default classification.")
            return {
                "healthName": "Non-Bleaching",
                "confidenceScore": 0.0
            }
        
        # Load and preprocess image
        img = Image.open(imagePath).convert('RGB')
        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Make prediction
        predictions = model.predict(img_array, verbose=0)
        class_index = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][class_index])
        health_name = CLASS_LABELS[class_index]
        
        print(f"[ML] Classification: {health_name} ({confidence:.2%})")
        
        return {
            "healthName": health_name,
            "confidenceScore": confidence
        }
        
    except FileNotFoundError:
        print(f"[ML] ERROR: Image file not found at {imagePath}")
        return {
            "healthName": "Non-Bleaching",
            "confidenceScore": 0.0
        }
    except Exception as e:
        print(f"[ML] Classification error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "healthName": "Non-Bleaching",
            "confidenceScore": 0.0
        }


# ============================================================================
# 4. BATCH CLASSIFICATION
# ============================================================================

def classifyMultipleCorals(image_paths: list) -> list:
    """
    Classify multiple coral images in batch.
    
    Args:
        image_paths: List of absolute paths to image files
        
    Returns:
        List of dictionaries with classification results
    """
    results = []
    for path in image_paths:
        result = classifyCoral(path)
        result['imagePath'] = path
        results.append(result)
    return results


# ============================================================================
# 5. UTILITY FUNCTIONS
# ============================================================================

def get_class_labels() -> dict:
    """
    Get the class labels mapping.
    
    Returns:
        Dictionary mapping class indices to label names
    """
    return CLASS_LABELS.copy()


def get_model_info() -> dict:
    """
    Get information about the loaded model.
    
    Returns:
        Dictionary with model information
    """
    model = loadModel()
    if model is None:
        return {
            "loaded": False,
            "error": "Model not found or failed to load"
        }
    
    return {
        "loaded": True,
        "input_shape": model.input_shape,
        "output_shape": model.output_shape,
        "classes": list(CLASS_LABELS.values())
    }


# ============================================================================
# 6. MAIN (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    """
    Test the classifier with a sample image.
    Usage: python coralclassifier.py /path/to/image.jpg
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python coralclassifier.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"[Test] Classifying image: {image_path}")
    
    result = classifyCoral(image_path)
    print(f"[Test] Result: {result}")