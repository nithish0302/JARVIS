use std::sync::Mutex;
use sysinfo::{Disks, System};
use std::process::Command;
use std::path::Path;
use std::fs;
use std::net::TcpStream;
use std::time::Duration;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;
use tauri::Manager;

mod sidecar_setup;
use sidecar_setup::SetupState;

pub struct SysState(pub Mutex<System>);

/// Holds the child handle for the bundled Python backend sidecar, if this
/// instance is the one that launched it. `None` either means the sidecar
/// hasn't been spawned yet, or the backend was already reachable at
/// startup (e.g. `pnpm tauri dev` next to a manually-run `uv run start.py`)
/// so we deliberately did not spawn a second copy - nothing for shutdown
/// to kill in that case.
pub struct EngineProcess(pub Mutex<Option<CommandChild>>);

const ENGINE_HOST: &str = "127.0.0.1";
const ENGINE_PORT: u16 = 8765;

fn engine_already_running() -> bool {
  TcpStream::connect_timeout(
    &format!("{}:{}", ENGINE_HOST, ENGINE_PORT).parse().unwrap(),
    Duration::from_millis(300),
  )
  .is_ok()
}

/// Prepares `<app-data-dir>/` as the sidecar's working directory and seeds
/// it with the wake-word model, then returns that directory.
///
/// The backend's config (jarvis_engine/core/config.py) resolves DB_PATH,
/// CHROMA_PATH, and WAKE_WORD_MODEL_PATH as paths RELATIVE to the
/// process's cwd - correct for the dev workflow (always run from
/// services/jarvis-engine/), meaningless for a frozen sidecar exe, whose
/// own directory is a temp install path with no writable model/data
/// layout of its own. Anchoring cwd here instead gives every install a
/// stable, writable, per-user location - %APPDATA%\com.nithish.jarvis\ -
/// that survives updates and reinstalls the same way whether the DB
/// already exists there or is created fresh.
fn prepare_engine_data_dir(app: &tauri::AppHandle) -> Option<std::path::PathBuf> {
  let data_dir = app.path().app_data_dir().ok()?;
  let models_dir = data_dir.join("models");
  if let Err(e) = fs::create_dir_all(&models_dir) {
    eprintln!("[SIDECAR] Could not create {:?}: {}", models_dir, e);
    return None;
  }

  let dest_model = models_dir.join("wake_up_jarvis.onnx");
  if !dest_model.exists() {
    if let Ok(resource_dir) = app.path().resource_dir() {
      let bundled_model = resource_dir.join("models").join("wake_up_jarvis.onnx");
      if bundled_model.exists() {
        if let Err(e) = fs::copy(&bundled_model, &dest_model) {
          eprintln!("[SIDECAR] Could not seed wake-word model: {}", e);
        } else {
          println!("[SIDECAR] Seeded wake-word model into {:?}", dest_model);
        }
      } else {
        eprintln!("[SIDECAR] Bundled wake-word model not found at {:?} - voice wake detection will be unavailable until one is placed at {:?}", bundled_model, dest_model);
      }
    }
  }

  Some(data_dir)
}

/// Recursively copies a directory. std::fs has no built-in for this.
pub(crate) fn copy_dir_recursive(src: &Path, dst: &Path) -> std::io::Result<()> {
  fs::create_dir_all(dst)?;
  for entry in fs::read_dir(src)? {
    let entry = entry?;
    let file_type = entry.file_type()?;
    let dest_path = dst.join(entry.file_name());
    if file_type.is_dir() {
      copy_dir_recursive(&entry.path(), &dest_path)?;
    } else {
      fs::copy(entry.path(), &dest_path)?;
    }
  }
  Ok(())
}

