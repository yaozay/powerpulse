import { LoginForm } from "@/components/login-form"
import { Zap } from "lucide-react"

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-4 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary">
              <Zap className="h-8 w-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="mb-2 font-sans text-3xl font-semibold text-foreground">Welcome to PowerPulse</h1>
          <p className="text-muted-foreground">Sign in for managing your home energy</p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}
