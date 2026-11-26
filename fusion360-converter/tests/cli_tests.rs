use std::{fs, process::Command};

#[test]
fn rejects_wrong_extension_and_invalid_archive() {
    let exe = env!("CARGO_BIN_EXE_fusion360-converter");
    let wrong = Command::new(exe)
        .args(["inspect", "model.txt", "--json"])
        .output()
        .unwrap();
    assert!(!wrong.status.success());
    assert!(wrong.stdout.is_empty());
    let path = std::env::temp_dir().join(format!(
        "fusion-converter-invalid-{}.F3D",
        std::process::id()
    ));
    fs::write(&path, b"not a Fusion archive").unwrap();
    let invalid = Command::new(exe)
        .arg("inspect")
        .arg(&path)
        .arg("--json")
        .output()
        .unwrap();
    assert!(!invalid.status.success());
    assert!(invalid.stdout.is_empty());
    assert!(!invalid.stderr.is_empty());
    assert_eq!(fs::read(&path).unwrap(), b"not a Fusion archive");
    fs::remove_file(path).unwrap();
}

#[test]
fn help_describes_inspect() {
    let output = Command::new(env!("CARGO_BIN_EXE_fusion360-converter"))
        .arg("--help")
        .output()
        .unwrap();
    assert!(output.status.success());
    assert!(String::from_utf8_lossy(&output.stdout).contains("inspect"));
}

#[test]
fn query_help_and_invalid_archives_are_safe() {
    let exe = env!("CARGO_BIN_EXE_fusion360-converter");
    let help = Command::new(exe)
        .args(["query", "model.f3d", "--help"])
        .output()
        .unwrap();
    let text = String::from_utf8_lossy(&help.stdout);
    assert!(help.status.success());
    assert!(text.contains("components") && text.contains("sketches"));
    for kind in ["components", "sketches"] {
        let output = Command::new(exe)
            .args(["query", "model.txt", kind, "--json"])
            .output()
            .unwrap();
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
        assert!(!output.stderr.is_empty());
    }
}
