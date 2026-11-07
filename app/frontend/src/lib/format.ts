export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '–'
  return `${(v * 100).toFixed(digits)}%`
}

export function dateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function shortDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function relativeTime(iso: string): string {
  const d = new Date(iso).getTime()
  if (Number.isNaN(d)) return ''
  const s = Math.round((Date.now() - d) / 1000)
  if (s < 45) return 'just now'
  const m = Math.round(s / 60)
  if (m < 60) return `${m} min ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h} h ago`
  const days = Math.round(h / 24)
  if (days < 7) return `${days} d ago`
  return shortDate(iso)
}

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export const ACCEPT = '.jpg,.jpeg,.jfif,.png,.bmp,.webp,.tif,.tiff,.dcm,.dicom,image/jpeg,image/png,image/bmp,image/webp,image/tiff,application/dicom'
export const MAX_BYTES = 25 * 1024 * 1024
const EXT_OK = /\.(jpe?g|jfif|png|bmp|webp|tiff?|dcm|dicom)$/i

/** Quick client-side check so obvious mistakes get an instant, friendly message. */
export function precheckFile(f: File): string | null {
  if (f.size === 0) return `${f.name || 'This file'} is empty.`
  if (f.size > MAX_BYTES) return `${f.name} is larger than 25 MB. Use a smaller or compressed image.`
  const typeOk = /^image\/(jpeg|png|bmp|webp|tiff)$/.test(f.type) || f.type === 'application/dicom'
  if (!EXT_OK.test(f.name) && !typeOk) {
    return `${f.name || 'This file'} is not a supported type. Use JPG, PNG, BMP, WEBP, TIFF or DICOM (.dcm).`
  }
  return null
}

export function canPreviewInBrowser(f: File): boolean {
  return /\.(jpe?g|jfif|png|bmp|webp)$/i.test(f.name) || /^image\/(jpeg|png|bmp|webp)$/.test(f.type)
}
