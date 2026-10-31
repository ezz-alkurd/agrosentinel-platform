# Camera and Jetson agent

Implementation work remains. Provide adapters for USB, RTSP/RTSPS, HTTP/MJPEG, Jetson CSI, recorded media and explicitly supported drone SDK/capture paths. Expose capture, preview, capabilities and optional telemetry through one source interface.

Implement single-use pairing, protected camera credentials, versioned configuration, start/stop, stream reconnection, bounded current-frame queues, per-source model routing and event confirmation, a durable event outbox, auto-start packaging and cloud/edge backend selection. A locally installed edge release can infer during a network outage; a cloud-only agent must display degraded analysis instead of pretending to keep detecting.
