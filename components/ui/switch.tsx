import * as React from "react"
import * as SwitchPrimitives from "@radix-ui/react-switch"

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <div className="flex items-center">
    <SwitchPrimitives.Root
      className={
        `peer inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-all duration-200 ease-in-out
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background
        disabled:cursor-not-allowed disabled:opacity-50
        data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-300
        hover:data-[state=unchecked]:bg-gray-400
        active:scale-95`
      }
      {...props}
      ref={ref}
    >
      <SwitchPrimitives.Thumb
        className={
          `pointer-events-none block h-6 w-6 rounded-full bg-white shadow-lg ring-0 transition-transform duration-200 ease-in-out
          data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0.5`
        }
      />
    </SwitchPrimitives.Root>
  </div>
))

Switch.displayName = "Switch"

export { Switch }
