"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cloud, Droplets, Wind } from "lucide-react"
import type { Weather } from "@/lib/api"

interface WeatherWidgetProps {
  weather: Weather | null | undefined
}

export function WeatherWidget({ weather }: WeatherWidgetProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weather</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Current</p>
            <p className="text-4xl font-bold">
              {weather ? `${Math.round(weather.temperature_f)}°F` : "--°F"}
            </p>
          </div>
          <Cloud className="h-16 w-16 text-muted-foreground" />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Droplets className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Humidity</span>
            </div>
            <span className="font-medium">
              {weather?.humidity ? `${weather.humidity}%` : "N/A"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wind className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Wind Speed</span>
            </div>
            <span className="font-medium">
              {weather?.wind_speed ? `${weather.wind_speed} mph` : "N/A"}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}