/// Spawns the bundled `jarvis-engine` sidecar unless something is already
/// listening on the engine port. Drains its stdout/stderr in a background
/// task so the child's output pipes never fill up and block it, and logs
/// enough to diagnose a startup failure without a console window.
///
/// `_internal` (PyInstaller's onedir support directory, needed physically
/// next to the sidecar .exe) is no longer bundled into the installer -
/// see sidecar_setup.rs for why and how it's fetched from a GitHub
/// Release on first run instead. If that setup fails, this bails out
/// without spawning the sidecar; the frontend shows the error and a
/// Retry button (see useSidecarSetup.ts) instead of a silently-broken
/// "JARVIS engine not running" state.
pub(crate) async fn spawn_engine_sidecar(app: &tauri::AppHandle) {
  if engine_already_running() {
    println!("[SIDECAR] Engine already reachable on {}:{} - not spawning a second copy", ENGINE_HOST, ENGINE_PORT);
    return;
  }

  if !sidecar_setup::ensure_sidecar_internal_dir(app).await {
    return;
  }

  let sidecar = match app.shell().sidecar("jarvis-engine") {
    Ok(cmd) => cmd,
    Err(e) => {
      eprintln!("[SIDECAR] Could not resolve jarvis-engine sidecar binary: {}", e);
      return;
    }
  };

  let sidecar = match prepare_engine_data_dir(app) {
    Some(data_dir) => sidecar.current_dir(data_dir),
    None => {
      eprintln!("[SIDECAR] Could not resolve app data dir - launching with default cwd");
      sidecar
    }
  };

  match sidecar.spawn() {
    Ok((mut rx, child)) => {
      println!("[SIDECAR] jarvis-engine started (pid {})", child.pid());
      if let Some(state) = app.try_state::<EngineProcess>() {
        *state.0.lock().unwrap() = Some(child);
      }
      tauri::async_runtime::spawn(async move {
        use tauri_plugin_shell::process::CommandEvent;
        while let Some(event) = rx.recv().await {
          match event {
            CommandEvent::Stdout(line) => {
              print!("[jarvis-engine] {}", String::from_utf8_lossy(&line));
            }
            CommandEvent::Stderr(line) => {
              eprint!("[jarvis-engine] {}", String::from_utf8_lossy(&line));
            }
            CommandEvent::Error(err) => {
              eprintln!("[jarvis-engine] process error: {}", err);
            }
            CommandEvent::Terminated(payload) => {
              println!("[jarvis-engine] exited: {:?}", payload);
              break;
            }
            _ => {}
          }
        }
      });
    }
    Err(e) => {
      eprintln!("[SIDECAR] Failed to spawn jarvis-engine: {}", e);
    }
  }
}

/// Kills the sidecar we launched, if any. Called on app exit so the
/// backend never survives the window closing as an orphaned process.
fn kill_engine_sidecar(app: &tauri::AppHandle) {
  if let Some(state) = app.try_state::<EngineProcess>() {
    if let Some(child) = state.0.lock().unwrap().take() {
      println!("[SIDECAR] Terminating jarvis-engine (pid {})", child.pid());
      if let Err(e) = child.kill() {
        eprintln!("[SIDECAR] Failed to kill jarvis-engine: {}", e);
      }
    }
  }
}

#[tauri::command]
fn get_system_info(state: tauri::State<SysState>) -> serde_json::Value {
    let mut sys = match state.0.lock() {
        Ok(guard) => guard,
        Err(poisoned) => {
            eprintln!("Mutex poisoned, recovering");
            poisoned.into_inner()
        }
    };
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let total_mem = sys.total_memory();
    let used_mem = sys.used_memory();
    let ram_pct = if total_mem > 0 {
        (used_mem as f64 / total_mem as f64 * 100.0)
            .min(100.0)
            .max(0.0) as u32
    } else {
        0
    };
    
    // Get CPU name
    let cpu_name = sys.cpus()
        .first()
        .map(|c| c.brand().to_string())
        .unwrap_or("Unknown CPU".to_string());

    let cpu_cores = sys.cpus().len();

    serde_json::json!({
        "cpu_usage": cpu_usage as u32,
        "cpu_name": cpu_name,
        "cpu_cores": cpu_cores,
        "ram_pct": ram_pct,
        "ram_used_gb": format!("{:.1}", used_mem as f64 / 1_073_741_824.0),
        "ram_total_gb": format!("{:.0}", total_mem as f64 / 1_073_741_824.0),
        "gpus": serde_json::json!([
            {
                "name": "GTX 1650",
                "type": "discrete",
                "usage": 0,
                "static": true
            },
            {
                "name": "Intel Iris Xe",
                "type": "integrated",
                "usage": 0,
                "static": true
            }
        ])
    })
}

const FIND_APP_SCRIPT: &str = include_str!("../scripts/find_application.ps1");

fn get_find_app_script_path() -> std::path::PathBuf {
  let candidates = [
    std::path::PathBuf::from("scripts/find_application.ps1"),
    std::path::PathBuf::from("src-tauri/scripts/find_application.ps1"),
    std::path::PathBuf::from("../src-tauri/scripts/find_application.ps1"),
  ];
  for c in &candidates {
    if c.exists() {
      if let Ok(abs) = std::fs::canonicalize(c) {
        return abs;
      }
      return c.clone();
    }
  }
  let temp_path = std::env::temp_dir().join("jarvis_find_application.ps1");
  if !temp_path.exists() {
    let _ = std::fs::write(&temp_path, FIND_APP_SCRIPT);
  }
  temp_path
}

