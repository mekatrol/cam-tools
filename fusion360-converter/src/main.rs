use clap::{Parser, Subcommand};
use std::{
    fs::OpenOptions,
    io::Write,
    path::{Path, PathBuf},
};

#[derive(Parser)]
#[command(version, about = "Inspect Autodesk Fusion archives")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Read an archive and report decoded model structure.
    Inspect {
        path: PathBuf,
        #[arg(long)]
        json: bool,
        /// Write JSON to a new file instead of stdout.
        #[arg(short, long, requires = "json")]
        output: Option<PathBuf>,
    },
    /// List decoder diagnostics, or examine one by its report number.
    Diagnostics {
        path: PathBuf,
        #[arg(long)]
        number: Option<usize>,
        #[arg(long)]
        json: bool,
        /// Write JSON to a new file instead of stdout.
        #[arg(short, long, requires = "json")]
        output: Option<PathBuf>,
    },
}

fn main() {
    if let Err(error) = run() {
        eprintln!("error: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    match Cli::parse().command {
        Command::Inspect { path, json, output } => {
            let result = fusion360_converter::inspect(&path)?;
            if json {
                write_json(&result, output.as_deref())?;
            } else {
                println!("File: {}", path.display());
                println!(
                    "Decoded component definitions: {}",
                    result.component_definitions
                );
                println!("Decoded occurrences: {}", result.occurrences);
                println!("Top-level occurrences: {}", result.top_level_occurrences);
                println!("Decoded bodies: {}", result.bodies);
                println!("Decoded sketches: {}", result.sketches);
                for warning in &result.warnings {
                    eprintln!("warning: {warning}");
                }
            }
        }
        Command::Diagnostics {
            path,
            number,
            json,
            output,
        } => {
            let all = fusion360_converter::diagnostics(&path)?;
            let selected: Vec<_> = if let Some(n) = number {
                vec![all.iter().find(|d| d.number == n).ok_or_else(|| {
                    format!(
                        "diagnostic {n} not found; report contains {} diagnostics",
                        all.len()
                    )
                })?]
            } else {
                all.iter().collect()
            };
            if json {
                write_json(
                    &serde_json::json!({"schema_version": 1, "diagnostics": selected}),
                    output.as_deref(),
                )?;
            } else {
                for d in selected {
                    println!("{} [{}] {}: {}", d.number, d.severity, d.code, d.message);
                    if number.is_some() {
                        println!("  Source: {}", d.source);
                        if let Some(provenance) = &d.provenance {
                            println!("  Provenance: {provenance}");
                        }
                        println!("  Practical explanation: {}", d.explanation.unwrap_or("Not yet investigated. Consult the decoder source for this code; do not infer the impact from its severity alone."));
                    }
                }
                if number.is_none() {
                    println!(
                        "Use --number N to inspect one diagnostic. Numbers refer to this decode report and may change."
                    );
                }
            }
        }
    }
    Ok(())
}

fn write_json(
    value: &impl serde::Serialize,
    output: Option<&Path>,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut data = serde_json::to_vec_pretty(value)?;
    data.push(b'\n');
    if let Some(path) = output {
        let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
        file.write_all(&data)?;
    } else {
        std::io::stdout().lock().write_all(&data)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::write_json;
    #[test]
    fn writes_json_and_refuses_overwrite() {
        let dir = std::env::temp_dir().join(format!("fusion-output-test-{}", std::process::id()));
        std::fs::create_dir(&dir).unwrap();
        let path = dir.join("report.json");
        write_json(&serde_json::json!({"count": 1}), Some(&path)).unwrap();
        let contents = std::fs::read(&path).unwrap();
        assert_eq!(
            serde_json::from_slice::<serde_json::Value>(&contents).unwrap()["count"],
            1
        );
        assert!(write_json(&serde_json::json!({"count": 2}), Some(&path)).is_err());
        assert_eq!(std::fs::read(&path).unwrap(), contents);
        std::fs::remove_dir_all(dir).unwrap();
    }
}
