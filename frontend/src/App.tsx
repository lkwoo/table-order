import { Navigate, Route, Routes } from 'react-router-dom'
import CustomerApp from './customer/CustomerApp'
import AdminApp from './admin/AdminApp'

export default function App() {
  return (
    <Routes>
      <Route path="/customer/*" element={<CustomerApp />} />
      <Route path="/admin/*" element={<AdminApp />} />
      <Route path="*" element={<Navigate to="/customer" replace />} />
    </Routes>
  )
}
