import { Route, Routes } from 'react-router-dom'
import ErDiagramPage from './pages/ErDiagramPage'
import NotFoundPage from './pages/NotFoundPage'
import TableDetailPage from './pages/TableDetailPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ErDiagramPage />} />
      <Route path="/tables/:owner/:table" element={<TableDetailPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
