# Replaying and citing the research artifacts

For the encrypted digit-classification experiment, start with the current study README. It distinguishes measurements made by two processes on one computer from measurements made on two physical Macs. Cite the hardware, cohort and repository commit with any timing result. A fresh client key is the paired unit of analysis. [ConvMNIST study](../research/conv-mnist-upgrade/README.md)

## Replay the single-machine measurements

From the checkout root, run this command with Python 3.11 or newer. The replay works offline with the Python standard library.

```sh
python3 research/conv-mnist-upgrade/verify.py
```

The verifier checks the packaged files against their SHA-256 manifests, reconstructs scalar predictions from the released model and MNIST pixels, reconciles client and evaluator journals, and recalculates the timing summaries. The two cohorts contain 1,152 prepared-key predictions and 384 on-demand predictions. Both use the same eight distinct images. This command analyzes recorded observations. For fresh native timings, extract the replay ZIP and follow `work/second-trained/patched/README.md` for the pinned extension build and `work/switchtrial/harness/README.md` for the experiment. [Verifier](../research/conv-mnist-upgrade/verify.py) · [Replay ZIP](../research/conv-mnist-upgrade/replay.zip) · [SHA-256 manifest](../research/conv-mnist-upgrade/SHA256SUMS)

The November 25 snapshot archived the single-machine journals and published an aggregate two-Mac checkpoint covering 10 of 12 prepared-key blocks. Use that revision when citing the checkpoint. The current study README records subsequent coverage and identifies the evidence available for each cohort. [November 25 snapshot](https://github.com/rohit661x/alpoge-cloud-lab/tree/219139e782f9b4314b4fb0103871e108526d7081/research/conv-mnist-upgrade) · [Current study](../research/conv-mnist-upgrade/README.md)

## Model, data and code provenance

| Material | Contents and reuse terms |
| --- | --- |
| TenSEAL ConvMNIST | The ZIP contains OpenMined’s original checkpoint and upstream benchmark, plus the study’s converted binary and JSON weights. The archived model README describes the tensor transposition and fixture preparation. The upstream Apache 2.0 license is included at `work/second-trained/model/TenSEAL-LICENSE`. Preserve applicable notices and identify modifications when redistributing upstream material. [Pinned checkpoint](https://github.com/OpenMined/TenSEAL/blob/c962074f0aa82cf30eeaddf17af887a8ea0e66fe/tutorials/parameters/ConvMNIST-0.1.pickle) · [Upstream license](https://github.com/OpenMined/TenSEAL/blob/c962074f0aa82cf30eeaddf17af887a8ea0e66fe/LICENSE) |
| MNIST test images and labels | The ZIP includes the full 10,000-record test split in the two compressed IDX files and eight derived fixtures for the encrypted runs. Credit Yann LeCun, Corinna Cortes and Christopher J. C. Burges. LeCun and Cortes hold the dataset copyright. MNIST is distributed under CC BY-SA 3.0. Preserve attribution, link the license, identify adaptations and honor its share-alike terms when distributing adapted data. [Dataset source](https://github.com/cvdfoundation/mnist) · [Dataset attribution](https://keras.io/api/datasets/mnist/) · [License](https://creativecommons.org/licenses/by-sa/3.0/) |
| VisionArena conversation lengths | The sensitivity analysis ships counts grouped by turn count, per-shard summaries and checksums. Study code uses those counts as a proxy for session length. The source dataset has its own agreement restricting redistribution. Obtain source data directly from the publisher for a fresh collection. [Pinned dataset and terms](https://huggingface.co/datasets/lmarena-ai/VisionArena-Chat/blob/1394b4f59ab6f1f2e5aff6bc15b448e15960e170/README.md) · [VisionArena paper](https://openaccess.thecvf.com/content/CVPR2025/html/Chou_VisionArena_230k_Real_World_User-VLM_Conversations_with_Preference_Labels_CVPR_2025_paper.html) |

The original verifier, experimental harness and reports are publicly readable. This edition has no project-wide license for those materials. For reuse that requires permission, contact the maintainer through the repository. Retain the relevant third-party terms with any separately licensed component. [Repository](https://github.com/rohit661x/alpoge-cloud-lab) · [GitHub’s licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

## Earlier encrypted-computation releases

These three tagged prereleases are publicly downloadable. Their historical tag names contain `private-preview`. Each release page contains the original brief and ZIP. The commands below assume you have extracted the corresponding ZIP and entered its top-level directory.

| Release | What it establishes | Replay |
| --- | --- | --- |
| [Eight encrypted neighbor views](https://github.com/rohit661x/alpoge-cloud-lab/releases/tag/stencil-rotations-private-preview-1) | A finite enumeration and two-host measurements for a centered 3×3 stencil in Microsoft SEAL BFV. The eight-view result concerns this BFV packing and its directed-key count. ConvMNIST uses CKKS and times a trained classifier. | From `stencil-rotation-kit/`, run `python3 -B verify.py --enumerate` with Python 3.9+ and a C++17 compiler. |
| [Encrypted filter bank](https://github.com/rohit661x/alpoge-cloud-lab/releases/tag/filter-bank-private-preview-1) | Native SEAL filter-bank measurements and source-level OpenFHE estimates. For measured execution of the first seven ResNet20 convolutions, use the seven-convolution release below. | From `encrypted-filter-study/`, run `python3 -B verify.py --search` with Python 3.9+, Git and a C++17 compiler. |
| [First seven ResNet20 convolutions](https://github.com/rohit661x/alpoge-cloud-lab/releases/tag/resnet20-seven-conv-private-preview-1) | Native OpenFHE measurements using Rovida and Leporati’s model. Its measured endpoint is the first seven convolutions and their feature-map checkpoints. A final classifier prediction requires later network stages. The archive includes the upstream model-project and OpenFHE notices in `licenses/`. | From `native-stage-study/`, run `python3 -B verify.py` with Python 3.9+. |

## Number-theory artifacts

To check the supplied 1,024-bit prime and its quadratic-form representation, run the following from the checkout root. The command uses the public certificate in this repository. The full Lean verification separately requires the pinned challenge and solution exports and their checker. [Certificate](../cm_prime_1024.json) · [Checker source](../alpoge_cm_certificate.py) · [Formal verification procedure](https://math.mit.edu/~drew/grh/)

```sh
python3 alpoge_cm_certificate.py verify cm_prime_1024.json
```
