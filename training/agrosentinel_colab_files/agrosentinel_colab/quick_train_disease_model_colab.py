"""
Quick starter training script for Google Colab.

Purpose:
- Train a simple disease classification model from a folder dataset
- Save the trained model as plant_disease_model.h5

Expected dataset structure:
PlantVillage_small/
    Tomato___Early_blight/
    Tomato___Late_blight/
    Tomato___healthy/
    Potato___Early_blight/
    Potato___Late_blight/
    Potato___healthy/

You can start with 3-6 classes first to make testing easy.
"""

import json
import tensorflow as tf
from tensorflow.keras import layers, models

DATA_DIR = "PlantVillage_small"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42
EPOCHS = 5

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

class_names = train_ds.class_names
print("Class names:", class_names)

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

model = models.Sequential([
    layers.Rescaling(1.0 / 255, input_shape=(224, 224, 3)),
    layers.Conv2D(32, 3, activation="relu"),
    layers.MaxPooling2D(),
    layers.Conv2D(64, 3, activation="relu"),
    layers.MaxPooling2D(),
    layers.Conv2D(128, 3, activation="relu"),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(len(class_names), activation="softmax"),
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
)

model.save("plant_disease_model.h5")

with open("class_names.json", "w", encoding="utf-8") as f:
    json.dump(class_names, f, indent=2)

print("Saved model to plant_disease_model.h5")
print("Saved class names to class_names.json")
