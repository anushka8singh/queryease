import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion as Motion } from 'framer-motion'
import {
  Activity,
  AlertCircle,
  ActivitySquare,
  Bot,
  CheckCircle2,
  Clock3,
  Copy,
  Database,
  LoaderCircle,
  Play,
  Radar,
  ShieldCheck,
  Sparkles,
  Table2,
} from 'lucide-react'
import { sendQuery } from './api'
import LogsPanel from './LogsPanel'

const cardClasses =
  'rounded-2xl border border-blue-100 bg-white shadow-lg shadow-blue-100/40 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl'

const motionProps = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
}

function stringifyCellValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function App() {
  const [query, setQuery] = useState('')
  const [sql, setSql] = useState('')
  const [result, setResult] = useState([])
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [showLogs, setShowLogs] = useState(false)

  const columns = useMemo(() => {
    const keySet = new Set()

    result.forEach((row) => {
      if (row && typeof row === 'object' && !Array.isArray(row)) {
        Object.keys(row).forEach((key) => keySet.add(key))
      }
    })

    return Array.from(keySet)
  }, [result])

  useEffect(() => {
    if (!error) return undefined

    const timeout = window.setTimeout(() => setError(''), 5000)
    return () => window.clearTimeout(timeout)
  }, [error])

  async function handleSubmit() {
    const trimmedQuery = query.trim()
    if (!trimmedQuery || loading) return

    setLoading(true)
    setError('')
    setSql('')
    setResult([])
    setLogs([])

    try {
      const data = await sendQuery(trimmedQuery)

      if (!data || typeof data !== 'object') {
        throw new Error('Empty response received from backend.')
      }

      setSql(data.sql || '')
      setResult(Array.isArray(data.result) ? data.result : [])
      setLogs(Array.isArray(data.logs) ? data.logs : [])

      if (data.sql === undefined && data.result === undefined && data.logs === undefined) {
        setError('Empty response received from backend.')
      }
    } catch (submitError) {
      setSql('')
      setResult([])
      setLogs([])
      setError(submitError.message || 'Failed to generate SQL.')
    } finally {
      setLoading(false)
    }
  }

  async function handleCopy() {
    if (!sql) return

    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
      setError('Clipboard access failed. Please copy the SQL manually.')
    }
  }

  const rowCount = result.length
  const logCount = logs.length

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 via-white to-cyan-50 text-slate-900">
      <AnimatePresence>
        {error ? (
          <Motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            className="fixed left-1/2 top-4 z-50 w-[min(92vw,640px)] -translate-x-1/2"
          >
            <div className="rounded-2xl border border-rose-200 bg-white/95 px-4 py-3 shadow-2xl shadow-rose-100 backdrop-blur">
              <div className="flex items-start gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 text-rose-500" />
                <div className="flex-1">
                  <p className="font-semibold text-rose-700">Query request failed</p>
                  <p className="text-sm text-slate-600">{error}</p>
                </div>
              </div>
            </div>
          </Motion.div>
        ) : null}
      </AnimatePresence>

      <div className="mx-auto min-h-screen w-full max-w-[1400px] px-6 py-6">
        <div className="grid min-h-[calc(100vh-3rem)] grid-cols-1 gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <Motion.aside
            {...motionProps}
            className="overflow-hidden rounded-[28px] border border-white/70 bg-slate-950 text-white shadow-2xl shadow-blue-200/60"
          >
            <div className="flex h-full flex-col bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.32),_transparent_42%),linear-gradient(180deg,_#0f172a_0%,_#111827_100%)] p-6">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.25em] text-blue-100">
                  <Sparkles className="h-3.5 w-3.5" />
                  QueryEase
                </div>
                <h1 className="mt-5 bg-gradient-to-r from-blue-300 via-cyan-200 to-indigo-300 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
                  QueryEase
                </h1>
                <p className="mt-2 text-sm text-slate-300">AI-Powered SQL Assistant</p>
                <p className="mt-5 text-sm leading-6 text-slate-400">
                  Translate business questions into executable SQL, inspect the generated query,
                  and review logs from the full AI workflow in one workspace.
                </p>
              </div>

              <div className="mt-8 grid gap-4">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-blue-500/15 p-2 text-blue-200">
                      <Radar className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-slate-400">
                        Rows Returned
                      </p>
                      <p className="mt-1 text-2xl font-semibold text-white">{rowCount}</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-cyan-500/15 p-2 text-cyan-200">
                      <Bot className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-slate-400">
                        Pipeline Steps
                      </p>
                      <p className="mt-1 text-2xl font-semibold text-white">{logCount}</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-emerald-500/15 p-2 text-emerald-200">
                      <ShieldCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-slate-400">
                        Session State
                      </p>
                      <p className="mt-1 text-sm font-semibold text-white">
                        {loading ? 'Generating SQL...' : sql ? 'Ready for analysis' : 'Awaiting query'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 rounded-2xl border border-blue-400/20 bg-blue-500/10 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-blue-100">
                  <CheckCircle2 className="h-4 w-4" />
                  How it works  
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Type your query and QueryEase takes care of the rest — fetching, processing, and presenting the data for you in seconds.
                </p>
              </div>
            </div>
          </Motion.aside>

          <main className="grid min-h-0 grid-cols-12 gap-6">
            <div className="col-span-12 grid min-h-0 gap-6 xl:col-span-7">
              <Motion.section {...motionProps} className={`${cardClasses} p-6`}>
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                        <Activity className="h-4 w-4" />
                        Natural Language Query
                      </div>
                      <h2 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
                        Ask for the exact insight you need
                      </h2>
                      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                        Describe your question in plain English and QueryEase will return
                        real SQL, result rows, and execution logs.
                      </p>
                    </div>

                    <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-white px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.22em] text-slate-500">
                        Request Target
                      </p>
            
                    </div>
                  </div>

                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-slate-700">
                      Business question
                    </span>
                    <textarea
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      rows={8}
                      placeholder="Example: Show monthly active users by plan tier for the last 90 days and rank the fastest-growing segment."
                      className="w-full rounded-2xl border border-blue-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-900 outline-none transition-all duration-300 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
                    />
                  </label>

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1">
                        <Database className="h-4 w-4 text-blue-600" />
                        Dynamic SQL generation
                      </span>
                      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1">
                        <Clock3 className="h-4 w-4 text-blue-600" />
                        Live pipeline logs
                      </span>
                    </div>

                    <Motion.button
                      whileHover={{ scale: loading ? 1 : 1.03 }}
                      whileTap={{ scale: loading ? 1 : 0.98 }}
                      type="button"
                      onClick={handleSubmit}
                      disabled={loading || query.trim().length < 3}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-blue-500 to-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition-all duration-300 hover:from-blue-600 hover:to-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {loading ? (
                        <>
                          <LoaderCircle className="h-4 w-4 animate-spin" />
                          Generating SQL...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          Generate SQL
                        </>
                      )}
                    </Motion.button>
                  </div>
                </div>
              </Motion.section>

              <Motion.section
                {...motionProps}
                transition={{ duration: 0.45, delay: 0.05 }}
                className={`${cardClasses} flex min-h-0 flex-col p-6`}
              >
                <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                      <Database className="h-4 w-4" />
                      SQL Output
                    </div>
                    <h2 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
                      Generated query
                    </h2>
                    <p className="mt-2 text-sm text-slate-500">
                      Structured SQL returned directly for the current request.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleCopy}
                    disabled={!sql}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-blue-200 bg-white px-4 py-2.5 text-sm font-medium text-blue-700 transition-all duration-300 hover:bg-blue-50 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Copy className="h-4 w-4" />
                    {copied ? 'Copied' : 'Copy SQL'}
                  </button>
                </div>

                <div className="min-h-[320px] overflow-hidden rounded-2xl border border-slate-200 bg-slate-950">
                  <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 text-xs uppercase tracking-[0.24em] text-slate-400">
                    <span>Live SQL Response</span>
                    <span>{sql ? 'Ready' : 'Waiting for request'}</span>
                  </div>
                  <div className="h-full overflow-auto p-4">
                    {sql ? (
                      <pre className="font-mono text-sm leading-7 text-sky-100">
                        <code>{sql}</code>
                      </pre>
                    ) : (
                      <div className="flex h-full min-h-[250px] items-center justify-center text-center text-sm text-slate-400">
                         Submit your query to generate and view results instantly.
                      </div>
                    )}
                  </div>
                </div>
              </Motion.section>
            </div>

            <div className="col-span-12 grid min-h-0 gap-6 xl:col-span-5">
              <Motion.section
                {...motionProps}
                transition={{ duration: 0.45, delay: 0.1 }}
                className={`${cardClasses} flex min-h-0 flex-col p-6`}
              >
                <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                      <Table2 className="h-4 w-4" />
                      Result Table
                    </div>
                    <h2 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
                      Query results
                    </h2>
                    <p className="mt-2 text-sm text-slate-500">
                       Results are organized automatically into rows and columns.
                    </p>
                  </div>

                  <div className="rounded-2xl bg-gradient-to-r from-blue-50 to-cyan-50 px-4 py-3 text-right">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Rows</p>
                    <p className="mt-1 text-lg font-semibold text-slate-900">{rowCount}</p>
                  </div>
                </div>

                <div className="min-h-[340px] overflow-hidden rounded-2xl border border-slate-200">
                  {columns.length > 0 ? (
                    <div className="h-full overflow-auto">
                      <table className="min-w-full border-collapse text-left text-sm">
                        <thead className="sticky top-0 z-10 bg-slate-100/95 text-slate-600 backdrop-blur">
                          <tr>
                            {columns.map((column) => (
                              <th key={column} className="px-4 py-3 font-semibold capitalize">
                                {column.replace(/_/g, ' ')}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white">
                          {result.map((row, rowIndex) => (
                            <tr
                              key={`row-${rowIndex}`}
                              className={`transition-colors duration-300 hover:bg-blue-50 ${
                                rowIndex % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'
                              }`}
                            >
                              {columns.map((column) => (
                                <td key={`${rowIndex}-${column}`} className="px-4 py-3 text-slate-700">
                                  {stringifyCellValue(row?.[column])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="flex h-full min-h-[340px] items-center justify-center px-6 text-center text-sm text-slate-400">
                      Results will show up here once your query is processed.
                    </div>
                  )}
                </div>
              </Motion.section>

              <Motion.section
                {...motionProps}
                transition={{ duration: 0.45, delay: 0.15 }}
                className={`${cardClasses} p-6`}
              >
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                      <Clock3 className="h-4 w-4" />
                      Logs Panel
                    </div>
                    <h2 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
                      Debug visibility
                    </h2>
                    <p className="mt-2 text-sm text-slate-400">
                      View step-by-step processing details when needed.
                    </p>
                  </div>

                  <div className="flex items-center gap-3 self-start sm:self-center">
                    {logCount > 0 ? (
                      <div className="inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50/80 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.2em] text-emerald-700 backdrop-blur">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        Live
                      </div>
                    ) : null}

                    <button
                      type="button"
                      onClick={() => setShowLogs((current) => !current)}
                      className={`inline-flex cursor-pointer items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all duration-300 ease-in-out hover:scale-[1.02] ${
                        showLogs
                          ? 'border-blue-200 bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-200/70'
                          : 'border-white/70 bg-white/70 text-slate-700 shadow-md shadow-blue-100/40 backdrop-blur hover:border-blue-100 hover:bg-blue-50/80 hover:shadow-lg hover:shadow-blue-100/60'
                      }`}
                    >
                      <ActivitySquare className={`h-4 w-4 ${showLogs ? 'text-white' : 'text-blue-600'}`} />
                      <span>Debug Logs</span>
                    </button>
                  </div>
                </div>

                <AnimatePresence initial={false}>
                  {showLogs ? (
                    <Motion.div
                      key="debug-logs"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: 'easeInOut' }}
                      className="overflow-hidden"
                    >
                      <div className="mt-5">
                        <LogsPanel logs={logs} />
                      </div>
                    </Motion.div>
                  ) : null}
                </AnimatePresence>
              </Motion.section>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default App
