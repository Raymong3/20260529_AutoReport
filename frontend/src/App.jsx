import { useState } from 'react'
import ModeSelect from './components/ModeSelect'
import Workspace from './components/Workspace'

export default function App() {
  const [mode, setMode] = useState(null)

  if (!mode) return <ModeSelect onSelect={setMode} />
  return <Workspace mode={mode} onBack={() => setMode(null)} />
}