// 1. FIND ANY INSTALLED APPLICATION
// Searches Windows registry + common paths
#[tauri::command]
fn find_application(app_name: String) 
  -> Result<String, String> {
  
  let name_lower = app_name.to_lowercase();
  
  // Common Windows apps (fast lookup)
  let common_apps: Vec<(&str, &str)> = vec![
    ("chrome", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
    ("firefox", "C:\\Program Files\\Mozilla Firefox\\firefox.exe"),
    ("edge", "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"),
    ("notepad", "notepad.exe"),
    ("calculator", "calc.exe"),
    ("explorer", "explorer.exe"),
    ("cmd", "cmd.exe"),
    ("powershell", "powershell.exe"),
    ("taskmgr", "taskmgr.exe"),
    ("mspaint", "mspaint.exe"),
    ("wordpad", "wordpad.exe"),
    ("vscode", "code"),
    ("vs code", "code"),
    ("visual studio code", "code"),
    ("spotify", "C:\\Users\\{}\\AppData\\Roaming\\Spotify\\Spotify.exe"),
    ("discord", "C:\\Users\\{}\\AppData\\Local\\Discord\\Update.exe"),
    ("telegram", "C:\\Users\\{}\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe"),
    ("whatsapp", "C:\\Users\\{}\\AppData\\Local\\WhatsApp\\WhatsApp.exe"),
    ("vlc", "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"),
    ("vlc_x86", "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe"),
    ("steam", "C:\\Program Files (x86)\\Steam\\steam.exe"),
    ("obs", "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe"),
    ("postman", "C:\\Users\\{}\\AppData\\Local\\Postman\\Postman.exe"),
  ];
  
  // Get current username
  let username = std::env::var("USERNAME")
    .unwrap_or_default();
  
  for (key, path) in &common_apps {
    if name_lower.contains(key) {
      let resolved = path.replace("{}", &username);
      if Path::new(&resolved).exists() 
        || !resolved.contains('\\') {
        return Ok(resolved);
      }
    }
  }
  
  // Search using bundled PowerShell script with parameterized input
  let script_path = get_find_app_script_path();
  let output = Command::new("powershell")
    .args([
      "-NoProfile",
      "-NonInteractive",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
    ])
    .arg(&script_path)
    .arg(&app_name)
    .output();
  
  if let Ok(out) = output {
    let result_path = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if !result_path.is_empty() {
      if result_path.starts_with("shell:appsFolder") || Path::new(&result_path).exists() {
        return Ok(result_path);
      }
    }
  }
  
  Err(format!("Could not find: {}", app_name))
}

// 2. OPEN ANY APPLICATION DYNAMICALLY
#[tauri::command]
fn open_application(app_name: String) 
  -> Result<String, String> {
  
  // First try to find the app
  let path = match find_application(
    app_name.clone()
  ) {
    Ok(p) => p,
    Err(_) => app_name.clone()
  };
  
  // Handle Windows Store apps
  if path.starts_with("shell:appsFolder") {
    return match Command::new("explorer")
      .arg(&path)
      .spawn() {
        Ok(_) => Ok(format!(
          "Opened {}, sir.", app_name
        )),
        Err(e) => Err(format!("Failed: {}", e))
      };
  }
  
  // Handle URLs
  if path.starts_with("http") || 
     path.starts_with("ms-settings") {
    return match open::that(&path) {
      Ok(_) => Ok(format!("Opened {}, sir.", app_name)),
      Err(e) => Err(format!("Failed: {}", e))
    };
  }
  
  // Direct execution
  match Command::new(&path).spawn() {
    Ok(_) => Ok(format!("Opened {}, sir.", app_name)),
    Err(_) => {
      // Try via cmd start
      match Command::new("cmd")
        .args(["/C", "start", "", &path])
        .spawn() {
          Ok(_) => Ok(format!(
            "Opened {}, sir.", app_name
          )),
          Err(e) => Err(format!(
            "Could not open {}: {}", app_name, e
          ))
        }
    }
  }
}

#[derive(Debug, serde::Serialize, serde::Deserialize, PartialEq, Eq, Clone, Copy)]
#[serde(rename_all = "snake_case")]
pub enum SystemQuery {
    IpAddress,
    BatteryLevel,
    DiskSpace,
    TopProcesses,
    Uptime,
}

#[derive(Debug, serde::Serialize, serde::Deserialize, Default)]
pub struct QueryParams {
    pub count: Option<u8>,
}

#[tauri::command]
fn run_system_query(
    state: tauri::State<SysState>,
    query: SystemQuery,
    params: Option<QueryParams>,
) -> Result<String, String> {
    run_system_query_impl(&state, query, params)
}

pub fn run_system_query_impl(
    state: &SysState,
    query: SystemQuery,
    params: Option<QueryParams>,
) -> Result<String, String> {
    match query {
        SystemQuery::IpAddress => {
            // Safe in-process local address resolution
            if let Ok(socket) = std::net::UdpSocket::bind("0.0.0.0:0") {
                if socket.connect("8.8.8.8:80").is_ok() {
                    if let Ok(addr) = socket.local_addr() {
                        let ip = addr.ip().to_string();
                        if !ip.starts_with("127.") && !ip.is_empty() {
                            return Ok(format!("IP Address: {}", ip));
                        }
                    }
                }
            }
            // Fallback to fixed, static, zero-parameter PowerShell script
            let out = Command::new("powershell")
                .args([
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | Select-Object -First 1).IPAddress",
                ])
                .output()
                .map_err(|e| format!("IP query failed: {}", e))?;
            let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
            if !stdout.is_empty() {
                Ok(format!("IP Address: {}", stdout))
            } else {
                Err("Could not retrieve IP address".to_string())
            }
        }
        SystemQuery::BatteryLevel => {
            let manager = battery::Manager::new()
                .map_err(|e| format!("Battery query failed: {}", e))?;
            let mut batteries = manager.batteries()
                .map_err(|e| format!("Battery query failed: {}", e))?;
            match batteries.next() {
                Some(Ok(bat)) => {
                    let level = (bat.state_of_charge().value * 100.0).round() as u64;
                    let status = match bat.state() {
                        battery::State::Charging => "Charging",
                        battery::State::Full => "Fully Charged",
                        battery::State::Discharging => "Discharging (On Battery)",
                        _ => "Plugged in",
                    };
                    Ok(format!("Battery: {}% ({})", level, status))
                }
                _ => Ok("Battery: 100% (Desktop PC - AC Power)".to_string()),
            }
        }
        SystemQuery::DiskSpace => {
            let disks = Disks::new_with_refreshed_list();
            let target = disks.list().iter()
                .find(|d| d.mount_point() == Path::new("C:\\"))
                .or_else(|| disks.list().first());

            match target {
                Some(d) => {
                    let total = d.total_space();
                    let available = d.available_space();
                    let used = total.saturating_sub(available);
                    let pct = if total > 0 { (used as f64 / total as f64 * 100.0) as u32 } else { 0 };
                    let used_gb = used as f64 / 1_073_741_824.0;
                    let total_gb = total as f64 / 1_073_741_824.0;
                    let free_gb = available as f64 / 1_073_741_824.0;
                    Ok(format!(
                        "Disk (C:): {:.0} GB used / {:.0} GB total ({:.0} GB free, {}% used)",
                        used_gb, total_gb, free_gb, pct
                    ))
                }
                None => Err("No storage disks detected".to_string()),
            }
        }
        SystemQuery::TopProcesses => {
            let limit = params.and_then(|p| p.count).unwrap_or(5).clamp(1, 20) as usize;
            let mut sys = match state.0.lock() {
                Ok(guard) => guard,
                Err(poisoned) => poisoned.into_inner(),
            };
            sys.refresh_processes();

            let mut processes: Vec<_> = sys.processes().values().collect();
            processes.sort_by(|a, b| b.cpu_usage().partial_cmp(&a.cpu_usage()).unwrap_or(std::cmp::Ordering::Equal));

            let mut lines = vec![format!("Top {} CPU Processes:", limit.min(processes.len()))];
            for (i, p) in processes.iter().take(limit).enumerate() {
                let mem_mb = p.memory() as f64 / 1_048_576.0;
                lines.push(format!("{}. {} (PID {}) - {:.1}% CPU, {:.0} MB RAM", i + 1, p.name(), p.pid(), p.cpu_usage(), mem_mb));
            }
            Ok(lines.join("\n"))
        }
        SystemQuery::Uptime => {
            let uptime_secs = System::uptime();
            let days = uptime_secs / 86400;
            let hours = (uptime_secs % 86400) / 3600;
            let minutes = (uptime_secs % 3600) / 60;
            if days > 0 {
                Ok(format!("System Uptime: {} days, {} hours, {} minutes", days, hours, minutes))
            } else if hours > 0 {
                Ok(format!("System Uptime: {} hours, {} minutes", hours, minutes))
            } else {
                Ok(format!("System Uptime: {} minutes", minutes))
            }
        }
    }
}

