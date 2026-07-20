const MAX = 20

let stack = []

export function pushUndo(entry) {
  stack.push(entry)
  if (stack.length > MAX) stack = stack.slice(-MAX)
}

export function popUndo() {
  return stack.pop() || null
}

export function undoDepth() {
  return stack.length
}
