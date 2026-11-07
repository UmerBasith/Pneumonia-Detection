// Reads models/metrics.json (written by ml/evaluate.py) defensively: any missing field becomes null.

export interface TestMetrics {
  n: number | null
  accuracy: number | null
  sensitivity: number | null
  specificity: number | null
  precision: number | null
  f1: number | null
  auc: number | null
  prAuc: number | null
  balanced: number | null
  threshold: number | null
  cm: { tn: number; fp: number; fn: number; tp: number } | null
}

export interface MemberRow {
  name: string
  arch: string
  res: number | null
  accuracy: number | null
  auc: number | null
  sensitivity: number | null
  specificity: number | null
}

export interface NormalisedMetrics {
  version: string | null
  test: TestMetrics | null
  val: TestMetrics | null
  members: MemberRow[]
  memberNames: string[]
  tta: boolean | null
  temperature: number | null
  thresholdRule: string | null
  riskBands: Record<string, [number, number]> | null
  dataset: {
    name: string | null
    source: string | null
    license: string | null
    doi: string | null
    split: string | null
    counts: Record<string, unknown> | null
    patients: unknown
    leakage: unknown
  } | null
  gate: Record<string, unknown> | null
}

type Obj = Record<string, unknown>
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v)
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const str = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)

function readTest(t: unknown): TestMetrics | null {
  if (!isObj(t)) return null
  const cm = isObj(t.confusion_matrix) ? t.confusion_matrix : null
  return {
    n: num(t.n),
    accuracy: num(t.accuracy),
    sensitivity: num(t.recall_sensitivity) ?? num(t.sensitivity) ?? num(t.recall),
    specificity: num(t.specificity),
    precision: num(t.precision),
    f1: num(t.f1),
    auc: num(t.roc_auc) ?? num(t.auc),
    prAuc: num(t.pr_auc),
    balanced: num(t.balanced_accuracy),
    threshold: num(t.threshold),
    cm:
      cm && num(cm.tn) !== null && num(cm.fp) !== null && num(cm.fn) !== null && num(cm.tp) !== null
        ? { tn: cm.tn as number, fp: cm.fp as number, fn: cm.fn as number, tp: cm.tp as number }
        : null,
  }
}

export function normaliseMetrics(m: Obj | null): NormalisedMetrics | null {
  if (!m || Object.keys(m).length === 0) return null
  const final = isObj(m.final) ? m.final : m
  const per = isObj(m.per_model) ? m.per_model : {}
  const members: MemberRow[] = Object.entries(per).map(([name, v]) => {
    const o = isObj(v) ? v : {}
    const hp = isObj(o.hyperparameters) ? o.hyperparameters : {}
    const t = readTest(o.test)
    return {
      name,
      arch: str(hp.arch) ?? str(o.arch) ?? name.split('_')[0],
      res: num(hp.res) ?? num(hp.resolution) ?? num(o.res),
      accuracy: t?.accuracy ?? null,
      auc: t?.auc ?? null,
      sensitivity: t?.sensitivity ?? null,
      specificity: t?.specificity ?? null,
    }
  })
  const ds = isObj(m.dataset) ? m.dataset : null
  const bands = isObj(final.risk_bands) ? (final.risk_bands as Record<string, [number, number]>) : null
  return {
    version: str(m.model_version),
    test: readTest(final.test),
    val: readTest(final.val),
    members,
    memberNames: Array.isArray(final.members) ? (final.members as unknown[]).map(String) : members.map((x) => x.name),
    tta: typeof final.tta_hflip === 'boolean' ? final.tta_hflip : null,
    temperature: num(final.temperature),
    thresholdRule: str(final.threshold_rule),
    riskBands: bands,
    dataset: ds
      ? {
          name: str(ds.name),
          source: str(ds.source),
          license: str(ds.license),
          doi: str(ds.doi),
          split: str(ds.split_method),
          counts: isObj(ds.counts) ? ds.counts : null,
          patients: ds.patients ?? null,
          leakage: ds.leakage_checks ?? null,
        }
      : null,
    gate: isObj(m.xray_gate) ? m.xray_gate : null,
  }
}
