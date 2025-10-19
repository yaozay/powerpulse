"use client"

import { Navigation } from "@/components/navigation"
import { NowSection } from "@/components/now-section"
import { ForecastSection } from "@/components/forecast-section"
import { DevicesSection } from "@/components/devices-section"
import { CoachSection } from "@/components/coach-section"

export default function Home() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated background gradients */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-primary/5 via-transparent to-transparent animate-pulse-slow blur-3xl" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-secondary/5 via-transparent to-transparent animate-pulse-slow-reverse blur-3xl" />
      </div>
      
      <Navigation />
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <NowSection />
        <ForecastSection />
        <DevicesSection />
        <CoachSection/> 
      </main>
    </div>
  )
}