// Loads the dashboard dataset. On startup it fetches /sample-data.json; the
// Header's "Load run…" button hands a user-selected file to parseFile() so a
// real exported run can replace the sample without a restart.

export async function loadDefaultData() {
  const res = await fetch('./sample-data.json')
  if (!res.ok) throw new Error(`Could not load sample-data.json (${res.status})`)
  const data = await res.json()
  return validate(data)
}

export function parseFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        resolve(validate(JSON.parse(reader.result)))
      } catch (err) {
        reject(new Error('That file is not valid pipeline JSON: ' + err.message))
      }
    }
    reader.onerror = () => reject(new Error('Could not read that file.'))
    reader.readAsText(file)
  })
}

// Minimal shape check — enough to fail friendly, not a strict schema.
function validate(data) {
  if (!data || typeof data !== 'object') throw new Error('root is not an object')
  data.meta ||= {}
  data.llmops ||= { totals: {}, by_step: [] }
  data.llmops.totals ||= {}
  data.llmops.by_step ||= []
  data.kpis ||= []
  data.employees ||= []
  return data
}
