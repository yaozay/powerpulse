// components/device-details-modal.tsx
"use client"

import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  Activity, Zap, AirVent, Refrigerator as RefrigeratorIcon, Lightbulb, Tv, Waves,
  Computer, Microwave, WashingMachine, HousePlug
} from "lucide-react"
import { getDeviceStats, type DeviceStats } from "@/lib/api"

type DeviceStatus = "online" | "offline" | "unknown"
type DeviceSource = "app" | "plug"
interface Device {
  name: string
  powerLabel: string
  status: DeviceStatus
  source: DeviceSource
  lastSeen?: string
}

const iconMap = [
  { test: (n: string) => /air|ac|conditioning/i.test(n), Icon: AirVent },
  { test: (n: string) => /fridge|refrigerator/i.test(n), Icon: RefrigeratorIcon },
  { test: (n: string) => /lamp|light/i.test(n), Icon: Lightbulb },
  { test: (n: string) => /tv|television/i.test(n), Icon: Tv },
  { test: (n: string) => /wash(ing)?\s*machine/i.test(n), Icon: WashingMachine },
  { test: (n: string) => /dishwasher/i.test(n), Icon: Waves },
  { test: (n: string) => /microwave/i.test(n), Icon: Microwave },
  { test: (n: string) => /computer|pc|laptop/i.test(n), Icon: Computer },
]
function pickIcon(name: string) {
  const hit = iconMap.find((m) => m.test(name))
  return hit?.Icon ?? HousePlug
}

interface DeviceDetailsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  device: Device | null
  homeId?: number | string
}

export function DeviceDetailsModal({ open, onOpenChange, device, homeId = 1 }: DeviceDetailsModalProps) {
  const [stats, setStats] = useState<DeviceStats | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let ignore = false
    async function load() {
      if (!open || !device?.name) {
        setStats(null)
        return
      }
      try {
        setLoading(true)
        const s = await getDeviceStats(homeId, device.name)
        if (!ignore) setStats(s)
      } catch {
        if (!ignore) setStats(null)
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    load()
    return () => {
      ignore = true
    }
  }, [open, homeId, device?.name])

  if (!device) return null
  const Icon = pickIcon(device.name)

  const currentPower = device.powerLabel || "—"
  const lastActive = device.lastSeen ? new Date(device.lastSeen).toLocaleString() : "—"

  const dailyUsage   = loading ? "…" : stats ? `${stats.daily_kwh} kWh` : "—"
  const monthlyUsage = loading ? "…" : stats ? `${stats.monthly_kwh} kWh` : "—"
  const avgRuntime   = loading ? "…" : stats ? `${Math.floor(stats.avg_runtime_hours)}h ${Math.round((stats.avg_runtime_hours % 1) * 60)}m` : "—"
  const peakHours    = loading ? "…" : (stats?.peak_hour ?? "—")

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
              <Icon className="h-6 w-6 text-foreground" />
            </div>
            <div>
              <DialogTitle className="text-2xl">{device.name}</DialogTitle>
              <div className="flex items-center gap-2 mt-1">
                <div
                  className={cn(
                    "h-2 w-2 rounded-full",
                    device.status === "online" ? "bg-secondary" : "bg-muted-foreground",
                  )}
                />
                <span className="text-sm text-muted-foreground capitalize">{device.status}</span>
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 pt-4">
    <Card className="h-40 flex items-center justify-center">
    <CardContent className="flex flex-col items-center justify-center text-center space-y-2">
        <div className="flex items-center gap-3 text-muted-foreground">
        <Zap className="h-6 w-6" />
        <span className="text-lg font-medium">Current Power</span>
        </div>
        <p className="text-4xl font-extrabold text-foreground">{currentPower}</p>
    </CardContent>
    </Card>

          <div className="space-y-3">
            <h3 className="font-semibold">Usage Statistics</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                <span className="text-sm text-muted-foreground">Daily Usage</span>
                <span className="font-semibold">{dailyUsage}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                <span className="text-sm text-muted-foreground">Monthly Usage</span>
                <span className="font-semibold">{monthlyUsage}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                <span className="text-sm text-muted-foreground">Avg. Runtime</span>
                <span className="font-semibold">{avgRuntime}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                <span className="text-sm text-muted-foreground">Peak Hours</span>
                <span className="font-semibold">{peakHours}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div
              className={cn(
                "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
                device.source === "plug" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground",
              )}
              title={device.source === "plug" ? "Reported via PowerPulse Plug" : "Reported via App cloud link"}
            >
              {device.source === "plug" ? "via Plug" : "via App"}
            </div>
            {device.status === "online" && (
              <p className="text-xs text-muted-foreground">Last active: {lastActive}</p>
            )}
          </div>

          <Button className="w-full" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}