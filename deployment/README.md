# Deployment requirements

## SmarterASP.NET

Confirm actual account plan/OS and IIS runtime support, app-pool memory/recycles, upload and request limits, outbound HTTPS, database quota and HTTPS domain. Publish ASP.NET Core 10 application artifacts using the account's supported Web Deploy/FTPS route after implementation. Apply SQL migrations deliberately and back up before migration. Configure secrets server-side; never commit production settings.

Required configuration groups: SQL connection; Firebase project/token validation; media bucket access; worker authentication; push sender; accepted client origins; pairing token parameters; upload limits; model registry; outbox/retention policies.

## Runpod

Build the Linux GPU runtime image in CI/registry, publish an immutable tag/digest, create a Secure Cloud GPU Pod sized from the actual models and far-image tiling workload, attach persistent model cache, inject worker credentials, and launch the supervised FastAPI/worker process. Docker Compose does not run inside Runpod Pods. Keep authoritative artifacts backed up independently of the instance and cache.

The persistent worker calls the ASP.NET internal job/outbox APIs over authenticated HTTPS. Keep that worker credential out of mobile apps and camera agents. Configure timeouts, bounded batches, retry/backoff and health alerts. A replacement worker can reclaim expired leases. No GPU subscription or Pod has been purchased by this repository setup.

## Jetson

Identify original Nano versus Orin Nano before choosing the image. Original Nano/JetPack 4 needs a legacy-compatible environment. Validate ONNX operators and build TensorRT engines on that target. Publish compatible releases with checksums; report unsupported models and measured scheduling/memory limits. Do not copy a cloud TensorRT engine to the Nano.
