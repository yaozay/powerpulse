import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Refrigerator, AirVent, Lightbulb, Tv, Waves } from "lucide-react"
import { cn } from "@/lib/utils"

const devices = [
  {
    name: "Refrigerator",
    power: "120W",
    status: "online",
    smart: "Smart",
    icon: Refrigerator,
  },
  {
    name: "Air Conditioner",
    power: "1,800W",
    status: "online",
    smart: "Smart",
    icon: AirVent,
  },
  {
    name: "Living Room Lamp",
    power: "15W",
    status: "online",
    smart: "Smart",
    icon: Lightbulb,
  },
  {
    name: "TV",
    power: "85W",
    status: "offline",
    smart: "Unknown",
    icon: Tv,
  },
  {
    name: "Washing Machine",
    power: "0W",
    status: "offline",
    smart: "Not Smart",
    icon: Waves,
  },
]

export function DevicesSection() {
  return (
    <section id="devices" className="py-12">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h2 className="mb-2 text-3xl font-bold text-balance">Connected Devices</h2>
          <p className="text-lg text-muted-foreground">Monitor and control your smart home devices</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Add Device
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {devices.map((device) => {
          const Icon = device.icon
          return (
            <Card key={device.name} className="transition-shadow hover:shadow-lg">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                      <Icon className="h-5 w-5 text-foreground" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{device.name}</CardTitle>
                      <p className="text-sm text-muted-foreground">{device.power}</p>
                    </div>
                  </div>
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      device.status === "online" ? "bg-secondary" : "bg-muted-foreground",
                    )}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div
                  className={cn(
                    "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
                    device.smart === "Smart"
                      ? "bg-primary/10 text-primary"
                      : device.smart === "Unknown"
                        ? "bg-muted text-muted-foreground"
                        : "bg-destructive/10 text-destructive",
                  )}
                >
                  {device.smart}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </section>
  )
}
