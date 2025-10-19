// components/add-device-modal.tsx
import * as React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { Device } from "@/lib/api"

export type AddDeviceModalValues = {
  name: string
  source?: Device["source"]   // 'app' | 'plug'
  powerLabel?: string
  lastSeen?: string
}

export type AddDeviceModalProps = {
  open: boolean
  onOpenChange: (v: boolean) => void
  /** NEW: called when user submits the form */
  onSubmit: (values: AddDeviceModalValues) => void
}

export function AddDeviceModal({ open, onOpenChange, onSubmit }: AddDeviceModalProps) {
  const [name, setName] = React.useState("")
  const [source, setSource] = React.useState<Device["source"]>("app")
  const [powerLabel, setPowerLabel] = React.useState("—")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      name: name.trim(),
      source,
      powerLabel: powerLabel?.trim() || "—",
    })
    onOpenChange(false)
    setName("")
    setPowerLabel("—")
    setSource("app")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add device</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="dev-name">Name</Label>
            <Input id="dev-name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>

          <div className="space-y-2">
            <Label htmlFor="dev-source">Source</Label>
            <select
              id="dev-source"
              className="w-full rounded-md border bg-background p-2 text-sm"
              value={source}
              onChange={(e) => setSource(e.target.value as Device["source"])}
            >
              <option value="app">via App</option>
              <option value="plug">via Plug</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="dev-power">Power label</Label>
            <Input
              id="dev-power"
              placeholder="e.g. 0.150 kWh (last reading)"
              value={powerLabel}
              onChange={(e) => setPowerLabel(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Add</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}