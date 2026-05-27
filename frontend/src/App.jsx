import { useState } from 'react'
import ModeSelect from './components/ModeSelect'
import Workspace from './components/Workspace'

export default function App() {
  const [mode, setMode] = useState(() => localStorage.getItem('kw_mode') || null)

  const handleSelect = (m) => {
    localStorage.setItem('kw_mode', m)
    setMode(m)
  }

  const handleBack = () => {
    localStorage.removeItem('kw_mode')
    setMode(null)
  }

  if (!mode) return <ModeSelect onSelect={handleSelect} />
  return <Workspace mode={mode} onBack={handleBack} />
}
