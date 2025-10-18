"use client"

import { useState, useEffect } from "react"
import { Zap, LogOut, User } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const navItems = [
  { id: "now", label: "Now" },
  { id: "forecast", label: "Forecast" },
  { id: "devices", label: "Devices" },
  { id: "coach", label: "Coach" },
]

export function Navigation() {
  const [activeSection, setActiveSection] = useState("now")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userEmail, setUserEmail] = useState("")

  useEffect(() => {
    const handleScroll = () => {
      const sections = navItems.map((item) => item.id)
      const scrollPosition = window.scrollY + 200

      for (const section of sections) {
        const element = document.getElementById(section)
        if (element) {
          const { offsetTop, offsetHeight } = element
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section)
            break
          }
        }
      }
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  useEffect(() => {
    const authToken = localStorage.getItem("powerpulse_auth")
    const email = localStorage.getItem("powerpulse_email")
    if (authToken && email) {
      setIsAuthenticated(true)
      setUserEmail(email)
    }
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

  const handleLogout = () => {
    localStorage.removeItem("powerpulse_auth")
    localStorage.removeItem("powerpulse_email")
    setIsAuthenticated(false)
    setUserEmail("")
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-semibold">PowerPulse</span>
          </div>

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

            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-9 w-9 rounded-xl">
                    <User className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <div className="px-2 py-1.5 text-sm text-muted-foreground">{userEmail}</div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button asChild variant="default" size="sm" className="rounded-xl">
                <Link href="/login">Login</Link>
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
