"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const chartConfig = {
  value: { label: "Value", color: "hsl(var(--chart-2))" },
} satisfies ChartConfig

type ChartKind = "kwh" | "cost" | "co2"

export interface ForecastChartPoint {
  day: string   // "Mon"
  value: number
}

interface ForecastChartProps {
  type: ChartKind
  data: ForecastChartPoint[]
}

export function ForecastChart({ type, data }: ForecastChartProps) {
  return (
    <ChartContainer config={chartConfig} className="h-[350px] w-full">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="fillForecast" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-value)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="var(--color-value)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="day" tickLine={false} axisLine={false} tickMargin={8} className="text-xs" />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} className="text-xs" />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area type="monotone" dataKey="value" stroke="var(--color-value)" strokeWidth={2} fill="url(#fillForecast)" />
      </AreaChart>
    </ChartContainer>
  )
}