// Close an application natively
#[tauri::command]
fn close_application(state: tauri::State<SysState>, app_name: String) -> Result<String, String> {
    close_application_impl(&state, app_name)
}

pub fn close_application_impl(state: &SysState, app_name: String) -> Result<String, String> {
    let clean_name = app_name.trim().to_lowercase();
    if clean_name.is_empty() {
        return Err("Application name is required".to_string());
    }
    // Validation: only allow standard executable / application names
    if !clean_name.chars().all(|c| c.is_alphanumeric() || c == ' ' || c == '-' || c == '_' || c == '.') {
        return Err("Invalid application name format".to_string());
    }
    
    let mut sys = match state.0.lock() {
        Ok(g) => g,
        Err(p) => p.into_inner(),
    };
    sys.refresh_processes();
    
    let target = clean_name.replace(".exe", "");
    let mut killed_count = 0;
    for (_pid, proc) in sys.processes() {
        let proc_name = proc.name().to_lowercase().replace(".exe", "");
        if proc_name == target || proc_name.contains(&target) {
            proc.kill();
            killed_count += 1;
        }
    }
    
    if killed_count > 0 {
        Ok(format!("Closed {} ({} process(es) terminated), sir.", app_name, killed_count))
    } else {
        // Fallback to taskkill with direct safe parameter binding (no shell interpolation)
        let exe_target = if clean_name.ends_with(".exe") { clean_name } else { format!("{}.exe", clean_name) };
        match Command::new("taskkill").args(["/IM", &exe_target, "/T", "/F"]).output() {
            Ok(out) if out.status.success() => Ok(format!("Closed {}, sir.", app_name)),
            _ => Err(format!("Could not find any running process for '{}', sir.", app_name)),
        }
    }
}

