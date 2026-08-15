use std::sync::Mutex;
use sysinfo::System;

pub struct SysState(pub Mutex<System>);

#[tauri::command]
fn get_system_info(state: tauri::State<SysState>) -> serde_json::Value {
    let mut sys = state.0.lock().unwrap();
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let total_mem = sys.total_memory();
    let used_mem = sys.used_memory();
    let ram_pct = if total_mem > 0 {
        (used_mem as f64 / total_mem as f64 * 100.0) as u32
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let sys = System::new_all();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SysState(Mutex::new(sys)))
        .invoke_handler(tauri::generate_handler![get_system_info])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
