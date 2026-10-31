# Repository handoff

Canonical clean source directory: `D:\graduation-project\agrosentinel`.

Original source is preserved under `D:\graduation-project\_archive\reorganization-2026-10-17\baseline-source`; raw data and old model weights remain at the outer project root for controlled reuse. Source-copy hashes and the move manifest are in that same reorganization archive. Generated outputs, previous planning documents and historical contributor work are archived without deleting files. Existing dataset and weight paths stay intact.

The connected GitHub account is `ezz-alkurd`. The connector available in this session cannot create repositories/invitations, and no local GitHub CLI/token credential was available. A local commit does not imply a remote repository exists.

When authenticated GitHub CLI access is available, run `scripts/publish-github.ps1` from this source directory to create a **private** `agrosentinel-platform` repository and push `main`. The script refuses to overwrite an existing origin. It can invite exactly four teammate handles with write access. Supply verified accounts for Sara, Khalid, Raneen and Dina; do not guess identities from names or unrelated accounts.

The initial source excludes private service accounts, signing keys, raw datasets and weight files. Firebase client configuration is generated/restored locally and ignored. Use controlled storage for datasets and model artifacts, with checksums and access appropriate to the dataset source conditions.

Do not run `git init` in the outer historical project root or reuse old commit history. Work inside the clean source directory. Use feature branches and pull requests; set branch protections in GitHub after publishing.
