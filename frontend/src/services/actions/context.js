import { createContext, useContext } from 'react'

export const CommandContext = createContext({
  openPalette: () => {},
  closePalette: () => {},
  openSheet: () => {},
  closeSheet: () => {},
  openConsole: () => {},
  closeConsole: () => {},
  runAction: () => {},
  paletteOpen: false,
  sheetOpen: false,
  consoleOpen: false,
})

export function useCommands() {
  return useContext(CommandContext)
}
