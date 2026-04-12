import { AnimatePresence, motion as Motion } from 'framer-motion'
import { Clock3 } from 'lucide-react'

const STEP_LABELS = {
  workflow_start: 'Started',
  input_node: 'Reading input',
  schema_loaded: 'Schema ready',
  sql_generator: 'Generating SQL',
  sql_generator_node: 'Generating SQL',
  sql_generated: 'SQL ready',
  validator_node: 'Validating',
  validation_passed: 'Validated',
  executor_node: 'Running query',
  query_executed: 'Results ready',
  workflow_complete: 'Completed',
}

const STEP_MESSAGES = {
  workflow_start: 'Preparing the request flow.',
  input_node: 'Checking your question and context.',
  schema_loaded: 'Database structure is available.',
  sql_generator: 'Creating a query from your input.',
  sql_generator_node: 'Creating a query from your input.',
  sql_generated: 'The SQL draft is ready.',
  validator_node: 'Reviewing the query for safety.',
  validation_passed: 'The query passed validation.',
  executor_node: 'Running the query now.',
  query_executed: 'Results were returned successfully.',
  workflow_complete: 'Everything finished successfully.',
}

function formatTimestamp(value, fallback) {
  if (!value || typeof value !== 'string') {
    return fallback
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return fallback
  }

  return date.toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
  })
}

function buildLogEntry(entry, index) {
  if (typeof entry === 'string') {
    return {
      id: `log-${index}`,
      label: 'Update',
      message: entry,
      time: `Step ${index + 1}`,
    }
  }

  if (!entry || typeof entry !== 'object') {
    return {
      id: `log-${index}`,
      label: 'Update',
      message: 'Status updated.',
      time: `Step ${index + 1}`,
    }
  }

  const stepKey = entry.step || entry.id || ''
  const fallbackMessage =
    typeof entry.message === 'string' && entry.message.trim() ? entry.message.trim() : 'Status updated.'

  return {
    id: entry.id || `${stepKey || 'log'}-${index}`,
    label: STEP_LABELS[stepKey] || 'Update',
    message: STEP_MESSAGES[stepKey] || fallbackMessage,
    time: formatTimestamp(entry.timestamp || entry.time, `Step ${index + 1}`),
  }
}

function LogsPanel({ logs }) {
  const items = logs.map(buildLogEntry)

  return (
    <AnimatePresence initial={false}>
      <Motion.section
        key="logs-panel"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        <div className="rounded-2xl border border-white/70 bg-gradient-to-br from-white/80 via-blue-50/55 to-cyan-50/50 p-5 shadow-lg shadow-blue-100/25 backdrop-blur">
          <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-sm font-medium text-slate-700 shadow-sm shadow-blue-100/40">
                <Clock3 className="h-4 w-4" />
                Debug Logs
              </div>
              <h2 className="mt-4 text-xl font-semibold tracking-tight text-slate-900">
                Query progress
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                A concise view of what happened during the latest request.
              </p>
            </div>

            <div className="rounded-full border border-white/80 bg-white/75 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-slate-500 shadow-sm shadow-blue-100/40">
              {items.length} steps
            </div>
          </div>

          <div className="max-h-[340px] space-y-3 overflow-auto pr-1">
            {items.length > 0 ? (
              items.map((item, index) => (
                <Motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.03 }}
                  className="rounded-xl border border-white/80 bg-white/70 p-3 text-sm shadow-md shadow-blue-100/30 backdrop-blur transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:bg-white/85 hover:shadow-lg hover:shadow-blue-100/40"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800">{item.label}</p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">{item.message}</p>
                    </div>
                    <span className="shrink-0 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                      {item.time}
                    </span>
                  </div>
                </Motion.div>
              ))
            ) : (
              <div className="flex min-h-[180px] items-center justify-center rounded-xl border border-dashed border-slate-200/80 bg-white/50 px-6 text-center text-sm text-slate-400 backdrop-blur">
                Debug logs will appear here after you run a query.
              </div>
            )}
          </div>
        </div>
      </Motion.section>
    </AnimatePresence>
  )
}

export default LogsPanel
