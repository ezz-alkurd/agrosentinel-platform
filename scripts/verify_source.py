"""Verify the clean source boundary without executing model/Firebase operations."""
from pathlib import Path
import ast
import json
import re
import subprocess

root = Path(__file__).resolve().parents[1]
issues = []
counts = {"python_files": 0, "json_files": 0, "files": 0}
tracked = subprocess.run(
    ['git', '-c', f'safe.directory={root.as_posix()}', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
    cwd=root, capture_output=True, check=True,
).stdout.decode('utf-8').split('\0')
for rel in filter(None, tracked):
    p = root / rel
    if not p.is_file():
        continue
    counts['files'] += 1
    allowed_mobile_model = rel == 'app/assets/models/tomato_closeup.onnx'
    if p.name in {'serviceAccountKey.json','firebase_options.dart','google-services.json'} or (p.suffix.lower() in {'.pt','.pth','.onnx','.engine','.jks','.keystore','.p12'} and not allowed_mobile_model):
        issues.append(f'Local-only artifact inside source tree: {rel}')
    if p.stat().st_size >= 50 * 1024 * 1024:
        issues.append(f'Oversized source file: {rel}')
    if p.suffix == '.py':
        try:
            ast.parse(p.read_text(encoding='utf-8-sig'), filename=rel)
            counts['python_files'] += 1
        except (SyntaxError, UnicodeError) as exc:
            issues.append(f'Python parse error: {rel}: {exc}')
    if p.suffix == '.json':
        try:
            json.loads(p.read_text(encoding='utf-8-sig'))
            counts['json_files'] += 1
        except (ValueError, UnicodeError) as exc:
            issues.append(f'JSON parse error: {rel}: {exc}')
    if p.suffix in {'.py','.json','.ipynb','.dart','.xml','.md','.txt','.yml','.yaml','.ps1','.properties','.config'}:
        content = p.read_text(encoding='utf-8-sig', errors='replace')
        # Build patterns in fragments so this verifier does not flag its own source.
        patterns = [r'-----BEGIN ' + r'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----', r'gh' + r'p_[A-Za-z0-9]{30,}', r'github_' + r'pat_[A-Za-z0-9_]{30,}', r'AIza' + r'[A-Za-z0-9_-]{30,}']
        if any(re.search(pattern, content) for pattern in patterns):
            issues.append(f'Credential material requires review: {rel}')
catalog = json.loads((root/'contracts/model-catalog.json').read_text())
if {m['id'] for m in catalog['models']} != {'plant-closeup','plant-far','fire-smoke'}:
    issues.append('Expected exactly the three agreed model IDs')
fire = next(m for m in catalog['models'] if m['id'] == 'fire-smoke')
if fire['owner'] != 'Dina Afram':
    issues.append('Fire-model owner must remain Dina Afram')
if issues:
    print('\n'.join(issues))
    raise SystemExit(1)
print(json.dumps({'status':'passed', **counts}, indent=2))
