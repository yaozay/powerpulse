// components/devices-section.tsx
"use client"

import { useEffect, useMemo, useState, useRef } from "react"
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
  Cpu,
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
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)
  const sectionRef = useRef<HTMLElement>(null)

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

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible")
          }
        })
      },
      { threshold: 0.1 }
    )

    const elements = sectionRef.current?.querySelectorAll(".scroll-animate")
    elements?.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [loading])

  const handleAddDevice = (newDevice: Partial<Device> & { name: string }) => {
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
    if (error) return "Couldn't load devices."
    return `${devices.length} connected device${devices.length === 1 ? "" : "s"}`
  }, [loading, error, devices.length])

  return (
    <section ref={sectionRef} id="devices" className="py-12 relative">
      <div className="mb-12 scroll-animate">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 mb-4 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <Cpu className="h-4 w-4" />
              <span>Smart Home</span>
            </div>
            <h2 className="mb-4 text-4xl md:text-5xl font-bold text-balance bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Connected Devices
            </h2>
            <p className="text-xl text-muted-foreground">{subtitle}</p>
          </div>
          <Button 
            className="gap-2 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-r from-primary to-secondary"
            onClick={() => setIsAddModalOpen(true)}
          >
            <Plus className="h-4 w-4" />
            Add Device
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl glass border-destructive/50 p-4 text-destructive scroll-animate">
          {error}
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {!loading &&
          !error &&
          devices.map((device, index) => {
            const Icon = pickIcon(device.name)
            return (
              <Card
                key={`${device.name}-${device.lastSeen ?? ""}`}
                className={cn(
                  "scroll-animate group relative overflow-hidden border-0 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 cursor-pointer",
                  "bg-gradient-to-br from-card to-card/50"
                )}
                style={{ animationDelay: `${index * 50}ms` }}
                onClick={() => handleDeviceClick(device)}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-2xl -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500" />
                
                <CardHeader className="relative z-10">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "flex h-12 w-12 items-center justify-center rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300",
                        "bg-gradient-to-br from-muted to-muted/50 backdrop-blur-sm"
                      )}>
                        <Icon className="h-6 w-6 text-foreground" />
                      </div>
                      <div>
                        <CardTitle className="text-lg group-hover:text-primary transition-colors duration-300">
                          {device.name}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground font-medium mt-1">{device.powerLabel}</p>
                      </div>
                    </div>
                    <div className="relative">
                      <div
                        className={cn(
                          "h-3 w-3 rounded-full shadow-lg",
                          device.status === "online"
                            ? "bg-secondary animate-pulse"
                            : device.status === "offline"
                            ? "bg-muted-foreground"
                            : "bg-border",
                        )}
                        title={device.status}
                      />
                      {device.status === "online" && (
                        <div className="absolute inset-0 h-3 w-3 rounded-full bg-secondary animate-ping opacity-75" />
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="flex items-center gap-2 relative z-10">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium shadow-sm",
                      device.source === "plug" 
                        ? "bg-primary/20 text-primary border border-primary/30" 
                        : "bg-muted/50 text-muted-foreground border border-border",
                    )}
                    title={device.source === "plug" ? "Reported via PowerPulse Plug" : "Reported via App cloud link"}
                  >
                    {device.source === "plug" ? "via Plug" : "via App"}
                  </span>

                  {device.lastSeen && (
                    <span className="text-xs text-muted-foreground">
                      {new Date(device.lastSeen).toLocaleDateString()}
                    </span>
                  )}
                </CardContent>
              </Card>
            )
          })}
      </div>

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