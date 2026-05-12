import * as React from "react"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { Card, CardHeader, CardBody, CardFooter } from "@/components/ui/Card"
import { Input } from "@/components/ui/Input"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/Select"
import { Switch } from "@/components/ui/Switch"
import { Avatar } from "@/components/ui/Avatar"
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/Tooltip"
import { SkeletonLoader } from "@/components/ui/SkeletonLoader"
import { Search, Mail } from "lucide-react"

export default function Showcase() {
  const [theme, setTheme] = React.useState<"dark" | "light">("dark")

  React.useEffect(() => {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light")
    } else {
      document.documentElement.removeAttribute("data-theme")
    }
  }, [theme])

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-bg-base p-8 text-primary font-ui">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex justify-between items-center border-b border-border-subtle pb-6">
            <h1 className="text-3xl font-bold">CashPilot Design System</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-secondary">Theme:</span>
              <Switch 
                checked={theme === "light"} 
                onCheckedChange={(c) => setTheme(c ? "light" : "dark")} 
              />
            </div>
          </div>

          <section className="space-y-6">
            <h2 className="text-xl font-semibold border-b border-border-subtle pb-2">Buttons</h2>
            <div className="flex flex-wrap gap-4 items-center">
              <Button intent="primary">Primary</Button>
              <Button intent="ghost">Ghost</Button>
              <Button intent="danger">Danger</Button>
              <Button intent="outline">Outline</Button>
              <Button disabled>Disabled</Button>
              <Button size="sm">Small</Button>
              <Button size="lg">Large</Button>
              <Button size="icon"><Search className="h-4 w-4" /></Button>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-semibold border-b border-border-subtle pb-2">Badges</h2>
            <div className="flex flex-wrap gap-4">
              <Badge intent="critical">CRITICAL</Badge>
              <Badge intent="warning">WARNING</Badge>
              <Badge intent="info">INFO</Badge>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-semibold border-b border-border-subtle pb-2">Inputs & Controls</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-secondary">Standard Input</label>
                <Input placeholder="Enter something..." />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-secondary">With Icons</label>
                <Input leftIcon={<Search className="h-4 w-4" />} rightIcon={<Mail className="h-4 w-4" />} placeholder="Search..." />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-secondary">Disabled Input</label>
                <Input disabled placeholder="Cannot type here" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-secondary">Select</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an option" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Option 1</SelectItem>
                    <SelectItem value="2">Option 2</SelectItem>
                    <SelectItem value="3">Option 3</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-secondary">Switch</label>
                <div><Switch /></div>
              </div>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-semibold border-b border-border-subtle pb-2">Avatars & Tooltips</h2>
            <div className="flex items-center gap-8">
              <Avatar fallback="JD" name="John Doe" />
              <Avatar fallback="AM" name="Alice Morris" />
              <Avatar fallback="WS" name="William Smith" />
              <Avatar src="https://github.com/shadcn.png" fallback="CN" />
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button intent="outline">Hover me</Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>This is a tooltip from Radix UI</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-semibold border-b border-border-subtle pb-2">Cards</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Card Title</h3>
                  <p className="text-sm text-secondary">A subtle description</p>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-tertiary">This is the body content of the card. It has some padding and uses the semantic colors.</p>
                </CardBody>
                <CardFooter className="justify-end gap-2">
                  <Button intent="ghost" size="sm">Cancel</Button>
                  <Button size="sm">Save</Button>
                </CardFooter>
              </Card>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-semibold border-b border-border-subtle pb-2">Skeleton Loaders</h2>
            <div className="space-y-8">
              <div>
                <h3 className="text-sm font-medium text-secondary mb-4">Variant: kpi-grid</h3>
                <SkeletonLoader variant="kpi-grid" />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-sm font-medium text-secondary mb-4">Variant: chart</h3>
                  <SkeletonLoader variant="chart" />
                </div>
                <div className="space-y-8">
                  <div>
                    <h3 className="text-sm font-medium text-secondary mb-4">Variant: list</h3>
                    <SkeletonLoader variant="list" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-secondary mb-4">Variant: table</h3>
                    <SkeletonLoader variant="table" />
                  </div>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </TooltipProvider>
  )
}
