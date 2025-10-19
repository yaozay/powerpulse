"use client"

import { useState, useEffect } from "react"
import { Zap } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { SignedIn, SignedOut, UserButton, useUser } from "@clerk/nextjs"

const navItems = [
  { id: "now", label: "Now" },
  { id: "forecast", label: "Forecast" },
  { id: "devices", label: "Devices" },
  { id: "coach", label: "Coach" },
]

export function Navigation() {
  const [activeSection, setActiveSection] = useState("now")
  const { user } = useUser()

  useEffect(() => {
    const handleScroll = () => {
      const sections = navItems.map((item) => item.id)
      const scrollPosition = window.scrollY + 200

      for (const section of sections) {
        const element = document.getElementById(section)
        if (element) {
          const { offsetTop, offsetHeight } = element
          if (
            scrollPosition >= offsetTop &&
            scrollPosition < offsetTop + offsetHeight
          ) {
            setActiveSection(section)
            break
          }
        }
      }
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      const offset = 100
      const elementPosition = element.offsetTop - offset
      window.scrollTo({
        top: elementPosition,
        behavior: "smooth",
      })
    }
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-semibold">PowerPulse</span>
          </div>

          {/* Nav buttons + Auth */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-full bg-muted p-1">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={cn(
                    "rounded-full px-4 py-1.5 text-sm font-medium transition-all",
                    activeSection === item.id
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Signed in → show user info + logout */}
            <SignedIn>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {user?.firstName || user?.emailAddresses[0]?.emailAddress}
                </span>

                <UserButton afterSignOutUrl="/" />
              </div>
            </SignedIn>

            {/* Signed out → show login button */}
            <SignedOut>
              <Button asChild variant="default" size="sm" className="rounded-xl">
                <Link href="/login">Login</Link>
              </Button>
            </SignedOut>
          </div>
        </div>
      </div>
    </nav>
  )
}