// Adjust volume natively via Windows media key simulation
#[tauri::command]
fn set_volume(action: String) -> Result<String, String> {
    let act = action.trim().to_lowercase();
    match act.as_str() {
        "up" => {
            #[cfg(target_os = "windows")]
            simulate_volume_key(0xAF); // VK_VOLUME_UP
            Ok("Volume increased, sir.".to_string())
        }
        "down" => {
            #[cfg(target_os = "windows")]
            simulate_volume_key(0xAE); // VK_VOLUME_DOWN
            Ok("Volume decreased, sir.".to_string())
        }
        "mute" | "unmute" => {
            #[cfg(target_os = "windows")]
            simulate_volume_key(0xAD); // VK_VOLUME_MUTE
            Ok("Volume mute toggled, sir.".to_string())
        }
        _ => Err(format!("Unknown volume action '{}'. Use 'up', 'down', or 'mute'.", action)),
    }
}

#[cfg(target_os = "windows")]
fn simulate_volume_key(vk: u8) {
    #[link(name = "user32")]
    extern "system" {
        fn keybd_event(b_vk: u8, b_scan: u8, dw_flags: u32, dw_extra_info: usize);
    }
    unsafe {
        keybd_event(vk, 0, 0, 0); // KEYEVENTF_KEYDOWN
        keybd_event(vk, 0, 2, 0); // KEYEVENTF_KEYUP
    }
}

// 4. LOCK SCREEN
#[tauri::command]
fn lock_screen() -> Result<String, String> {
  match Command::new("rundll32.exe")
    .args(["user32.dll,LockWorkStation"])
    .spawn() {
      Ok(_) => Ok("Screen locked, sir.".to_string()),
      Err(e) => Err(format!("Lock failed: {}", e))
    }
}

// 5. GET BATTERY INFO (real)
// In-process via the `battery` crate (Windows: WMI COM calls, no
// powershell.exe spawn) instead of shelling out to PowerShell.
#[tauri::command]
fn get_battery_info()
  -> Result<serde_json::Value, String> {
  let manager = battery::Manager::new()
    .map_err(|e| format!("Battery manager init failed: {}", e))?;

  let mut batteries = manager.batteries()
    .map_err(|e| format!("Battery query failed: {}", e))?;

  match batteries.next() {
    Some(Ok(bat)) => {
      let level = (bat.state_of_charge().value * 100.0).round() as u64;
      let charging = matches!(
        bat.state(),
        battery::State::Charging | battery::State::Full
      );

      Ok(serde_json::json!({
        "level": level,
        "charging": charging,
        "has_battery": true,
        "status": if charging {
          "Charging"
        } else {
          "On Battery"
        }
      }))
    }
    _ => Ok(serde_json::json!({
      "level": 100,
      "charging": true,
      "has_battery": false,
      "status": "Desktop - No battery"
    }))
  }
}

// 6. GET REAL DISK INFO
// In-process via sysinfo's Disks API - no powershell.exe spawn.
#[tauri::command]
fn get_disk_info()
  -> Result<serde_json::Value, String> {
  let disks = Disks::new_with_refreshed_list();

  let target = disks.list().iter()
    .find(|d| d.mount_point() == Path::new("C:\\"))
    .or_else(|| disks.list().first());

  let (total, available) = match target {
    Some(d) => (d.total_space(), d.available_space()),
    None => (0, 0)
  };

  let used = total.saturating_sub(available);
  let pct = if total > 0 {
    ((used as f64 / total as f64 * 100.0).min(100.0)) as u32
  } else { 0 };

  Ok(serde_json::json!({
    "pct": pct,
    "used_gb": format!("{:.0}", used as f64 / 1_073_741_824.0),
    "total_gb": format!("{:.0}", total as f64 / 1_073_741_824.0)
  }))
}

#[tauri::command]
fn open_url_in_browser(url: String, browser: String) -> Result<String, String> {
    if url.starts_with("ms-windows-store://") {
        return match Command::new("cmd")
            .args(["/C", "start", &url])
            .spawn() {
                Ok(_) => Ok(format!(
                    "Opened Microsoft Store, sir."
                )),
                Err(e) => Err(format!("Failed: {}", e))
            };
    }

    let browser_lower = browser.to_lowercase();
    let browser_path = if browser_lower.contains("firefox") {
        "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
    } else if browser_lower.contains("edge") {
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    } else if browser_lower.contains("chrome") {
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    } else {
        ""
    };

    if !browser_path.is_empty() && Path::new(browser_path).exists() {
        match Command::new(browser_path).arg(&url).spawn() {
            Ok(_) => return Ok(format!("Opened URL in {}, sir.", browser)),
            Err(_) => {}
        }
    }

    // Fallback to default OS handler
    match open::that(&url) {
        Ok(_) => Ok(format!("Opened URL in default browser, sir.")),
        Err(e) => Err(format!("Failed to open URL: {}", e))
    }
}

