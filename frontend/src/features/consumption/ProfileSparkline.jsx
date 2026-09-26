import { useId } from 'react'

const W = 240
const H = 56
const PAD = 4

function points(values, max) {
  return values
    .map((v, i) => `${(PAD + (i * (W - 2 * PAD)) / 23).toFixed(1)},${(H - PAD - (v / max) * (H - 2 * PAD)).toFixed(1)}`)
    .join(' ')
}

export function ProfileSparkline({ preview }) {
  const titleId = useId()
  const max = Math.max(...preview.hours, ...preview.winter, ...preview.summer, 1e-9)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="cp-spark" role="img" aria-labelledby={titleId}>
      <title id={titleId}>Reparto horario del consumo: media anual, invierno y verano</title>
      <polyline points={points(preview.winter, max)} fill="none" stroke="var(--blue-500, #3b82f6)" strokeWidth="1" opacity="0.45" />
      <polyline points={points(preview.summer, max)} fill="none" stroke="var(--amber-500)" strokeWidth="1" opacity="0.55" />
      <polyline points={points(preview.hours, max)} fill="none" stroke="var(--green-600)" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  )
}
