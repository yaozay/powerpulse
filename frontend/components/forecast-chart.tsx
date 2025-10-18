"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const forecastData = {
  kwh: [
    { day: "Mon", value: 22.5 },
    { day: "Tue", value: 24.2 },
    { day: "Wed", value: 21.8 },
    { day: "Thu", value: 23.5 },
    { day: "Fri", value: 25.1 },
    { day: "Sat", value: 19.8 },
    { day: "Sun", value: 18.5 },
  ],
  cost: [
    { day: "Mon", value: 5.4 },
    { day: "Tue", value: 5.8 },
    { day: "Wed", value: 5.2 },
    { day: "Thu", value: 5.6 },
    { day: "Fri", value: 6.0 },
    { day: "Sat", value: 4.8 },
    { day: "Sun", value: 4.4 },
  ],
  co2: [
    { day: "Mon", value: 10.1 },
    { day: "Tue", value: 10.9 },
    { day: "Wed", value: 9.8 },
    { day: "Thu", value: 10.6 },
    { day: "Fri", value: 11.3 },
    { day: "Sat", value: 8.9 },
    { day: "Sun", value: 8.3 },
  ],
}

const chartConfig = {
  value: {
    label: "Value",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig

interface ForecastChartProps {
  type: string
}

export function ForecastChart({ type }: ForecastChartProps) {
  const data = forecastData[type as keyof typeof forecastData] || forecastData.kwh

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
