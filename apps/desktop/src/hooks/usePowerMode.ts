import { useEffect } from "react"
import { invoke } from "@tauri-apps/api/core"
import { useAppStore } from "../stores/useAppStore"

export function usePowerMode() {
  const { setGraphMode, setIsCharging } = 
    useAppStore()
  
  useEffect(() => {
    const checkPower = async () => {
      try {
        const status: any = await invoke(
          "get_power_status"
        )
        console.log("Power status:", status);
        console.log("Setting graphMode to:", status.is_charging ? "3d" : "2d");
        setIsCharging(status.is_charging)
        setGraphMode(
          status.is_charging ? "3d" : "2d"
        )
        console.log(
          `Power: ${status.is_charging ?
            "charging → 3D" : "battery → 2D"}`
        )
      } catch (err) {
        console.error("Power check failed:", err)
        setGraphMode("3d") // Default to 3D
      }
    }
    
    checkPower()
    const interval = setInterval(
      checkPower, 30000
    )
    return () => clearInterval(interval)
  }, [setGraphMode, setIsCharging])
}
