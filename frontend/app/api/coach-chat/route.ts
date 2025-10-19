import { NextResponse } from "next/server"

export const dynamic = "force-dynamic"

const BACKEND_BASE =
  (process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "")

export async function POST(request: Request) {
  const payload = await request.json()

  try {
    const res = await fetch(`${BACKEND_BASE}/coach/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })

    const text = await res.text()
    let data: unknown
    try {
      data = text ? JSON.parse(text) : {}
    } catch {
      data = { message: text }
    }

    if (!res.ok) {
      return NextResponse.json(
        { error: "coach_backend_error", details: data },
        { status: res.status }
      )
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error("Coach proxy error", error)
    return NextResponse.json(
      { error: "coach_proxy_failed", message: "Unable to reach coach backend." },
      { status: 502 }
    )
  }
}
