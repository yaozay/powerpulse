"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ForecastChart } from "@/components/forecast-chart"
import { cn } from "@/lib/utils"

const tabs = [
  { id: "kwh", label: "kWh" },
  { id: "cost", label: "Cost" },
  { id: "co2", label: "CO₂" },
]

export function ForecastSection() {
  const [activeTab, setActiveTab] = useState("kwh")

  return (
    <section id="forecast" className="py-12">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold text-balance">Energy Forecast</h2>
        <p className="text-lg text-muted-foreground">Predicted energy consumption for the next 7 days</p>
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
          <ForecastChart type={activeTab} />
        </CardContent>
      </Card>
    </section>
  )
}
