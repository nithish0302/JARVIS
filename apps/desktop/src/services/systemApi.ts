import { invoke } from "@tauri-apps/api/core"

export async function openApplication(
  appName: string
): Promise<string> {
  return await invoke("open_application", {
    appName
  })
}

export async function openUrlInBrowser(
  url: string,
  browser: string
): Promise<string> {
  return await invoke("open_url_in_browser", {
    url,
    browser
  })
}

export async function executePowerShell(
  script: string,
  requiresConfirmation: boolean = false
): Promise<string> {
  return await invoke("execute_powershell", {
    script,
    requiresConfirmation
  })
}

export async function lockScreen(): 
  Promise<string> {
  return await invoke("lock_screen")
}

export async function getBatteryInfo(): Promise<any> {
  return await invoke("get_battery_info")
}

export async function getDiskInfo(): Promise<any> {
  return await invoke("get_disk_info")
}

export async function listDirectory(
  path: string
): Promise<any> {
  return await invoke("list_directory", { path })
}

export async function createFolder(
  path: string
): Promise<string> {
  return await invoke("create_folder", { path })
}

export async function readFile(
  path: string
): Promise<string> {
  return await invoke("read_file", { path })
}

export async function openFile(
  path: string
): Promise<string> {
  return await invoke("open_file", { path })
}

export async function showInExplorer(
  path: string
): Promise<string> {
  return await invoke("show_in_explorer", { path })
}

export async function renameItem(
  from: string,
  to: string
): Promise<string> {
  return await invoke("rename_item", { from, to })
}

export async function deleteFile(
  path: string,
  confirmed: boolean = false
): Promise<string> {
  return await invoke("delete_file", { 
    path, confirmed 
  })
}
