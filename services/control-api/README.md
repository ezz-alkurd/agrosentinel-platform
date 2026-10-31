# ASP.NET Core control API

Implemented as a .NET 8 module hosted by presentation-web. SQL Server schema: schema.sql. Setup and verification: [SMARTERASP_SETUP.md](../../docs/SMARTERASP_SETUP.md).

API routes cover health, Firebase-authenticated owner access, pairing, device heartbeat and revocation, idempotent evidence-backed events, event feeds/deletion and signed private media. Durable inference jobs/cloud GPU workers are outside this change. Hosted database provisioning and end-to-end validation remain pending.
