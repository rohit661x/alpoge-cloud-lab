#!/usr/bin/env python3
"""Materialize the import closure of the pinned archive's orbitSum theorem."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen


COMMIT = "40e56bab026552e089d7afcfeff08d2defb9c005"
BASE = "https://raw.githubusercontent.com/leanprover-community/riemann-hypothesis/" + COMMIT
ROOT = Path(__file__).resolve().parent
FILES = {
    "lean-toolchain": "3aac669c7a910ec2389f4e4f921b605adf6ebf2d1e0c9b9cd0be4d33f3f5db71",
    "lakefile.toml": "b831ad8cac0babb7bf713433259bdfe5163e58c90734e86d71536d4e30ddec4c",
    "lake-manifest.json": "fee57ee9ed399d0a638ca955e5ad40a37a36eeb9b6dfd9f5964114fa7bbe4774",
    "src/Formalism/ThetaLiftIndependence/ThetaOrbitSums/OrbitSum.lean": "61ba191683315fffc3dcc0d633c1b59a913352b2522c19efcf32fb51f59bd18e",
    "src/Formalism/ThetaLiftIndependence/Statement.lean": "152e9f5bc1edaaa4f87f9d744808443e06e84c6f943938d03193729d2629255e",
    "src/Formalism/HermitianLattices/StatementLat.lean": "38a4a07538f89db787edb0f968266e3e34732c459c662e1d48c4e3be6b2bd4e6",
    "src/Formalism/HermitianLattices/StatementTheta.lean": "022656a7cda6cd623c61421f65b2b455cdf90dcc702a4571e859588d00e2a3c1",
    "src/Formalism/SatakeDualWeyl/Statement.lean": "ff0b4971b2c44e6b9eeac44013ff35e5aeb7a126a87d7640d2fd72277147696c",
    "src/Formalism/AlphaUniqueness/Statement.lean": "7c511c51e0843fde4d1565486e2234896fc9d41ed79c4b7f9e53b3c258b0dcb0",
    "src/Formalism/FockGram/StatementHerm.lean": "e43e12b8c437eee06a1d62f20fb8378ea04e5ff7f7ef16585ddfbbd13fa9fa87",
    "src/Formalism/LatticeTheta/Statement.lean": "f7ffef3f178e6561642d908ca1893357c73e9614e0b07c784e7a9a91aee4a735",
    "src/Formalism/FockGram/StatementLat.lean": "87cfdae603278d7c9e502c093bdba25ede58ea6beb60eaede474b907c4a85724",
}


def fetch(item):
    path, expected = item
    destination = ROOT / path
    if destination.is_file() and sha256(destination.read_bytes()).hexdigest() == expected:
        return path
    with urlopen(BASE + "/" + path, timeout=45) as response:
        data = response.read()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"{path}: SHA-256 mismatch at {COMMIT}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return path


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(fetch, FILES.items()):
            print(name)
