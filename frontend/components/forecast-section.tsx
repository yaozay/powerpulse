"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ForecastChart, type ForecastChartPoint } from "@/components/forecast-chart"
import { cn } from "@/lib/utils"
import { getForecast7d } from "@/lib/api"

const tabs = [
  { id: "kwh", label: "kWh" },
  { id: "cost", label: "Cost" },
  { id: "co2", label: "CO₂" },
] as const
type TabId = typeof tabs[number]["id"]

export function ForecastSection({ homeId = 1 }: { homeId?: number | string }) {
  const [activeTab, setActiveTab] = useState<TabId>("kwh")
  const [raw, setRaw] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false
    ;(async () => {
      try {
        setLoading(true); setError(null)
        const f = await getForecast7d(homeId)
        if (!ignore) setRaw(f)
      } catch (e: any) {
        if (!ignore) setError(e?.message ?? "Failed to load forecast")
      } finally {
        if (!ignore) setLoading(false)
      }
    })()
    return () => { ignore = true }
  }, [homeId])

  const data: ForecastChartPoint[] = useMemo(() => {
    const key = activeTab === "kwh" ? "kwh" : activeTab === "cost" ? "cost_usd" : "co2_kg"
    return (raw || []).map(d => ({
      day: d.weekday,        // "Mon"
      value: Number(d[key] ?? 0)
    }))
  }, [raw, activeTab])

  return (
    <section id="forecast" className="py-12">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold text-balance">Energy Forecast</h2>
        <p className="text-lg text-muted-foreground">
          Predicted energy consumption for the next 7 days
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>7-Day Forecast</CardTitle>

            <div className="flex items-center gap-2 rounded-full bg-muted p-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "rounded-full px-4 py-1.5 text-sm font-medium transition-all",
                    activeTab === tab.id
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {error ? (
            <div className="text-sm text-destructive">{error}</div>
          ) : (
            <ForecastChart type={activeTab} data={data} />
          )}
          {loading && <div className="mt-2 text-xs text-muted-foreground">Loading forecast…</div>}
        </CardContent>
      </Card>
    </section>
  )
}