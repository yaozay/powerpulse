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

  const data = metrics?.hourly_usage_24h || []

  return (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 rounded-lg blur-xl" />
      <ChartContainer config={chartConfig} className="h-[300px] w-full relative z-10">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="fillKWh" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-kwh, var(--chart-1))" stopOpacity={0.4} />
              <stop offset="50%" stopColor="var(--color-kwh, var(--chart-1))" stopOpacity={0.2} />
              <stop offset="95%" stopColor="var(--color-kwh, var(--chart-1))" stopOpacity={0} />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" opacity={0.5} />
          <XAxis 
            dataKey="time" 
            tickLine={false} 
            axisLine={false} 
            tickMargin={8} 
            className="text-xs font-medium"
            stroke="hsl(var(--muted-foreground))"
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            className="text-xs font-medium"
            tickFormatter={(v) => `${v} kWh`}
            domain={[0, "dataMax + 0.5"]}
            stroke="hsl(var(--muted-foreground))"
          />
          <ChartTooltip 
            content={<ChartTooltipContent className="bg-background/95 backdrop-blur-xl border-border/50 shadow-xl" />} 
          />
          <Area 
            type="monotone" 
            dataKey="kwh" 
            stroke="var(--color-kwh, var(--chart-1))" 
            strokeWidth={3} 
            fill="url(#fillKWh)"
            filter="url(#glow)"
          />
        </AreaChart>
      </ChartContainer>
    </div>
  )
}