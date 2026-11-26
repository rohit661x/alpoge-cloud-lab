# When does an encrypted ConvMNIST client recover the cost of two more rotation keys?

For a client already using 17 rotation keys after five predictions, uploading the keys for rotations +512 and +2048 at request six took extra time immediately. The upgrade first held a cumulative lead over continuing with 17 keys at **prediction 12** with keys prepared in advance, and **prediction 13** with keys generated on demand. Both leads persisted through the last measured prediction, number 24. These are averages from one Apple M5 Pro running the client and evaluator as separate processes.

| Conditional comparison against staying at 17 keys | Prepared keys | On-demand keys |
| --- | ---: | ---: |
| Independent fresh client keys | 12 | 4 |
| Extra mean wait from the end of prediction 5 through prediction 6 | 125.6 ms | 177.0 ms |
| First prediction with a sustained mean lead through 24 | 12 | 13 |
| Mean time saved from the end of prediction 5 through prediction 24 | 221.2 ms | 337.8 ms |

**Should every client start with 17 keys?** The experiment leaves that question open. On the prespecified mix of sessions ending at five (80%) or 24 (20%), the adaptive policy averaged 13.456 seconds with prepared keys. Fixed 19 was the fastest fixed policy at 13.469 seconds. The estimated 12.5 ms advantage had an exploratory 95% paired bootstrap interval spanning **28.3 ms faster to 5.8 ms slower**, reselecting the fastest fixed policy in each resample. For sessions known in advance to reach 24, starting with 19 keys was 121.6 ms faster on average than upgrading. The prespecified mix used an average **76.05 MB** of actual framed client uploads with the adaptive policy, **74.50 MB** with fixed 17, and **82.44 MB** with fixed 19. MB is decimal.

## What was measured

The trained TenSEAL ConvMNIST classifier ran on the first eight MNIST test images. Each fresh client key supplied 24 freshly encrypted inputs, one per request position. At each position the four policies received the same ciphertext. The prepared cohort ran 1,152 encrypted predictions and the separate on-demand cohort ran 384. All 1,536 predictions agreed with both scalar inference and the digit label. The paired statistical unit is a fresh client key. The eight repeated images support a correctness check for these inputs.

The client paced writes at 500 Mbit/s over local TCP. Replies were unpaced and each evaluator used one thread. The prepared-key clock ran from the first setup write through decryption. The on-demand clock also included preparing the initial public catalog and generating incremental keys when needed. Both clocks excluded shared secret-key setup, input encryption, process startup and connection establishment. The key counts and timings depend on this model, packing, software and workload.

## Reproduce the completed study

Run this from the checkout root with stock Python 3.11 or newer. The command works offline. It checks the distribution and archive hashes, rebuilds the scalar predictions from the IDX fixtures and weights, reconciles the client and evaluator journals, and reproduces the published timing summaries from the recorded observations.

```sh
python3 research/conv-mnist-upgrade/verify.py
```

The HTML report includes the measured workload comparisons and an interactive session-length control. Download it and open it locally. The replay ZIP contains the original protocol, native runner and build instructions for collecting new measurements, model and dataset attribution, machine-readable results and a provenance record for this repository edition. That record documents two normalized paths in older pilot metadata and identifies the archival source by SHA-256. Research preparation and code were predominantly AI-generated. [Report](report.html) · [Replay archive](replay.zip) · [SHA-256 manifest](SHA256SUMS)

## Partial two-Mac replication · November 25, 2026

The physical M5 Pro client and M5 MacBook Air evaluator completed **10 of 12** prepared-key blocks. All **960 of 960** predictions agreed with the scalar reference and labels across eight images, with 9,600 decrypted logits checked. A separate four-prediction smoke test passed. Eight uncommitted attempts at the eleventh block produced 54 prediction receipts, all excluded. The on-demand replication had completed **0 of 4** blocks at this snapshot.

The checkpoint publishes aggregate counts and digests of the underlying local verification records. The repository check validates its checksum and count consistency. Independent replay of the two-Mac trial would require the underlying cross-host journals. The primary cross-host latency comparison is pending. [Partial checkpoint](partial/two-mac-checkpoint.json)

## Model and data attribution

The model and benchmark come from OpenMined’s TenSEAL v0.3.18. The replay includes the upstream Apache 2.0 license, converted weights and their provenance. MNIST was created by Yann LeCun, Corinna Cortes and Christopher J. C. Burges. The enclosed MNIST fixtures carry CC BY-SA 3.0 attribution. The report’s external workload sensitivity uses aggregate conversation lengths from VisionArena as a proxy for session length. [Pinned TenSEAL checkpoint](https://github.com/OpenMined/TenSEAL/blob/c962074f0aa82cf30eeaddf17af887a8ea0e66fe/tutorials/parameters/ConvMNIST-0.1.pickle) · [MNIST attribution](https://keras.io/api/datasets/mnist/) · [VisionArena data revision](https://huggingface.co/datasets/lmarena-ai/VisionArena-Chat/tree/1394b4f59ab6f1f2e5aff6bc15b448e15960e170)
