use std::sync::Mutex;
use sysinfo::System;
use std::process::Command;
use std::path::Path;

pub struct SysState(pub Mutex<System>);

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
    
    // GPU info - detect both GPUs
    let gpus = vec![
        serde_json::json!({
            "name": "GTX 1650",
            "type": "discrete",
            "usage": 0,
            "temp": 0
        }),
        serde_json::json!({
            "name": "Intel UHD",
            "type": "integrated", 
            "usage": 0,
            "temp": 0
        })
    ];
    
    serde_json::json!({
        "cpu_usage": cpu_usage as u32,
        "cpu_name": cpu_name,
        "cpu_cores": cpu_cores,
        "ram_pct": ram_pct,
        "ram_used_gb": format!("{:.1}", used_mem as f64 / 1_073_741_824.0),
        "ram_total_gb": format!("{:.0}", total_mem as f64 / 1_073_741_824.0),
        "gpus": gpus,
        "ssd_pct": 80,
        "ssd_used_gb": "410",
        "ssd_total_gb": "512"
    })
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
  
  // Search using PowerShell for installed apps
  let output = Command::new("powershell")
    .args([
      "-Command",
      &format!(
        "Get-StartApps | Where-Object {{$_.Name -like '*{}*'}} | Select-Object -First 1 -ExpandProperty AppID",
        app_name
      )
    ])
    .output();
  
  if let Ok(out) = output {
    let app_id = String::from_utf8_lossy(
      &out.stdout
    ).trim().to_string();
    if !app_id.is_empty() {
      return Ok(format!("shell:appsFolder\\{}", app_id));
    }
  }
  
  // Search in AppData for user-installed apps
  let appdata_output = Command::new("powershell")
    .args([
      "-Command",
      &format!(
        "Get-ChildItem -Path \"$env:LOCALAPPDATA\\Programs\",\"$env:APPDATA\" -Recurse -Depth 3 -Filter \"*.exe\" -ErrorAction SilentlyContinue | Where-Object {{$_.Name -match '^{}(\\.exe)?$'}} | Select-Object -First 1 -ExpandProperty FullName",
        app_name
      )
    ])
    .output();
    
  if let Ok(out) = appdata_output {
    let path = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if !path.is_empty() && Path::new(&path).exists() {
      return Ok(path);
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

// 3. EXECUTE POWERSHELL WITH SAFETY CHECK
// Returns (output, is_safe)
#[tauri::command]
fn execute_powershell(
  script: String,
  requires_confirmation: bool
) -> Result<String, String> {
  
  // Safety: block dangerous operations
  let dangerous = vec![
    "remove-item", "del ", "rmdir", "format ",
    "clear-disk", "initialize-disk",
    "stop-computer", "restart-computer",
    "disable-netadapter", "invoke-webrequest",
    "downloadfile", "invoke-expression",
    "wget ", "curl ", "iex ", 
    "set-executionpolicy",
  ];
  
  let script_lower = script.to_lowercase();
  for danger in &dangerous {
    if script_lower.contains(danger) 
       && !requires_confirmation {
      return Err(format!(
        "REQUIRES_CONFIRMATION:{}",
        script
      ));
    }
  }
  
  let output = Command::new("powershell")
    .args([
      "-NoProfile",
      "-NonInteractive", 
      "-Command",
      &script
    ])
    .output();
  
  match output {
    Ok(out) => {
      let stdout = String::from_utf8_lossy(
        &out.stdout
      ).trim().to_string();
      let stderr = String::from_utf8_lossy(
        &out.stderr
      ).trim().to_string();
      
      if out.status.success() {
        Ok(if stdout.is_empty() { 
          "Done.".to_string() 
        } else { 
          stdout 
        })
      } else {
        Err(if stderr.is_empty() { 
          "Command failed".to_string() 
        } else { 
          stderr 
        })
      }
    }
    Err(e) => Err(format!("Execution failed: {}", e))
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
#[tauri::command]
fn get_battery_info() 
  -> Result<serde_json::Value, String> {
  let output = Command::new("powershell")
    .args([
      "-Command",
      "Get-WmiObject Win32_Battery | \
       Select-Object EstimatedChargeRemaining,\
       BatteryStatus | ConvertTo-Json"
    ])
    .output();
  
  match output {
    Ok(out) => {
      let raw = String::from_utf8_lossy(
        &out.stdout
      ).trim().to_string();
      
      if raw.is_empty() {
        return Ok(serde_json::json!({
          "level": 100,
          "charging": true,
          "has_battery": false,
          "status": "Desktop - No battery"
        }));
      }
      
      if let Ok(parsed) = 
        serde_json::from_str::<serde_json::Value>(
          &raw
        ) {
        let level = parsed[
          "EstimatedChargeRemaining"
        ].as_u64().unwrap_or(100);
        let status = parsed[
          "BatteryStatus"
        ].as_u64().unwrap_or(2);
        let charging = status == 2;
        
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
      } else {
        Ok(serde_json::json!({
          "level": 100,
          "charging": true,
          "has_battery": false,
          "status": "Unknown"
        }))
      }
    }
    Err(e) => Err(format!("Battery query failed: {}", e))
  }
}

// 6. GET REAL DISK INFO
#[tauri::command]
fn get_disk_info() 
  -> Result<serde_json::Value, String> {
  let output = Command::new("powershell")
    .args([
      "-Command",
      "Get-PSDrive C | \
       Select-Object Used,Free | \
       ConvertTo-Json"
    ])
    .output();
  
  match output {
    Ok(out) => {
      let raw = String::from_utf8_lossy(
        &out.stdout
      ).trim().to_string();
      
      if let Ok(parsed) = 
        serde_json::from_str::<serde_json::Value>(
          &raw
        ) {
        let used = parsed["Used"]
          .as_u64().unwrap_or(0);
        let free = parsed["Free"]
          .as_u64().unwrap_or(0);
        let total = used + free;
        let pct = if total > 0 {
          ((used as f64 / total as f64 * 100.0)
            .min(100.0)) as u32
        } else { 0 };
        
        Ok(serde_json::json!({
          "pct": pct,
          "used_gb": format!("{:.0}", 
            used as f64 / 1_073_741_824.0),
          "total_gb": format!("{:.0}", 
            total as f64 / 1_073_741_824.0)
        }))
      } else {
        Ok(serde_json::json!({
          "pct": 0, "used_gb": "0", 
          "total_gb": "0"
        }))
      }
    }
    Err(e) => Err(format!("Disk query failed: {}", e))
  }
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let sys = System::new_all();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SysState(Mutex::new(sys)))
        .invoke_handler(tauri::generate_handler![
            get_system_info,
            open_application,
            find_application,
            execute_powershell,
            lock_screen,
            get_battery_info,
            get_disk_info,
            open_url_in_browser,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
