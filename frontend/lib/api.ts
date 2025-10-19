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
  
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard metrics: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Fetch only current power reading
 */
export async function getCurrentPower(homeId: number = 1): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/dashboard/current-power/${homeId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch current power: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.current_power_kw
}

/**
 * Fetch today's stats (usage, cost, CO2)
 */
export async function getTodayStats(homeId: number = 1) {
  const response = await fetch(`${API_BASE_URL}/dashboard/today-stats/${homeId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch today's stats: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Fetch 24-hour hourly usage data
 */
export async function getHourlyUsage(homeId: number = 1): Promise<HourlyUsage[]> {
  const response = await fetch(`${API_BASE_URL}/dashboard/hourly/${homeId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch hourly usage: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.data || []
}

/**
 * Fetch weather data
 */
export async function getWeather(homeId: number = 1): Promise<Weather> {
  const response = await fetch(`${API_BASE_URL}/dashboard/weather/${homeId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch weather: ${response.statusText}`)
  }
  
  return response.json()
}