// List files in a directory
#[tauri::command]
fn list_directory(path: String) 
  -> Result<serde_json::Value, String> {
  
  // Expand common shortcuts
  let expanded = path
    .replace("~", &std::env::var("USERPROFILE")
      .unwrap_or_default())
    .replace("%USERPROFILE%", 
      &std::env::var("USERPROFILE")
        .unwrap_or_default())
    .replace("%DESKTOP%",
      &format!("{}\\Desktop",
        std::env::var("USERPROFILE")
          .unwrap_or_default()));
  
  match fs::read_dir(&expanded) {
    Ok(entries) => {
      let mut files = vec![];
      let mut folders = vec![];
      
      for entry in entries.flatten() {
        let name = entry.file_name()
          .to_string_lossy()
          .to_string();
        let is_dir = entry.path().is_dir();
        let size = if !is_dir {
          entry.metadata()
            .map(|m| m.len())
            .unwrap_or(0)
        } else { 0 };
        
        if is_dir {
          folders.push(serde_json::json!({
            "name": name,
            "type": "folder",
            "size": 0
          }));
        } else {
          files.push(serde_json::json!({
            "name": name,
            "type": "file",
            "size": size
          }));
        }
      }
      
      Ok(serde_json::json!({
        "path": expanded,
        "folders": folders,
        "files": files,
        "total": folders.len() + files.len()
      }))
    }
    Err(e) => Err(format!(
      "Cannot read directory {}: {}", path, e
    ))
  }
}

// Create a folder
#[tauri::command]
fn create_folder(path: String)
  -> Result<String, String> {

  let expanded = path
    .replace("~", &std::env::var("USERPROFILE")
      .unwrap_or_default())
    .replace("%DESKTOP%",
      &format!("{}\\Desktop",
        std::env::var("USERPROFILE")
          .unwrap_or_default()));

  // Check if folder already exists
  if std::path::Path::new(&expanded).exists() {
    return Ok(format!(
      "Folder already exists: {}", expanded
    ));
  }

  match fs::create_dir_all(&expanded) {
    Ok(_) => Ok(format!(
      "Created folder: {}", expanded
    )),
    Err(e) => Err(format!(
      "Failed to create folder: {}", e
    ))
  }
}

// Read a text file
#[tauri::command]
fn read_file(path: String) 
  -> Result<String, String> {
  
  // Safety: only allow reading text files
  let allowed_extensions = vec![
    "txt", "md", "json", "csv", "log",
    "ini", "cfg", "yaml", "yml", "toml",
    "py", "js", "ts", "rs", "html", "css",
    "xml", "env", "gitignore",
  ];
  
  let ext = std::path::Path::new(&path)
    .extension()
    .and_then(|e| e.to_str())
    .unwrap_or("")
    .to_lowercase();
  
  if !allowed_extensions.contains(&ext.as_str())
     && !ext.is_empty() {
    return Err(format!(
      "Cannot read file type: .{}", ext
    ));
  }
  
  // Limit file size to 100KB
  let metadata = fs::metadata(&path)
    .map_err(|e| format!("File not found: {}", e))?;
  
  if metadata.len() > 102400 {
    return Err(
      "File too large to read (max 100KB)".to_string()
    );
  }
  
  fs::read_to_string(&path)
    .map_err(|e| format!("Cannot read file: {}", e))
}

// Open file with default application
#[tauri::command]
fn open_file(path: String) 
  -> Result<String, String> {
  match open::that(&path) {
    Ok(_) => Ok(format!(
      "Opened: {}", path
    )),
    Err(e) => Err(format!(
      "Cannot open file: {}", e
    ))
  }
}

// Show file in Windows Explorer
#[tauri::command]
fn show_in_explorer(path: String) 
  -> Result<String, String> {
  match Command::new("explorer")
    .args(["/select,", &path])
    .spawn() {
    Ok(_) => Ok(format!(
      "Showing {} in Explorer", path
    )),
    Err(e) => Err(format!("Failed: {}", e))
  }
}

// Rename or move a file/folder
#[tauri::command]
fn rename_item(
  from: String,
  to: String
) -> Result<String, String> {
  match fs::rename(&from, &to) {
    Ok(_) => Ok(format!(
      "Renamed {} to {}", from, to
    )),
    Err(e) => Err(format!(
      "Rename failed: {}", e
    ))
  }
}

