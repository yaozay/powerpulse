"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import type { DashboardMetrics } from "@/lib/api"

interface EnergyChartProps {
  homeId: string
  metrics: DashboardMetrics | null
}

export function EnergyChart({ metrics }: EnergyChartProps) {
  const chartConfig = {
    kwh: { label: "Energy (kWh)", color: "hsl(var(--chart-1))" },
  } as const

  // Use data from API or empty array
  const data = metrics?.hourly_usage_24h || []

  return (
    <ChartContainer config={chartConfig} className="h-[300px] w-full">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="fillKWh" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-kwh, var(--chart-1))" stopOpacity={0.3} />
            <stop offset="95%" stopColor="var(--color-kwh, var(--chart-1))" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis 
          dataKey="time" 
          tickLine={false} 
          axisLine={false} 
          tickMargin={8} 
          className="text-xs" 
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          className="text-xs"
          tickFormatter={(v) => `${v} kWh`}
          domain={[0, "dataMax + 0.5"]}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area 
          type="monotone" 
          dataKey="kwh" 
          stroke="var(--color-kwh, var(--chart-1))" 
          strokeWidth={2} 
          fill="url(#fillKWh)" 
        />
      </AreaChart>
    </ChartContainer>
  )
}