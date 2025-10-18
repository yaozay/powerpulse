import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Zap, DollarSign, Leaf, TrendingUp } from "lucide-react"
import { EnergyChart } from "@/components/energy-chart"
import { WeatherWidget } from "@/components/weather-widget"

const metrics = [
  {
    title: "Current Power",
    value: "2.4",
    unit: "kW",
    icon: Zap,
    color: "text-primary",
  },
  {
    title: "Today's Usage",
    value: "18.7",
    unit: "kWh",
    icon: TrendingUp,
    color: "text-chart-2",
  },
  {
    title: "Today's Cost",
    value: "$4.23",
    unit: "",
    icon: DollarSign,
    color: "text-chart-3",
  },
  {
    title: "Today's CO₂",
    value: "8.4",
    unit: "kg",
    icon: Leaf,
    color: "text-secondary",
  },
]

export function NowSection() {
  return (
    <section id="now" className="py-12">
      <div className="mb-8">
        <h1 className="mb-2 text-4xl font-bold text-balance">Your Energy at a Glance</h1>
        <p className="text-lg text-muted-foreground">Real-time monitoring of your home energy consumption</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {metrics.map((metric) => {
          const Icon = metric.icon
          return (
            <Card key={metric.title} className="transition-shadow hover:shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{metric.title}</CardTitle>
                <Icon className={cn("h-4 w-4", metric.color)} />
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{metric.value}</span>
                  {metric.unit && <span className="text-sm text-muted-foreground">{metric.unit}</span>}
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
            <EnergyChart />
          </CardContent>
        </Card>

        <WeatherWidget />
      </div>
    </section>
  )
}
