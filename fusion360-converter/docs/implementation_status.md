# Implementation status

The `inspect` command decodes local F3D/F3Z archives using cadmpeg 0.6.12 and reports decoded product definitions, occurrences, root occurrences, bodies and sketches, in text or versioned JSON. Definitions and occurrences are separate; root occurrences are not all top-level objects. Decode losses are surfaced. F3Z decoding merges documents, losing document identity in these counts. This is read-only and does not require CAD applications.

No redistributable real Fusion fixtures are present, so successful decoding, modern archives, compression variants and count accuracy on real files remain unverified. Timeline and migration are not implemented. Next: validate against representative user-owned F3D and F3Z files and investigate document-level archive inspection and source object coverage before expanding queries.

cadmpeg's installed source declares Rust 1.88, but the resolved zip 9.8.2 declares 1.89; 1.89 is the locked dependency lower bound, not a tested MSRV. The local toolchain is Rust 1.100.0. Crates.io access was unavailable; the locally cached 0.6.12 was selected and locked without downgrading.

The `diagnostics` command lists numbered cadmpeg loss notes with their codes and can show one at a time. It currently explains the composed sketch-name warning; other messages remain explicitly uninvestigated. The pasted real-file report demonstrates that decoding produced output on one user file, but the file itself and count accuracy were not independently verified in this workspace.
