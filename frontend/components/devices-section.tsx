// components/devices-section.tsx
"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"
import {
  Plus,
  Refrigerator as RefrigeratorIcon,
  AirVent,
  Lightbulb,
  Tv,
  Waves,
  Computer,
  Microwave,
  WashingMachine,
  HousePlug,
} from "lucide-react"
import { getDevices, type Device } from "@/lib/api"
import { DeviceDetailsModal } from "./device-details-modal"
import { AddDeviceModal } from "./add-device-modal"

const iconMap: Array<{ test: (n: string) => boolean; Icon: LucideIcon }> = [
  { test: (n) => /air|ac|conditioning/i.test(n), Icon: AirVent },
  { test: (n) => /fridge|refrigerator/i.test(n), Icon: RefrigeratorIcon },
  { test: (n) => /lamp|light/i.test(n), Icon: Lightbulb },
  { test: (n) => /tv|television/i.test(n), Icon: Tv },
  { test: (n) => /wash(ing)?\s*machine/i.test(n), Icon: WashingMachine },
  { test: (n) => /dishwasher/i.test(n), Icon: Waves },
  { test: (n) => /microwave/i.test(n), Icon: Microwave },
  { test: (n) => /computer|pc|laptop/i.test(n), Icon: Computer },
]
function pickIcon(name: string): LucideIcon {
  const hit = iconMap.find((m) => m.test(name))
  return hit?.Icon ?? HousePlug
}

export function DevicesSection({ homeId = 2 }: { homeId?: number | string }) {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // NEW: modal & selection state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)

  useEffect(() => {
    let ignore = false
    ;(async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await getDevices(homeId)
        if (!ignore) setDevices(data)
      } catch (e: any) {
        if (!ignore) setError(e?.message ?? "Failed to load devices")
      } finally {
        if (!ignore) setLoading(false)
      }
    })()
    return () => {
      ignore = true
    }
  }, [homeId])

  // NEW: handlers
  const handleAddDevice = (newDevice: Partial<Device> & { name: string }) => {
    // We render icons from the name, so we only need to add the device data
    // Provide reasonable defaults for optional fields
    const toAdd: Device = {
      name: newDevice.name,
      powerLabel: newDevice.powerLabel ?? "—",
      status: newDevice.status ?? "unknown",
      source: newDevice.source ?? "app",
      lastSeen: newDevice.lastSeen,
    }
    setDevices((prev) => [...prev, toAdd])
  }

  const handleDeviceClick = (device: Device) => {
    setSelectedDevice(device)
    setIsDetailsModalOpen(true)
  }

  const subtitle = useMemo(() => {
    if (loading) return "Loading your devices…"
    if (error) return "Couldn’t load devices."
    return `Home ${homeId} — ${devices.length} device${devices.length === 1 ? "" : "s"}`
  }, [loading, error, devices.length, homeId])

  return (
    <section id="devices" className="py-12">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h2 className="mb-2 text-3xl font-bold text-balance">Connected Devices</h2>
          <p className="text-lg text-muted-foreground">{subtitle}</p>
        </div>
        <Button className="gap-2" onClick={() => setIsAddModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Add Device
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {!loading &&
          !error &&
          devices.map((device) => {
            const Icon = pickIcon(device.name)
            return (
              <Card
                key={`${device.name}-${device.lastSeen ?? ""}`}
                className="transition-shadow hover:shadow-lg cursor-pointer"
                onClick={() => handleDeviceClick(device)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                        <Icon className="h-5 w-5 text-foreground" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{device.name}</CardTitle>
                        <p className="text-sm text-muted-foreground">{device.powerLabel}</p>
                      </div>
                    </div>
                    <div
                      className={cn(
                        "h-2 w-2 rounded-full",
                        device.status === "online"
                          ? "bg-secondary"
                          : device.status === "offline"
                            ? "bg-muted-foreground"
                            : "bg-border",
                      )}
                      title={device.status}
                    />
                  </div>
                </CardHeader>

                <CardContent className="flex items-center gap-2">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
                      device.source === "plug" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground",
                    )}
                    title={device.source === "plug" ? "Reported via PowerPulse Plug" : "Reported via App cloud link"}
                  >
                    {device.source === "plug" ? "via Plug" : "via App"}
                  </span>

                  {device.lastSeen && (
                    <span className="text-xs text-muted-foreground">
                      Last seen: {new Date(device.lastSeen).toLocaleString()}
                    </span>
                  )}
                </CardContent>
              </Card>
            )
          })}
      </div>

      {/* NEW: Modals */}
      <AddDeviceModal
        open={isAddModalOpen}
        onOpenChange={setIsAddModalOpen}
        onSubmit={(values: Partial<Device> & { name: string }) => {
          handleAddDevice(values)
          setIsAddModalOpen(false)
        }}
      />

      <DeviceDetailsModal
          open={isDetailsModalOpen}
          onOpenChange={setIsDetailsModalOpen}
          device={selectedDevice}
          homeId={homeId}
        />
    </section>
  )
}