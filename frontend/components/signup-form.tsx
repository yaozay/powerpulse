"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useSignUp } from "@clerk/nextjs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"

export function SignUpForm() {
  const router = useRouter()
  const { isLoaded, signUp, setActive } = useSignUp()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [code, setCode] = useState("")
  const [pendingVerification, setPendingVerification] = useState(false)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Step 1: Sign up
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoaded) return
    setIsLoading(true)
    setError(null)

    try {
      const result = await signUp.create({
        emailAddress: email,
        password,
      })

      if (result.status === "complete") {
        // Assign sequential homeId
        await fetch("/api/assign-home-id", {
          method: "POST",
          body: JSON.stringify({ userId: result.user.id }),
        })

        await setActive({ session: result.createdSessionId })
        router.push("/")
      } else {
        // Require verification
        await signUp.prepareEmailAddressVerification({ strategy: "email_code" })
        setPendingVerification(true)
      }
    } catch (err: any) {
      console.error("Signup error:", err)
      setError(err.errors?.[0]?.longMessage || err.message || "Something went wrong")
    } finally {
      setIsLoading(false)
    }
  }

  // Step 2: Verify email code
  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoaded) return
    setIsLoading(true)
    setError(null)

    try {
      const result = await signUp.attemptEmailAddressVerification({ code })

      if (result.status === "complete") {
        // Assign sequential homeId
        await fetch("/api/assign-home-id", {
          method: "POST",
          body: JSON.stringify({ userId: result.user.id }),
        })

        await setActive({ session: result.createdSessionId })
        router.push("/")
      } else {
        console.log("Verification step:", result)
      }
    } catch (err: any) {
      console.error("Verification error:", err)
      setError(err.errors?.[0]?.longMessage || err.message || "Verification failed")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="p-8 shadow-lg">
      {!pendingVerification ? (
        // ---------- Step 1: Sign Up ----------
        <form onSubmit={handleSignUp} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
              className="h-11"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder=""
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
              className="h-11"
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button type="submit" className="h-11 w-full font-medium" disabled={isLoading}>
            {isLoading ? "Creating account..." : "Sign up"}
          </Button>

          <div className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <a href="/login" className="text-primary hover:underline">Sign in</a>
          </div>
        </form>
      ) : (
        // ---------- Step 2: Verify ----------
        <form onSubmit={handleVerify} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="code">Verification Code</Label>
            <Input
              id="code"
              type="text"
              placeholder="Enter the code from your email"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              disabled={isLoading}
              className="h-11"
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button type="submit" className="h-11 w-full font-medium" disabled={isLoading}>
            {isLoading ? "Verifying..." : "Verify Email"}
          </Button>
        </form>
      )}
    </Card>
  )
}
