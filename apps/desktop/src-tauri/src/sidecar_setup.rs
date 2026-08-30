use std::io::Write;
use std::path::Path;
use std::process::Command;
use std::sync::Mutex;

use futures_util::StreamExt;
use serde::Serialize;
use sha2::{Digest, Sha256};
use sysinfo::Disks;
use tauri::{AppHandle, Emitter, Manager};

/// Where the split, gzipped `_internal` archive lives. Uploaded once via
/// the release process documented in docs/SIDECAR_RUNTIME_RELEASE.md -
/// bump RELEASE_TAG and the PARTS table together if the backend build
/// (and therefore _internal) ever changes.
const RELEASE_TAG: &str = "sidecar-runtime-v1";
const RELEASE_BASE: &str = "https://github.com/nithish0302/JARVIS/releases/download";

struct PartSpec {
    name: &'static str,
    sha256: &'static str,
    size: u64,
}

// Filled in from the actual upload - see docs/SIDECAR_RUNTIME_RELEASE.md
const PARTS: &[PartSpec] = &[
    PartSpec {
        name: "internal.tar.gz.part_aa",
        sha256: "a5bba4c522c854cc33e52ce5f85074598a3b61c44216a095880b4c30844986dc",
        size: 1_992_294_400,
    },
    PartSpec {
        name: "internal.tar.gz.part_ab",
        sha256: "27656f00bf7f46c40aaa325af05967c80f3515ada47f195c80f7ae611b0156d8",
        size: 283_638_255,
    },
];

/// Sanity thresholds for the extracted result - not exact equality,
/// since file counts can drift slightly across builds without anything
/// being wrong. Anything drastically short of these means a partial or
/// corrupted extraction slipped past the per-part checksum check.
const EXPECTED_FILE_COUNT: usize = 19571;
const EXPECTED_TOTAL_SIZE_BYTES: u64 = 3_748_643_176;

/// Extracted _internal is ~3.7GB; the tar.gz plus its parts sit
/// alongside it briefly during setup, so require roughly 2.5x that as a
/// safety margin rather than cutting it close.
const MIN_FREE_SPACE_BYTES: u64 = 10 * 1024 * 1024 * 1024;

#[derive(Clone, Serialize)]
pub struct SetupProgress {
    pub stage: String, // "idle" | "checking" | "downloading" | "extracting" | "verifying" | "done" | "error"
    pub percent: f64,
    pub message: String,
}

impl Default for SetupProgress {
    fn default() -> Self {
        Self { stage: "idle".into(), percent: 0.0, message: String::new() }
    }
}

pub struct SetupState(pub Mutex<SetupProgress>);

fn emit_progress(app: &AppHandle, stage: &str, percent: f64, message: impl Into<String>) {
    let progress = SetupProgress { stage: stage.into(), percent, message: message.into() };
    if let Some(state) = app.try_state::<SetupState>() {
        *state.0.lock().unwrap() = SetupProgress {
            stage: progress.stage.clone(),
            percent: progress.percent,
            message: progress.message.clone(),
        };
    }
    let _ = app.emit("sidecar-setup-progress", progress);
}

fn count_files(dir: &Path) -> usize {
    let mut count = 0;
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            if let Ok(ft) = entry.file_type() {
                if ft.is_dir() {
                    count += count_files(&entry.path());
                } else {
                    count += 1;
                }
            }
        }
    }
    count
}

fn dir_size(dir: &Path) -> u64 {
    let mut total = 0u64;
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            if let Ok(ft) = entry.file_type() {
                if ft.is_dir() {
                    total += dir_size(&entry.path());
                } else if let Ok(meta) = entry.metadata() {
                    total += meta.len();
                }
            }
        }
    }
    total
}

