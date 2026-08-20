use std::sync::Mutex;
use sysinfo::System;
use std::process::Command;
use std::path::Path;
use std::fs;

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
  if !confirmed {
    return Err(format!(
      "REQUIRES_CONFIRMATION:Delete {}?", path
    ));
  }

  let p = std::path::Path::new(&path);

  // CRITICAL: Verify path exists before attempting delete
  if !p.exists() {
    return Err(format!(
      "Path does not exist: {}", path
    ));
  }

  // Determine if it's a file or folder
  let is_dir = p.is_dir();
  let item_type = if is_dir { "folder" } else { "file" };
  let item_name = p.file_name()
    .and_then(|n| n.to_str())
    .unwrap_or("item");

  // Perform deletion with appropriate method
  let result = if is_dir {
    fs::remove_dir_all(&path)
  } else {
    fs::remove_file(&path)
  };

  match result {
    Ok(_) => Ok(format!(
      "Deleted {} '{}' successfully",
      item_type,
      item_name
    )),
    Err(e) => {
      // Return detailed error message
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

#[tauri::command]
fn get_power_status() 
  -> Result<serde_json::Value, String> {
  let output = Command::new("powershell")
    .args([
      "-Command",
      "Get-WmiObject Win32_Battery | \
       Select-Object BatteryStatus | \
       ConvertTo-Json -Compress"
    ])
    .output();
  
  match output {
    Ok(out) => {
      let raw = String::from_utf8_lossy(
        &out.stdout
      ).trim().to_string();
      
      if raw.is_empty() || 
         raw == "null" || 
         raw == "{}" {
        // Desktop PC - always AC power
        return Ok(serde_json::json!({
          "is_charging": true,
          "has_battery": false,
          "mode": "3d"
        }));
      }
      
      if let Ok(parsed) = 
        serde_json::from_str::<serde_json::Value>(
          &raw
        ) {
        // BatteryStatus 2 = AC Power (charging)
        // BatteryStatus 1 = Discharging
        let status = parsed["BatteryStatus"]
          .as_u64().unwrap_or(1);
        let is_charging = status == 2;
        
        return Ok(serde_json::json!({
          "is_charging": is_charging,
          "has_battery": true,
          "mode": if is_charging { "3d" } else { "2d" }
        }));
      }
      
      Ok(serde_json::json!({
        "is_charging": true,
        "has_battery": false,
        "mode": "3d"
      }))
    }
    Err(e) => Err(format!(
      "Power query failed: {}", e
    ))
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
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
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
}

