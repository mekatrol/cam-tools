use cadmpeg_codec_f3d::F3dCodec;
use cadmpeg_ir::{Codec, DecodeOptions, products::OccurrenceParent};
use serde::Serialize;
use std::{error::Error, fs::File, path::Path};

/// List decoder records. IDs are decoder identities, not durable migration IDs.
pub fn query(
    path: &Path,
    kind: &str,
    component: Option<&str>,
) -> Result<serde_json::Value, Box<dyn Error>> {
    let ext = path.extension().and_then(|x| x.to_str()).unwrap_or("");
    if !ext.eq_ignore_ascii_case("f3d") && !ext.eq_ignore_ascii_case("f3z") {
        return Err("expected a .f3d or .f3z file".into());
    }
    let result = F3dCodec.decode(&mut File::open(path)?, &DecodeOptions::default())?;
    let model = &result.ir().model;
    let definitions = serde_json::to_value(&model.product_definitions)?;
    let sketches = serde_json::to_value(&model.sketches)?;
    let mut warnings: Vec<String> = result
        .report()
        .losses
        .iter()
        .map(|loss| format!("{:?}: {}", loss.severity, loss.message))
        .collect();
    warnings.push("IDs are decoder identities and are not guaranteed durable across decoder versions. Decoded data may be incomplete.".into());
    if ext.eq_ignore_ascii_case("f3z") {
        warnings.push("F3Z decoding merges documents; document identity is not preserved.".into());
    }
    let mut output = serde_json::json!({"schema_version": 1, "warnings": warnings});
    match kind {
        "components" => {
            output["components"] = definitions;
            output["occurrences"] = serde_json::to_value(&model.occurrences)?;
        }
        "sketches" => {
            let selected = if let Some(id) = component {
                let definition = definitions
                    .as_array()
                    .unwrap()
                    .iter()
                    .find(|d| d["id"].as_str() == Some(id))
                    .ok_or_else(|| format!("component {id:?} not found"))?;
                let owned = definition.get("sketches").and_then(|v| v.as_array());
                sketches
                    .as_array()
                    .unwrap()
                    .iter()
                    .filter(|s| owned.is_some_and(|ids| ids.contains(&s["id"])))
                    .cloned()
                    .collect::<Vec<_>>()
            } else {
                sketches.as_array().unwrap().clone()
            };
            output["sketches"] = serde_json::to_value(selected)?;
            output["component_filter"] = serde_json::to_value(component)?;
        }
        _ => return Err("unknown query".into()),
    }
    Ok(output)
}

#[derive(Debug, Serialize)]
pub struct Structure {
    pub schema_version: u32,
    pub component_definitions: usize,
    pub occurrences: usize,
    pub top_level_occurrences: usize,
    pub bodies: usize,
    pub sketches: usize,
    pub warnings: Vec<String>,
}

pub fn inspect(path: &Path) -> Result<Structure, Box<dyn Error>> {
    let ext = path.extension().and_then(|x| x.to_str()).unwrap_or("");
    if !ext.eq_ignore_ascii_case("f3d") && !ext.eq_ignore_ascii_case("f3z") {
        return Err("expected a .f3d or .f3z file".into());
    }
    let mut file = File::open(path)?;
    let result = F3dCodec.decode(&mut file, &DecodeOptions::default())?;
    let model = &result.ir().model;
    let mut warnings: Vec<String> = result
        .report()
        .losses
        .iter()
        .map(|loss| format!("{:?}: {}", loss.severity, loss.message))
        .collect();
    if ext.eq_ignore_ascii_case("f3z") {
        warnings.push(
            "F3Z decoding merges documents; these counts do not preserve document identity.".into(),
        );
    }
    warnings.push("Counts describe decoded entities; top-level occurrences do not include all possible root objects. Missing or unsupported source data may affect counts.".into());
    Ok(Structure {
        schema_version: 1,
        component_definitions: model.product_definitions.len(),
        occurrences: model.occurrences.len(),
        top_level_occurrences: model
            .occurrences
            .iter()
            .filter(|o| matches!(o.parent, OccurrenceParent::Root {}))
            .count(),
        bodies: model.bodies.len(),
        sketches: model.sketches.len(),
        warnings,
    })
}

/// One decoder diagnostic. Numbers are positions in this decode report, not durable IDs.
#[derive(Debug, Serialize)]
pub struct Diagnostic {
    pub number: usize,
    pub source: &'static str,
    pub code: String,
    pub severity: String,
    pub message: String,
    pub provenance: Option<serde_json::Value>,
    pub explanation: Option<&'static str>,
}

fn explanation(code: &str) -> Option<&'static str> {
    if code == "f3d/sketch.name-composed-from-feature-ordinal"
        || code == "sketch.name-composed-from-feature-ordinal"
    {
        Some(
            "cadmpeg could not use a stored sketch display name for these sketches and assigned a name derived from the associated feature kind and ordinal. The name may differ from a name shown in Fusion, especially if it was renamed. Compare the sketch names in Fusion before relying on them; the warning alone does not establish a geometry or constraint error.",
        )
    } else {
        None
    }
}

/// Decode diagnostics without modifying the source file.
pub fn diagnostics(path: &Path) -> Result<Vec<Diagnostic>, Box<dyn Error>> {
    let ext = path.extension().and_then(|x| x.to_str()).unwrap_or("");
    if !ext.eq_ignore_ascii_case("f3d") && !ext.eq_ignore_ascii_case("f3z") {
        return Err("expected a .f3d or .f3z file".into());
    }
    let mut file = File::open(path)?;
    let result = F3dCodec.decode(&mut file, &DecodeOptions::default())?;
    result
        .report()
        .losses
        .iter()
        .enumerate()
        .map(|(index, loss)| {
            let code = loss.code.to_string();
            Ok(Diagnostic {
                number: index + 1,
                source: "cadmpeg-codec-f3d 0.6.12",
                explanation: explanation(&code),
                code,
                severity: format!("{:?}", loss.severity),
                message: loss.message.clone(),
                provenance: loss
                    .provenance
                    .as_ref()
                    .map(serde_json::to_value)
                    .transpose()?,
            })
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::explanation;

    #[test]
    fn sketch_name_code_has_explanation() {
        assert!(
            explanation("f3d/sketch.name-composed-from-feature-ordinal")
                .unwrap()
                .contains("display name")
        );
        assert!(explanation("f3d/unknown").is_none());
    }
}