fn check_disk_space(exe_dir: &Path) -> Result<(), String> {
    let disks = Disks::new_with_refreshed_list();
    let avail = disks
        .list()
        .iter()
        .filter(|d| exe_dir.starts_with(d.mount_point()))
        .max_by_key(|d| d.mount_point().as_os_str().len())
        .map(|d| d.available_space());

    if let Some(avail) = avail {
        if avail < MIN_FREE_SPACE_BYTES {
            return Err(format!(
                "Not enough free disk space to set up JARVIS: {:.1} GB available, at least {:.0} GB required. Free up space, then click Retry.",
                avail as f64 / 1_073_741_824.0,
                MIN_FREE_SPACE_BYTES as f64 / 1_073_741_824.0
            ));
        }
    }
    Ok(())
}

/// Downloads every part in `PARTS`, verifying each part's sha256 as it
/// streams, concatenating into one tar.gz alongside the sidecar exe,
/// extracts it with the system `tar` (bundled in Windows since 10
/// 1803, no extra dependency needed), then sanity-checks the result
/// before declaring success. Any failure leaves `dest` absent so the
/// next launch (or a Retry click) starts over cleanly instead of
/// resuming into a possibly-corrupt half-state.
async fn download_and_extract(app: &AppHandle, exe_dir: &Path, dest: &Path) -> Result<(), String> {
    emit_progress(app, "checking", 0.0, "Checking disk space...");
    check_disk_space(exe_dir)?;

    let tmp_dir = exe_dir.join("_setup_tmp");
    let _ = std::fs::remove_dir_all(&tmp_dir);
    std::fs::create_dir_all(&tmp_dir).map_err(|e| format!("Could not create temp directory: {e}"))?;

    let client = reqwest::Client::builder()
        .build()
        .map_err(|e| format!("Could not initialize HTTP client: {e}"))?;

    let total_bytes: u64 = PARTS.iter().map(|p| p.size).sum();
    let mut downloaded_so_far: u64 = 0;

    let concat_path = tmp_dir.join("internal.tar.gz");
    let mut concat_file = std::fs::File::create(&concat_path)
        .map_err(|e| format!("Could not create archive file: {e}"))?;

    for part in PARTS {
        let url = format!("{RELEASE_BASE}/{RELEASE_TAG}/{}", part.name);
        emit_progress(
            app,
            "downloading",
            if total_bytes > 0 { downloaded_so_far as f64 / total_bytes as f64 * 100.0 } else { 0.0 },
            "Downloading JARVIS engine components...",
        );

        let resp = client.get(&url).send().await.map_err(|e| {
            format!("Network error while downloading engine components ({e}). Check your connection and click Retry.")
        })?;
        if !resp.status().is_success() {
            return Err(format!(
                "Download failed for {} (HTTP {}). Click Retry to try again.",
                part.name,
                resp.status()
            ));
        }

        let mut hasher = Sha256::new();
        let mut stream = resp.bytes_stream();
        let mut last_emit = std::time::Instant::now();
        while let Some(chunk) = stream.next().await {
            let chunk = chunk.map_err(|e| {
                format!("Download was interrupted ({e}). Click Retry to resume setup.")
            })?;
            concat_file
                .write_all(&chunk)
                .map_err(|e| format!("Could not write downloaded data to disk: {e}"))?;
            hasher.update(&chunk);
            downloaded_so_far += chunk.len() as u64;

            if last_emit.elapsed().as_millis() > 200 {
                let pct = if total_bytes > 0 { downloaded_so_far as f64 / total_bytes as f64 * 100.0 } else { 0.0 };
                emit_progress(
                    app,
                    "downloading",
                    pct,
                    format!("Downloading JARVIS engine components... {:.0}%", pct),
                );
                last_emit = std::time::Instant::now();
            }
        }

        let digest = hex::encode(hasher.finalize());
        if digest != part.sha256 {
            let _ = std::fs::remove_dir_all(&tmp_dir);
            return Err(format!(
                "Downloaded file {} is corrupted (checksum mismatch). Click Retry to download again.",
                part.name
            ));
        }
    }
    drop(concat_file);

    emit_progress(app, "extracting", 0.0, "Extracting JARVIS engine components...");
    let status = Command::new("tar")
        .arg("-xzf")
        .arg(&concat_path)
        .arg("-C")
        .arg(exe_dir)
        .status()
        .map_err(|e| format!("Could not run tar to extract the downloaded archive: {e}"))?;
    if !status.success() {
        let _ = std::fs::remove_dir_all(&tmp_dir);
        let _ = std::fs::remove_dir_all(dest);
        return Err("Extraction failed - the downloaded archive may be corrupted. Click Retry.".to_string());
    }

    emit_progress(app, "verifying", 50.0, "Verifying installation...");
    if !dest.exists() {
        return Err("Extraction did not produce the expected engine files. Click Retry.".to_string());
    }
    let file_count = count_files(dest);
    let min_expected_files = EXPECTED_FILE_COUNT * 9 / 10;
    if EXPECTED_FILE_COUNT > 0 && file_count < min_expected_files {
        let _ = std::fs::remove_dir_all(dest);
        return Err(format!(
            "Extracted engine files look incomplete ({} of ~{} expected files). Click Retry.",
            file_count, EXPECTED_FILE_COUNT
        ));
    }
    let extracted_size = dir_size(dest);
    let min_expected_size = EXPECTED_TOTAL_SIZE_BYTES * 9 / 10;
    if EXPECTED_TOTAL_SIZE_BYTES > 0 && extracted_size < min_expected_size {
        let _ = std::fs::remove_dir_all(dest);
        return Err(format!(
            "Extracted engine files look incomplete ({:.1} GB of ~{:.1} GB expected). Click Retry.",
            extracted_size as f64 / 1_073_741_824.0,
            EXPECTED_TOTAL_SIZE_BYTES as f64 / 1_073_741_824.0
        ));
    }

    let _ = std::fs::remove_dir_all(&tmp_dir);
    Ok(())
}

