"use client"

import { useEffect, useState } from "react"
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { loadDailyUsageByHour } from "@/lib/loadDailyUsage"

type Point = { time: string; kwh: number }

export function EnergyChart({
  homeId,
  date, // optional "M/D/YY" (e.g., "6/15/23"); if omitted, uses latest in the file
}: {
  homeId: string
  date?: string
}) {
  const [data, setData] = useState<Point[]>([])

  useEffect(() => {
    loadDailyUsageByHour(homeId, date).then(setData).catch(console.error)
  }, [homeId, date])

  const chartConfig = {
    kwh: { label: "Energy (kWh)", color: "hsl(var(--chart-1))" },
  } as const

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
        <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} className="text-xs" />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          className="text-xs"
          tickFormatter={(v) => `${v} kWh`}
          domain={[0, "dataMax + 1"]}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area type="monotone" dataKey="kwh" stroke="var(--color-kwh, var(--chart-1))" strokeWidth={2} fill="url(#fillKWh)" />
      </AreaChart>
    </ChartContainer>
  )
}