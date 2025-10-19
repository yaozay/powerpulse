"use client"

import { Navigation } from "@/components/navigation"
import { NowSection } from "@/components/now-section"
import { ForecastSection } from "@/components/forecast-section"
import { DevicesSection } from "@/components/devices-section"
import { CoachSection } from "@/components/coach-section"

export default function Home() {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <NowSection />
        <ForecastSection />
        <DevicesSection />
        <CoachSection homeId={1} /> 
      </main>
    </div>
  )
}