/// PyInstaller's onedir build needs its `_internal` support directory
/// physically next to the sidecar .exe. Older builds bundled it as a
/// Tauri resource and this just copied it into place; that made the
/// installer itself ~3.7GB. It's no longer bundled - instead this
/// downloads it from a GitHub Release the first time the app runs (see
/// docs/SIDECAR_RUNTIME_RELEASE.md), and skips straight past on every
/// later launch once `_internal` exists on disk.
pub async fn ensure_sidecar_internal_dir(app: &AppHandle) -> bool {
    let Ok(current_exe) = std::env::current_exe() else {
        emit_progress(app, "error", 0.0, "Could not resolve the app's own install location.");
        return false;
    };
    let Some(exe_dir) = current_exe.parent() else {
        emit_progress(app, "error", 0.0, "Could not resolve the app's own install location.");
        return false;
    };
    let dest = exe_dir.join("_internal");
    if dest.exists() {
        emit_progress(app, "done", 100.0, "Ready");
        return true;
    }

    // Legacy/dev fallback: still honor a bundled resource copy if one is
    // present, so `pnpm tauri dev` / older builds keep working unchanged.
    if let Ok(resource_dir) = app.path().resource_dir() {
        let src = resource_dir.join("_internal");
        if src.exists() {
            emit_progress(app, "extracting", 0.0, "Staging backend runtime files...");
            if crate::copy_dir_recursive(&src, &dest).is_ok() {
                emit_progress(app, "done", 100.0, "Ready");
                return true;
            }
        }
    }

    println!("[SIDECAR] _internal not found - downloading engine runtime from GitHub Release {RELEASE_TAG}");
    match download_and_extract(app, exe_dir, &dest).await {
        Ok(()) => {
            emit_progress(app, "done", 100.0, "Ready");
            true
        }
        Err(e) => {
            eprintln!("[SIDECAR] Engine runtime setup failed: {e}");
            emit_progress(app, "error", 0.0, e);
            false
        }
    }
}

#[tauri::command]
pub fn get_sidecar_setup_status(state: tauri::State<SetupState>) -> SetupProgress {
    let guard = state.0.lock().unwrap();
    SetupProgress { stage: guard.stage.clone(), percent: guard.percent, message: guard.message.clone() }
}

#[tauri::command]
pub async fn retry_sidecar_setup(app: AppHandle) -> Result<(), String> {
    crate::spawn_engine_sidecar(&app).await;
    Ok(())
}
