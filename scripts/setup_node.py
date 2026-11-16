"""Download a checksum-verified portable Node.js runtime for local deployment."""
import hashlib
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
destination = ROOT / '.tools'
destination.mkdir(exist_ok=True)
base = 'https://nodejs.org/dist/latest-v22.x/'
checksums = urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=60).read().decode()
checksum, filename = next(line.split() for line in checksums.splitlines() if line.endswith('-win-x64.zip'))
archive = destination / filename
print('Downloading', filename, flush=True)
urllib.request.urlretrieve(base + filename, archive)
assert hashlib.sha256(archive.read_bytes()).hexdigest() == checksum, 'Node checksum mismatch'
with zipfile.ZipFile(archive) as package:
    package.extractall(destination)
print('Runtime:', destination / filename.removesuffix('.zip') / 'node.exe', flush=True)
