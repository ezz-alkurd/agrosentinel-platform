# Python inference service and worker

Implementation work remains. Extract tested runtime operations from `ai-backend/` into one model interface for the approved close-up, far and fire releases. FastAPI serves internal model/health routes; the external worker claims SQL-backed jobs through the authenticated application API, executes inference and completes jobs idempotently.

Deploy an immutable Linux GPU container to a Runpod Secure Cloud Pod, with persistent artifact caching and restart monitoring. Do not run training on the production inference instance. Use a separate task/Pod for training. The cloud and original Jetson Nano require separate runtime environments; share the contract, not an incompatible requirements file or TensorRT engine.
