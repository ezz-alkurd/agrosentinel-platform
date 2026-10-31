# ONNX Runtime Java classes are accessed through JNI. Preserve their names and fields.
# https://onnxruntime.ai/docs/build/android.html
-keep class ai.onnxruntime.** { *; }
