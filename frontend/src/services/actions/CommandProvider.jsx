import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTransition } from '@/services/transition'
import { CommandContext } from './context'
import { findActionForEvent, isMac } from './registry'
import { CommandPalette } from './CommandPalette'
import { ShortcutSheet } from './ShortcutSheet'
import { CliConsole } from './CliConsole'

function isTypingTarget(el) {
  if (!el) return false
  const tag = el.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (el.isContentEditable) return true
  return false
}

export function CommandProvider({ children }) {
  const { navigate } = useTransition()
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [sheetOpen, setSheetOpen] = useState(false)
  const [consoleOpen, setConsoleOpen] = useState(false)
  const mac = isMac()

  const openPalette = useCallback(() => {
    setSheetOpen(false)
    setConsoleOpen(false)
    setPaletteOpen(true)
  }, [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])
  const openSheet = useCallback(() => {
    setPaletteOpen(false)
    setConsoleOpen(false)
    setSheetOpen(true)
  }, [])
  const closeSheet = useCallback(() => setSheetOpen(false), [])
  const openConsole = useCallback(() => {
    setPaletteOpen(false)
    setSheetOpen(false)
    setConsoleOpen(true)
  }, [])
  const closeConsole = useCallback(() => setConsoleOpen(false), [])

  const ctx = useMemo(
    () => ({
      navigate,
      openPalette,
      closePalette,
      openSheet,
      closeSheet,
      openConsole,
      closeConsole,
      paletteOpen,
      sheetOpen,
      consoleOpen,
    }),
    [
      navigate,
      openPalette,
      closePalette,
      openSheet,
      closeSheet,
      openConsole,
      closeConsole,
      paletteOpen,
      sheetOpen,
      consoleOpen,
    ],
  )

  const runAction = useCallback((action) => action && action.run(ctx), [ctx])

  useEffect(() => {
    function onKey(event) {
      if (event.defaultPrevented) return
      const action = findActionForEvent(event, mac)
      if (!action) return
      const usesMod = Boolean(action.shortcut.mod)
      if ((!usesMod || action.skipWhenTyping) && isTypingTarget(event.target)) return
      event.preventDefault()
      action.run(ctx)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [ctx, mac])

  const value = useMemo(
    () => ({
      openPalette,
      closePalette,
      openSheet,
      closeSheet,
      openConsole,
      closeConsole,
      runAction,
      paletteOpen,
      sheetOpen,
      consoleOpen,
    }),
    [
      openPalette,
      closePalette,
      openSheet,
      closeSheet,
      openConsole,
      closeConsole,
      runAction,
      paletteOpen,
      sheetOpen,
      consoleOpen,
    ],
  )

  return (
    <CommandContext.Provider value={value}>
      {children}
      {paletteOpen && <CommandPalette onClose={closePalette} onRun={runAction} mac={mac} />}
      {sheetOpen && <ShortcutSheet onClose={closeSheet} mac={mac} />}
      {consoleOpen && <CliConsole onClose={closeConsole} ctx={ctx} />}
    </CommandContext.Provider>
  )
}
