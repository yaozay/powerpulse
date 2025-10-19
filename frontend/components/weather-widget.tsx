"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cloud, Sun, CloudRain, MapPin } from "lucide-react"
import type { Weather } from "@/lib/api"
import { getWeatherForecast7d, type WeatherForecastPoint } from "@/lib/api"

interface WeatherWidgetProps {
  weather: Weather | null | undefined
  homeId?: number | string
}

export function WeatherWidget({ weather, homeId = 1 }: WeatherWidgetProps) {
  const [weekly, setWeekly] = useState<WeatherForecastPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false
    ;(async () => {
      try {
        setLoading(true); setError(null)
        const data = await getWeatherForecast7d(homeId)
        if (!ignore) setWeekly(data)
      } catch (e: any) {
        if (!ignore) setError(e?.message ?? "Failed to load weather forecast")
      } finally {
        if (!ignore) setLoading(false)
      }
    })()
    return () => { ignore = true }
  }, [homeId])

  const getWeatherIcon = (f?: number) => {
    const temp = f ?? weather?.temperature_f ?? 60
    if (temp >= 85) return Sun
    if (temp <= 45) return CloudRain
    return Cloud
  }

  const CurrentIcon = getWeatherIcon(weather?.temperature_f)
  const loc = weather?.location
  ? `${weather.location} (Home ${homeId})`
  : `Home ${homeId}`

  return (
    <Card className="group relative overflow-hidden border-0 shadow-xl h-full">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-400/20 to-transparent rounded-full blur-3xl" />

      <CardHeader className="relative z-10">
        <CardTitle className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
          Weather
        </CardTitle>
        <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
          <MapPin className="h-3.5 w-3.5" />
          <span>{loc}</span>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 relative z-10">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Current</p>
            <p className="text-5xl font-bold bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-transparent">
              {weather ? `${Math.round(weather.temperature_f)}°` : "--°"}
            </p>
            <p className="text-lg text-muted-foreground mt-1">Fahrenheit</p>
          </div>

          <div className="relative">
            <CurrentIcon className="h-20 w-20 text-blue-400/80" />
            <div className="absolute inset-0 h-20 w-20 blur-xl bg-blue-400/20" />
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-sm font-semibold">This week</div>

          {error ? (
            <div className="text-sm text-destructive">{error}</div>
          ) : loading ? (
            <div className="text-xs text-muted-foreground">Loading…</div>
          ) : (
            <ul className="grid grid-cols-2 gap-2">
              {weekly.map((d) => {
                const Icon = getWeatherIcon(d.temp_f)
                return (
                  <li
                    key={d.date}
                    className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2 text-sm"
                  >
                    <span className="text-muted-foreground flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      {d.weekday}
                    </span>
                    <span className="font-medium">{Math.round(d.temp_f)}°</span>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  )
}