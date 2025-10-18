import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Lightbulb, TrendingDown, Clock, Sparkles } from "lucide-react"

const suggestions = [
  {
    icon: Lightbulb,
    title: "Upgrade Your Refrigerator",
    message:
      "Your fridge is using 15% more energy than average. Consider upgrading to an Energy Star certified model to save $120/year.",
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  {
    icon: TrendingDown,
    title: "Reduce Peak Usage",
    message:
      "Your energy usage peaks between 6-8 PM. Try running your dishwasher and laundry during off-peak hours to save on costs.",
    color: "text-secondary",
    bgColor: "bg-secondary/10",
  },
  {
    icon: Clock,
    title: "Schedule AC Smartly",
    message:
      "Set your AC to 78°F when away and 72°F when home. This could reduce cooling costs by up to 25% this summer.",
    color: "text-chart-3",
    bgColor: "bg-chart-3/10",
  },
  {
    icon: Sparkles,
    title: "Great Job This Week!",
    message: "You've reduced your energy consumption by 12% compared to last week. Keep up the excellent work!",
    color: "text-chart-2",
    bgColor: "bg-chart-2/10",
  },
]

export function CoachSection() {
  return (
    <section id="coach" className="py-12 pb-24">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold text-balance">AI Energy Coach</h2>
        <p className="text-lg text-muted-foreground">Personalized recommendations to optimize your energy usage</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {suggestions.map((suggestion) => {
          const Icon = suggestion.icon
          return (
            <Card key={suggestion.title} className="transition-shadow hover:shadow-lg">
              <CardContent className="pt-6">
                <div className="mb-4 flex items-start gap-4">
                  <div
                    className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg", suggestion.bgColor)}
                  >
                    <Icon className={cn("h-5 w-5", suggestion.color)} />
                  </div>
                  <div className="flex-1">
                    <h3 className="mb-2 font-semibold">{suggestion.title}</h3>
                    <p className="text-sm leading-relaxed text-muted-foreground">{suggestion.message}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">
                    Snooze
                  </Button>
                  <Button size="sm">Apply</Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </section>
  )
}
