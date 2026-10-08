import { Route, Routes } from 'react-router-dom'
import ErDiagramPage from './pages/ErDiagramPage'
import NotFoundPage from './pages/NotFoundPage'
import PdbPage from './pages/PdbPage'
import TableDetailPage from './pages/TableDetailPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ErDiagramPage />} />
      <Route path="/tables/:owner/:table" element={<TableDetailPage />} />
      <Route path="/pdb" element={<PdbPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
