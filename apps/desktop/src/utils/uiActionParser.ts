export interface UIAction {
  type: string
  payload?: string
}

export function parseUIActions(text: string): {
  cleanText: string
  actions: UIAction[]
} {
  const actions: UIAction[] = []
  const ACTION_REGEX = /\[UI_ACTION:([^\]]+)\]/g
  
  let match
  while ((match = ACTION_REGEX.exec(text)) !== null) {
    const actionStr = match[1]
    const colonIdx = actionStr.indexOf(":")
    if (colonIdx === -1) {
      actions.push({ type: actionStr })
    } else {
      actions.push({
        type: actionStr.substring(0, colonIdx),
        payload: actionStr.substring(colonIdx + 1)
      })
    }
  }
  
  // Remove all action tags from displayed text
  const cleanText = text
    .replace(ACTION_REGEX, "")
    .trim()
  
  return { cleanText, actions }
}
