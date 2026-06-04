import i18n from './config'

export function messageForError(error, translate) {
  const t = translate || i18n.t.bind(i18n)
  const code = error?.data?.code || error?.code
  if (code) {
    const key = `errors:${code}`
    if (i18n.exists(key)) return t(key)
  }
  const details = error?.data?.details
  if (Array.isArray(details) && details.length) {
    return details.map((d) => d.msg).filter(Boolean).join(' · ')
  }
  if (error?.message) return error.message
  return t('errors:error.bad_request')
}
