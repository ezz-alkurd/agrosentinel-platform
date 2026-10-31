# Authenticated tomato photo service

This is the selected demo's compatibility endpoint for the existing Flutter AI Hub. It does not implement or replace the final ASP.NET/SQL job platform. The existing Firestore demo event path remains the camera path.

Build context is generated under `deliverables/AgroSentinel-Plant-Cloud-Context/` by `scripts/package_doctor_demo.py`. Never build from a directory containing credentials. The small selected classifier runs on CPU; the image does not need CUDA. No cloud resource has been purchased or started.

```sh
docker build -t agrosentinel-plant-photo:doctor-20261024 .
docker run --rm -p 8008:8008 --mount type=bind,src=/private/serviceAccountKey.json,dst=/run/secrets/firebase.json,readonly -e FIREBASE_KEY_PATH=/run/secrets/firebase.json agrosentinel-plant-photo:doctor-20261024
```

For Runpod, publish the image to your registry, choose an existing appropriately sized Pod, expose HTTP port 8008 and supply `FIREBASE_KEY_PATH` through a mounted private credential. Use the returned Runpod HTTPS proxy URL as the Flutter analysis-service URL. Do not run Docker-in-Docker inside a Pod. Do not put the key in the image, Git, mobile app or handoff ZIP.

`GET /health` reports the actual loaded model ID/hash. `POST /diagnose` accepts raw JPEG/PNG/WebP, at most 8 MB and 20 megapixels. It requires `Authorization: Bearer <signed-in Firebase ID token>`. Low-confidence results return `status=inconclusive`, never healthy. Results are experimental suggestions for close-up tomato leaves, not a general field diagnostic release.

Before handoff: confirm `/health`, reject unauthenticated requests, sign in on a real phone, analyze the same close-up photo over WiFi then mobile data, restart the container, and repeat. Configure provider-side request/rate limits and budgets. Actual hosted connectivity is pending account/Pod access and local container-build verification.
