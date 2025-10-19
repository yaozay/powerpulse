"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cloud, Droplets, Wind, Sun, CloudRain } from "lucide-react"
import type { Weather } from "@/lib/api"

interface WeatherWidgetProps {
  weather: Weather | null | undefined
}

export function WeatherWidget({ weather }: WeatherWidgetProps) {
  const getWeatherIcon = () => {
    if (!weather) return Cloud
    const temp = weather.temperature_f
    const humidity = weather.humidity || 0

    if (humidity > 70) return CloudRain
    if (temp > 75) return Sun
    return Cloud
  }

  const WeatherIcon = getWeatherIcon()

  return (
    <Card className="group relative overflow-hidden border-0 shadow-xl h-full">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-400/20 to-transparent rounded-full blur-3xl animate-pulse-slow" />

      <CardHeader className="relative z-10">
        <CardTitle className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
          Weather
        </CardTitle>
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
            <WeatherIcon className="h-20 w-20 text-blue-400/80 animate-float" />
            <div className="absolute inset-0 h-20 w-20 blur-xl bg-blue-400/20 animate-pulse-slow" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Droplets className="h-4 w-4 text-blue-400" />
            Humidity: {weather ? `${weather.humidity ?? "--"}%` : "--"}
          </div>
          <div className="flex items-center gap-2">
            <Wind className="h-4 w-4 text-blue-400" />
            Wind: {weather ? `${weather.wind_speed ?? "--"} mph` : "--"}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
