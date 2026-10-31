# Repository handoff

Canonical source directory: `D:\graduation-project\agrosentinel`. Public GitHub repository: https://github.com/ezz-alkurd/agrosentinel-platform. The published `main` branch starts from a fresh root commit; the previous local commit remains only on the local `local/pre-publication` branch.

Original source is preserved under `D:\graduation-project\_archive\reorganization-2026-10-17\baseline-source`; raw data and old model weights remain at the outer project root for controlled reuse. Source-copy hashes and the move manifest are in that same reorganization archive. Generated outputs, previous planning documents and historical contributor work are archived without deleting files. Existing dataset and weight paths stay intact.

The repository owner is `ezz-alkurd`. The source is pushed to `origin/main`. The five-person team is Ezzeldeen Alkurd (owner), Sara Hamdan, Khalid Masoud, Raneen Abdullah, and Dina Afram. Anyone can read and clone the repository. The four collaborators need invitations to push branches or open pull requests in this repository; use their verified GitHub usernames rather than guessing identities from names.

Teammates can clone with `git clone https://github.com/ezz-alkurd/agrosentinel-platform.git` immediately. To give them write access, open the repository's **Settings → Collaborators and teams**, search each verified username, and invite them. After accepting, each teammate can make a branch per task and open a pull request into `main`. Assign a teammate to review each pull request. If the repository plan supports branch rules, require a pull request and passing source checks before merging to `main`.

The initial source excludes private service accounts, signing keys, raw datasets and weight files. Firebase client configuration is generated/restored locally and ignored. Use controlled storage for datasets and model artifacts, with checksums and access appropriate to the dataset source conditions.

Do not run `git init` in the outer historical project root or reuse old commit history. Work inside the clean source directory. Use feature branches and pull requests; set branch protections in GitHub after publishing.
