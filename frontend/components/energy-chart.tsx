"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const chartData = [
  { time: "00:00", power: 1.2 },
  { time: "02:00", power: 0.9 },
  { time: "04:00", power: 0.8 },
  { time: "06:00", power: 1.5 },
  { time: "08:00", power: 2.8 },
  { time: "10:00", power: 2.4 },
  { time: "12:00", power: 3.2 },
  { time: "14:00", power: 2.9 },
  { time: "16:00", power: 2.6 },
  { time: "18:00", power: 3.5 },
  { time: "20:00", power: 2.8 },
  { time: "22:00", power: 2.1 },
  { time: "24:00", power: 1.5 },
]

const chartConfig = {
  power: {
    label: "Power",
    color: "hsl(var(--chart-1))",
  },
} satisfies ChartConfig

export function EnergyChart() {
  return (
    <ChartContainer config={chartConfig} className="h-[300px] w-full">
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="fillPower" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-power)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="var(--color-power)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} className="text-xs" />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          className="text-xs"
          tickFormatter={(value) => `${value}kW`}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area type="monotone" dataKey="power" stroke="var(--color-power)" strokeWidth={2} fill="url(#fillPower)" />
      </AreaChart>
    </ChartContainer>
  )
}