// Delete file (requires confirmation flag)
#[tauri::command]
fn delete_file(
  path: String,
  confirmed: bool
) -> Result<String, String> {

  // -----------------------------------------------------------------------
  // HARD SAFETY GATE — runs unconditionally, before `confirmed` is checked.
  // Canonicalize first so symlinks / ".." traversal can never escape this.
  // -----------------------------------------------------------------------
  let raw_path = std::path::Path::new(&path);

  // Require the path to exist so we can canonicalize it.
  if !raw_path.exists() {
    return Err(format!("Path does not exist: {}", path));
  }

  let canonical = raw_path.canonicalize()
    .map_err(|e| format!("Could not resolve path: {}", e))?;

  // Build the set of always-protected paths.
  let mut protected: Vec<std::path::PathBuf> = vec![
    std::path::PathBuf::from(r"C:\"),
    std::path::PathBuf::from(r"C:\Windows"),
    std::path::PathBuf::from(r"C:\Program Files"),
    std::path::PathBuf::from(r"C:\Program Files (x86)"),
    std::path::PathBuf::from(r"C:\Users"),
    std::path::PathBuf::from(r"C:\ProgramData"),
    std::path::PathBuf::from(r"C:\System Volume Information"),
  ];

  // Also protect the user's own home directory root (e.g. C:\Users\nithish)
  // — files INSIDE it are fine, the root itself is not.
  if let Ok(home) = std::env::var("USERPROFILE") {
    protected.push(std::path::PathBuf::from(home));
  }
  // Belt-and-suspenders: also check HOMEDRIVE+HOMEPATH.
  if let (Ok(drive), Ok(homepath)) = (
    std::env::var("HOMEDRIVE"),
    std::env::var("HOMEPATH")
  ) {
    protected.push(std::path::PathBuf::from(format!("{}{}", drive, homepath)));
  }

  // Canonicalize each protected path (best-effort; skip if it doesn't exist).
  for protected_path in &protected {
    let canon_protected = protected_path
      .canonicalize()
      .unwrap_or_else(|_| protected_path.clone());

    if canonical == canon_protected {
      return Err(
        "This path is protected and cannot be deleted, sir.".to_string()
      );
    }
  }

  // Depth check: require at least 3 components from the drive root so that
  // paths like "C:\Users\username" (2 components after root) are rejected
  // even if they somehow slipped past the explicit list above.
  // e.g. C:\Users\nithish\Documents\file.txt has components:
  //   ["C:\\", "Users", "nithish", "Documents", "file.txt"] — depth 4, ok.
  // e.g. C:\Users\nithish has depth 2, rejected.
  let component_count = canonical.components().count();
  if component_count < 4 {
    return Err(
      "This path is too close to the drive root and cannot be deleted, sir."
        .to_string()
    );
  }

  // -----------------------------------------------------------------------
  // Confirmation gate (caller-supplied; enforced by the frontend confirm
  // flow — the hard gate above is the real security boundary).
  // -----------------------------------------------------------------------
  if !confirmed {
    return Err(format!(
      "REQUIRES_CONFIRMATION:Delete {}?", path
    ));
  }

  // Determine if it's a file or folder.
  let is_dir = canonical.is_dir();
  let item_type = if is_dir { "folder" } else { "file" };
  let item_name = canonical.file_name()
    .and_then(|n| n.to_str())
    .unwrap_or("item");

  // Perform deletion with appropriate method.
  let result = if is_dir {
    fs::remove_dir_all(&canonical)
  } else {
    fs::remove_file(&canonical)
  };

  match result {
    Ok(_) => Ok(format!(
      "Deleted {} '{}' successfully",
      item_type,
      item_name
    )),
    Err(e) => {
      let error_msg = e.to_string();
      Err(format!(
        "Failed to delete {} '{}': {}",
        item_type,
        item_name,
        if error_msg.is_empty() {
          "Permission denied or file in use"
        } else {
          error_msg.as_str()
        }
      ))
    }
  }
}


// Shutdown computer with confirmation
#[tauri::command]
fn shutdown_computer(confirmed: bool)
  -> Result<String, String> {
  if !confirmed {
    return Err(
      "REQUIRES_CONFIRMATION:Shutdown computer?"
        .to_string()
    );
  }
  Command::new("shutdown")
    .args(["/s", "/t", "30", "/c",
           "JARVIS initiated shutdown"])
    .spawn()
    .map(|_| "Shutting down in 30 seconds. \
               Say 'cancel shutdown' to abort."
               .to_string())
    .map_err(|e| format!("Failed: {}", e))
}

// Cancel shutdown
#[tauri::command]
fn cancel_shutdown() -> Result<String, String> {
  Command::new("shutdown")
    .args(["/a"])
    .spawn()
    .map(|_| "Shutdown cancelled, sir.".to_string())
    .map_err(|e| format!("Failed: {}", e))
}

// Restart computer with confirmation
#[tauri::command]
fn restart_computer(confirmed: bool)
  -> Result<String, String> {
  if !confirmed {
    return Err(
      "REQUIRES_CONFIRMATION:Restart computer?"
        .to_string()
    );
  }
  Command::new("shutdown")
    .args(["/r", "/t", "30"])
    .spawn()
    .map(|_| "Restarting in 30 seconds."
           .to_string())
    .map_err(|e| format!("Failed: {}", e))
}

// In-process via the `battery` crate - no powershell.exe spawn.
#[tauri::command]
fn get_power_status()
  -> Result<serde_json::Value, String> {
  let manager = battery::Manager::new()
    .map_err(|e| format!("Power manager init failed: {}", e))?;

  let mut batteries = manager.batteries()
    .map_err(|e| format!("Power query failed: {}", e))?;

  match batteries.next() {
    Some(Ok(bat)) => {
      let is_charging = matches!(
        bat.state(),
        battery::State::Charging | battery::State::Full
      );
      Ok(serde_json::json!({
        "is_charging": is_charging,
        "has_battery": true,
        "mode": if is_charging { "3d" } else { "2d" }
      }))
    }
    // No battery reported - desktop PC, always AC power
    _ => Ok(serde_json::json!({
      "is_charging": true,
      "has_battery": false,
      "mode": "3d"
    }))
  }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let sys = System::new_all();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SysState(Mutex::new(sys)))
        .manage(EngineProcess(Mutex::new(None)))
        .manage(SetupState(Mutex::new(sidecar_setup::SetupProgress::default())))
        .setup(|app| {
            let handle = app.handle().clone();
            // Spawned on the async runtime rather than blocking .setup():
            // the TCP probe, first-run _internal download, and process
            // spawn must never delay the window from opening. The
            // frontend polls /health and shows "engine not running" (see
            // useEngineStatus.ts), and separately listens for
            // sidecar-setup-progress events (see useSidecarSetup.ts) to
            // show real download progress instead of an apparently-frozen
            // app during first-run setup.
            tauri::async_runtime::spawn(async move {
                spawn_engine_sidecar(&handle).await;
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_system_info,
            sidecar_setup::get_sidecar_setup_status,
            sidecar_setup::retry_sidecar_setup,
            open_application,
            find_application,
            close_application,
            set_volume,
            run_system_query,
            lock_screen,
            get_battery_info,
            get_disk_info,
            open_url_in_browser,
            list_directory,
            create_folder,
            read_file,
            open_file,
            show_in_explorer,
            rename_item,
            delete_file,
            shutdown_computer,
            cancel_shutdown,
            restart_computer,
            get_power_status,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            // RunEvent::Exit (not just window CloseRequested) so the
            // backend is also reaped if the app quits via the tray, a
            // shutdown signal, or any path other than the user clicking
            // the window's close button.
            if let tauri::RunEvent::Exit = event {
                kill_engine_sidecar(app_handle);
            }
        });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_application_notepad() {
        let result = find_application("notepad".to_string());
        assert!(result.is_ok(), "Notepad should be found");
        let path = result.unwrap();
        assert!(path.contains("notepad") || path.contains("Microsoft.WindowsNotepad"));
    }

    #[test]
    fn test_powershell_injection_prevented() {
        let injection_payload = "test'; Write-Output 'INJECTED".to_string();
        let result = find_application(injection_payload);
        assert!(result.is_err(), "Injection payload should fail to find any application");
        let err_msg = result.unwrap_err();
        assert_eq!(err_msg, "Could not find: test'; Write-Output 'INJECTED");
    }

    #[test]
    fn test_app_name_with_apostrophe() {
        let app_name = "test's app".to_string();
        let result = find_application(app_name);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Could not find: test's app");
    }

    #[test]
    fn test_system_query_uptime() {
        let state = SysState(Mutex::new(System::new_all()));
        let result = run_system_query_impl(
            &state,
            SystemQuery::Uptime,
            None,
        );
        assert!(result.is_ok());
        assert!(result.unwrap().contains("System Uptime:"));
    }

    #[test]
    fn test_system_query_disk_space() {
        let state = SysState(Mutex::new(System::new_all()));
        let result = run_system_query_impl(
            &state,
            SystemQuery::DiskSpace,
            None,
        );
        assert!(result.is_ok());
        assert!(result.unwrap().contains("Disk (C:):"));
    }

    #[test]
    fn test_system_query_top_processes() {
        let state = SysState(Mutex::new(System::new_all()));
        let result = run_system_query_impl(
            &state,
            SystemQuery::TopProcesses,
            Some(QueryParams { count: Some(3) }),
        );
        assert!(result.is_ok());
        let out = result.unwrap();
        assert!(out.contains("Top 3 CPU Processes:"));
    }

    #[test]
    fn test_system_query_battery() {
        let state = SysState(Mutex::new(System::new_all()));
        let result = run_system_query_impl(
            &state,
            SystemQuery::BatteryLevel,
            None,
        );
        assert!(result.is_ok());
        assert!(result.unwrap().contains("Battery:"));
    }

    #[test]
    fn test_system_query_ip_address() {
        let state = SysState(Mutex::new(System::new_all()));
        let result = run_system_query_impl(
            &state,
            SystemQuery::IpAddress,
            None,
        );
        assert!(result.is_ok());
        assert!(result.unwrap().contains("IP Address:"));
    }

    #[test]
    fn test_close_application_invalid_name() {
        let state = SysState(Mutex::new(System::new_all()));
        let result = close_application_impl(
            &state,
            "calc; rm -rf /".to_string(),
        );
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Invalid application name format");
    }

    #[test]
    fn test_set_volume_actions() {
        assert!(set_volume("up".to_string()).is_ok());
        assert!(set_volume("down".to_string()).is_ok());
        assert!(set_volume("mute".to_string()).is_ok());
        assert!(set_volume("invalid".to_string()).is_err());
    }
}

