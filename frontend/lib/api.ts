// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface DashboardMetrics {
  current_power_kw: number
  today_usage_kwh: number
  today_cost_usd: number
  today_co2_kg: number
  hourly_usage_24h: HourlyUsage[]
  weather: Weather | null
}

export interface HourlyUsage {
  time: string
  hour: number
  kwh: number
}

export interface Weather {
  temperature_f: number
  temperature_c: number
  indoor_temperature_c: number
  humidity: number | null
  wind_speed: number | null
}

/**
 * Fetch all dashboard metrics for a home
 */
export async function getDashboardMetrics(homeId: number = 1): Promise<DashboardMetrics> {
  const response = await fetch(`${API_BASE_URL}/dashboard/metrics/${homeId}`)
  if (!response.ok) throw new Error(`Failed to fetch dashboard metrics: ${response.statusText}`)
  return response.json()
}

/**
 * Fetch only current power reading
 */
export async function getCurrentPower(homeId: number = 1): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/dashboard/current-power/${homeId}`)
  if (!response.ok) throw new Error(`Failed to fetch current power: ${response.statusText}`)
  const data = await response.json()
  return data.current_power_kw
}

/**
 * Fetch today's stats (usage, cost, CO2)
 */
export async function getTodayStats(homeId: number = 1) {
  const response = await fetch(`${API_BASE_URL}/dashboard/today-stats/${homeId}`)
  if (!response.ok) throw new Error(`Failed to fetch today's stats: ${response.statusText}`)
  return response.json()
}

/**
 * Fetch 24-hour hourly usage data
 */
export async function getHourlyUsage(homeId: number = 1): Promise<HourlyUsage[]> {
  const response = await fetch(`${API_BASE_URL}/dashboard/hourly/${homeId}`)
  if (!response.ok) throw new Error(`Failed to fetch hourly usage: ${response.statusText}`)
  const data = await response.json()
  return data.data || []
}

/**
 * Fetch weather data
 */
export async function getWeather(homeId: number = 3): Promise<Weather> {
  const response = await fetch(`${API_BASE_URL}/dashboard/weather/${homeId}`)
  if (!response.ok) throw new Error(`Failed to fetch weather: ${response.statusText}`)
  return response.json()
}

/** ---------------- NEW: Devices fetcher ----------------
 * Backend endpoint (suggested):
 *   GET /homes/:homeId/devices
 *   -> { home_id, devices: [{ appliance_type, last_kwh, last_seen_iso, device_smartness, is_online }] }
 * If your backend returns a different shape, just adjust the mapping below.
 */
export type DeviceStatus = 'online' | 'offline' | 'unknown'
export type DeviceSource = 'app' | 'plug'

export interface Device {
  name: string
  powerLabel: string
  status: DeviceStatus
  source: DeviceSource     // only this classification remains
  lastSeen?: string
}

export async function getDevices(homeId: number | string = 1): Promise<Device[]> {
  const res = await fetch(`${API_BASE_URL}/homes/${homeId}/devices`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to fetch devices: ${res.statusText}`)
  const json = await res.json()

  const now = Date.now()
  return (json.devices || []).map((d: any): Device => {
    const lastSeen = d.last_seen_iso || undefined
    const hoursSince = lastSeen ? (now - new Date(lastSeen).getTime()) / 36e5 : Number.POSITIVE_INFINITY

    const status: DeviceStatus =
      typeof d.is_online === 'boolean'
        ? d.is_online
          ? 'online'
          : 'offline'
        : hoursSince <= 24
          ? 'online'
          : hoursSince <= 72
            ? 'unknown'
            : 'offline'

    const source: DeviceSource = d.source === 'plug' ? 'plug' : 'app'
    const powerLabel =
      typeof d.last_kwh === 'number' && !Number.isNaN(d.last_kwh)
        ? `${d.last_kwh.toFixed(3)} kWh`
        : '—'

    return { name: d.appliance_type, powerLabel, status, source, lastSeen }
  })
}
