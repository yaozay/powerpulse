'use client'

import { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Lightbulb, TrendingDown, Bot } from "lucide-react"

type ChatMessage = {
  role: "user" | "assistant"
  content: string
}

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
const COACH_CHAT_ENDPOINT = `${API_BASE}/coach/chat`;

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
]

export function CoachSection() {
  const leftColumn = suggestions
  const chatCard = {
    icon: Bot,
    title: "Chat with PowerPulse Coach",
    message:
      "Ask about peak-hour strategies, comfort tips, or general energy questions—the assistant responds with ideas you can act on right away.",
    color: "text-chart-3",
    bgColor: "bg-chart-3/10",
  }
  const FeatureIcon = chatCard.icon

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I’m the PowerPulse Coach bot. Ask anything about your energy usage, peak events, or savings ideas and I’ll brainstorm with you."
    }
  ])
  const [draft, setDraft] = useState("")
  const [isThinking, setIsThinking] = useState(false)
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isThinking])

  const sendToCoach = async (history: ChatMessage[]): Promise<string> => {
  try {
    // 1) Sanitize payload: removes undefined / non-JSON-serializable bits safely
    const payload = {
      messages: history.map(m => ({
        role: m.role === "assistant" ? "assistant" : "user", // normalize
        content: String(m.content ?? "")
      })),
      persona: "eco",
      context: {} // include an explicit context to satisfy stricter backends
    };
    // Drop any undefined by a round-trip
    const safeBody = JSON.stringify(JSON.parse(JSON.stringify(payload)));

    const res = await fetch(COACH_CHAT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: safeBody,
    });

    if (!res.ok) {
      // 2) Log exact server text so you can see where JSON parsing failed
      const errText = await res.text();
      console.error("Coach reply failed:", res.status, errText);
      throw new Error(`Coach reply failed with status ${res.status}`);
    }

    const data = await res.json().catch(async () => {
      // If server didn’t return JSON, show raw body for debugging
      const txt = await res.text();
      console.error("Non-JSON server response:", txt);
      return { message: "" };
    });

    const message = typeof data?.message === "string" ? data.message.trim() : "";
    return message || "Sorry—no reply received.";
  } catch (error) {
    console.error("Coach chat error", error);
    return "Sorry—something went wrong sending that.";
  }
};


  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text) return

    const nextHistory: ChatMessage[] = [...messages, { role: "user", content: text }]
    setMessages(nextHistory)
    setDraft("")
    setIsThinking(true)

    try {
      const reply = await sendToCoach(nextHistory)
      setMessages((prev) => [...prev, { role: "assistant", content: reply }])
    } finally {
      setIsThinking(false)
    }
  }

  return (
    <section id="coach" className="py-12 pb-24">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold text-balance">AI Energy Coach</h2>
        <p className="text-lg text-muted-foreground">Personalized recommendations to optimize your energy usage</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-stretch">
        <div className="grid gap-4 sm:grid-cols-2 lg:h-[520px] lg:grid-cols-1 lg:grid-rows-2">
          {leftColumn.map((suggestion) => {
            const Icon = suggestion.icon
            return (
              <Card key={suggestion.title} className="transition-shadow hover:shadow-lg lg:flex lg:h-full lg:flex-col">
                <CardContent className="flex flex-1 flex-col pt-6">
                  <div className="mb-4 flex items-start gap-4">
                    <div
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                        suggestion.bgColor
                      )}
                    >
                      <Icon className={cn("h-5 w-5", suggestion.color)} />
                    </div>
                    <div className="flex-1">
                      <h3 className="mb-2 font-semibold">{suggestion.title}</h3>
                      <p className="text-sm leading-relaxed text-muted-foreground">{suggestion.message}</p>
                    </div>
                  </div>
                  <div className="mt-auto flex gap-2">
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

        {FeatureIcon && (
          <Card className="transition-shadow hover:shadow-lg min-h-0 lg:flex lg:h-[520px] lg:max-h-[520px] lg:flex-col">
            <CardContent className="flex h-full min-h-0 flex-col pt-6">
              <div className="mb-6 flex items-start gap-4">
                <div
                  className={cn(
                    "flex h-12 w-12 shrink-0 items-center justify-center rounded-lg",
                    chatCard.bgColor
                  )}
                >
                  <FeatureIcon className={cn("h-6 w-6", chatCard.color)} />
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold">{chatCard.title}</h3>
                  <p className="text-base leading-relaxed text-muted-foreground">{chatCard.message}</p>
                </div>
              </div>
              <ScrollArea className="flex-1 min-h-0 pr-2">
                <div className="space-y-4 pb-2">
                  {messages.map((message, index) => (
                    <div
                      key={`${message.role}-${index}-${message.content.slice(0, 12)}`}
                      className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}
                    >
                      <div
                        className={cn(
                          "max-w-[80%] rounded-lg px-4 py-3 text-sm shadow-sm",
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {message.content}
                      </div>
                    </div>
                  ))}
                  {isThinking && (
                    <div className="flex justify-start">
                      <div className="bg-muted text-muted-foreground/80 max-w-[75%] rounded-lg px-4 py-3 text-sm">
                        Thinking…
                      </div>
                    </div>
                  )}
                  <div ref={endRef} />
                </div>
              </ScrollArea>
              <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
                <Textarea
                  placeholder="Ask about peak rates, thermostat tweaks, or appliance schedules…"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  rows={3}
                  className="resize-none"
                />
                <div className="flex justify-end gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isThinking || draft.trim().length === 0}
                  >
                    {isThinking ? "Working…" : "Send"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  )
}
