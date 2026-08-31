import { Navigate, Route, Routes } from 'react-router-dom'
import { CustomerAuthProvider, useCustomerAuth } from './CustomerAuthContext'
import { CartProvider } from './CartContext'
import { Spinner } from '../shared/ui'
import TableLoginView from './TableLoginView'
import MenuListView from './MenuListView'
import OrderConfirmView from './OrderConfirmView'
import OrderSubmitView from './OrderSubmitView'
import OrderHistoryView from './OrderHistoryView'
import './customer.css'

function CustomerRoutes() {
  const { auth, ready } = useCustomerAuth()

  if (!ready) {
    return (
      <div className="center-screen">
        <Spinner />
      </div>
    )
  }

  if (!auth) {
    return <TableLoginView />
  }

  return (
    <Routes>
      <Route index element={<MenuListView />} />
      <Route path="confirm" element={<OrderConfirmView />} />
      <Route path="submit" element={<OrderSubmitView />} />
      <Route path="history" element={<OrderHistoryView />} />
      <Route path="*" element={<Navigate to="/customer" replace />} />
    </Routes>
  )
}

export default function CustomerApp() {
  return (
    <CustomerAuthProvider>
      <CartProvider>
        <CustomerRoutes />
      </CartProvider>
    </CustomerAuthProvider>
  )
}
