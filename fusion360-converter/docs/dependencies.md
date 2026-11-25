# Dependencies

`cadmpeg-codec-f3d` and `cadmpeg-ir` 0.6.12 are pinned together, based on installed crate sources. The codec uses ZIP 9 and handles Fusion decoding; its `Codec::decode` returns IR and a report with losses. Its F3Z decode merges documents. `clap` provides argument parsing; `serde` and `serde_json` provide versioned JSON output. Cargo.lock records the complete resolution. The locked ZIP 9.8.2 declares Rust 1.89; this lower bound has not been independently tested.
