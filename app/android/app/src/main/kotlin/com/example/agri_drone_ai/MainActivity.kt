package com.example.agri_drone_ai

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import io.flutter.FlutterInjector
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import org.json.JSONObject
import java.nio.FloatBuffer
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : FlutterActivity() {
    private var plantEngine: PlantInference? = null
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        plantEngine = PlantInference(applicationContext)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "agrosentinel/plant_inference")
            .setMethodCallHandler { call, result ->
                if (call.method != "analyze") result.notImplemented()
                else plantEngine?.analyze(call.argument<FloatArray>("input"), result)
            }
    }
    override fun onDestroy() {
        plantEngine?.close()
        super.onDestroy()
    }
}

private class PlantInference(private val context: Context) {
    private val executor = Executors.newSingleThreadExecutor()
    private val main = Handler(Looper.getMainLooper())
    private val busy = AtomicBoolean(false)
    private val closed = AtomicBoolean(false)
    private var session: OrtSession? = null
    private var environment: OrtEnvironment? = null

    private fun asset(name: String): ByteArray {
        val key = FlutterInjector.instance().flutterLoader().getLookupKeyForAsset(name)
        return context.assets.open(key).use { it.readBytes() }
    }
    private fun load(): OrtSession {
        session?.let { return it }
        val metadata = JSONObject(String(asset("assets/models/tomato_closeup.json"), Charsets.UTF_8))
        val bytes = asset("assets/models/tomato_closeup.onnx")
        val hash = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 0xff) }
        check(hash == metadata.getString("sha256")) { "Model checksum mismatch" }
        val env = OrtEnvironment.getEnvironment()
        environment = env
        val options = OrtSession.SessionOptions()
        options.setIntraOpNumThreads(2)
        options.setMemoryPatternOptimization(false)
        options.setInterOpNumThreads(1)
        try { session = env.createSession(bytes, options) } finally { options.close() }
        return checkNotNull(session)
    }
    fun analyze(input: FloatArray?, result: MethodChannel.Result) {
        if (closed.get()) { result.error("UNAVAILABLE", "Model runtime is closed", null); return }
        if (input == null || input.size != 3 * 224 * 224) { result.error("INPUT", "Invalid input tensor", null); return }
        if (busy.getAndSet(true)) { result.error("BUSY", "Analysis already running", null); return }
        executor.execute {
            try {
                val model = load()
                val started = System.nanoTime()
                val probabilities = OnnxTensor.createTensor(checkNotNull(environment), FloatBuffer.wrap(input), longArrayOf(1, 3, 224, 224)).use { tensor ->
                    model.run(mapOf("images" to tensor)).use { output ->
                        @Suppress("UNCHECKED_CAST")
                        val values = output.get(0).value as Array<FloatArray>
                        values[0].map { it.toDouble() }
                    }
                }
                val elapsed = (System.nanoTime() - started) / 1_000_000.0
                main.post { if (!closed.get()) result.success(mapOf("probabilities" to probabilities, "inferenceMs" to elapsed, "provider" to "CPU")) }
            } catch (error: Throwable) {
                Log.e("AgroSentinelPlant", "Packaged model inference failed", error)
                main.post { if (!closed.get()) result.error("INFERENCE_UNAVAILABLE", "Unable to load or run the packaged model", null) }
            } finally { busy.set(false) }
        }
    }
    fun close() {
        if (closed.getAndSet(true)) return
        executor.execute { session?.close(); session = null }
        executor.shutdown()
        // OrtEnvironment is process-wide and remains owned by ONNX Runtime.
    }
}
