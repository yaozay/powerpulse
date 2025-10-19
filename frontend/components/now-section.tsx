"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Zap, DollarSign, Leaf, TrendingUp } from "lucide-react"
import { EnergyChart } from "@/components/energy-chart"
import { WeatherWidget } from "@/components/weather-widget"
import { getDashboardMetrics, type DashboardMetrics } from "@/lib/api"

const metricConfigs = [
  {
    key: "current_power_kw",
    title: "Current Power",
    unit: "kW",
    icon: Zap,
    color: "text-primary",
  },
  {
    key: "today_usage_kwh",
    title: "Today's Usage",
    unit: "kWh",
    icon: TrendingUp,
    color: "text-chart-2",
  },
  {
    key: "today_cost_usd",
    title: "Today's Cost",
    unit: "",
    prefix: "$",
    icon: DollarSign,
    color: "text-chart-3",
  },
  {
    key: "today_co2_kg",
    title: "Today's CO₂",
    unit: "kg",
    icon: Leaf,
    color: "text-secondary",
  },
]

export function NowSection() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Initial fetch
    fetchMetrics()

    // Refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchMetrics = async () => {
    try {
      const data = await getDashboardMetrics(1)
      setMetrics(data)
      setError(null)
    } catch (err) {
      console.error("Failed to fetch metrics:", err)
      setError("Failed to load data")
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="now" className="py-12">
      <div className="mb-8">
        <h1 className="mb-2 text-4xl font-bold text-balance">Your Energy at a Glance</h1>
        <p className="text-lg text-muted-foreground">Real-time monitoring of your home energy consumption</p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg bg-destructive/10 p-4 text-destructive">
          {error} - Make sure the backend is running on http://localhost:8000
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {metricConfigs.map((config) => {
          const Icon = config.icon
          const value = metrics?.[config.key as keyof DashboardMetrics] ?? 0
          const displayValue = config.prefix 
            ? `${config.prefix}${Number(value).toFixed(2)}`
            : Number(value).toFixed(1)

          return (
            <Card key={config.title} className="transition-shadow hover:shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {config.title}
                </CardTitle>
                <Icon className={cn("h-4 w-4", config.color)} />
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-1">
                  {loading ? (
                    <span className="text-3xl font-bold text-muted-foreground">--</span>
                  ) : (
                    <>
                      <span className="text-3xl font-bold">{displayValue}</span>
                      {config.unit && (
                        <span className="text-sm text-muted-foreground">{config.unit}</span>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Energy Usage (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <EnergyChart homeId="1" metrics={metrics} />
          </CardContent>
        </Card>

        <WeatherWidget weather={metrics?.weather} />
      </div>
    </section>
  )
}