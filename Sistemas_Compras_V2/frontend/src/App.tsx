import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import ProtectedRoute from './routes/ProtectedRoute'
import PermissionRoute from './routes/PermissionRoute'
import MainLayout from './layouts/MainLayout'
import LoginPage from './features/auth/components/LoginPage'
import Dashboard from './pages/Dashboard'
import SolicitacoesListPage from './pages/solicitacoes/ListPage'
import NovaSolicitacaoPage from './pages/solicitacoes/NovaSolicitacaoPage'
import DetalheSolicitacaoPage from './pages/solicitacoes/DetalheSolicitacaoPage'
import RequisicoesPage from './pages/estoque/RequisicoesPage'
import ProcessarRequisicoesPage from './pages/suprimentos/ProcessarRequisicoesPage'
import CotacoesPage from './pages/suprimentos/CotacoesPage'
import PedidosPage from './pages/suprimentos/PedidosPage'
import AprovacoesPage from './pages/diretoria/AprovacoesPage'
import UsuariosPage from './pages/admin/UsuariosPage'
import ConfiguracoesPage from './pages/admin/ConfiguracoesPage'
import AuditoriaPage from './pages/admin/AuditoriaPage'
import DashboardSolicitante from './pages/solicitacoes/DashboardSolicitante'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route
          path="dashboard/solicitante"
          element={
            <PermissionRoute perm="can_create_solicitation">
              <DashboardSolicitante />
            </PermissionRoute>
          }
        />
        <Route path="solicitacoes" element={<SolicitacoesListPage />} />
        <Route
          path="solicitacoes/nova"
          element={
            <PermissionRoute perm="can_create_solicitation">
              <NovaSolicitacaoPage />
            </PermissionRoute>
          }
        />
        <Route
          path="solicitacoes/:id"
          element={
            <PermissionRoute perm="can_create_solicitation">
              <DetalheSolicitacaoPage />
            </PermissionRoute>
          }
        />
        <Route
          path="estoque/requisicoes"
          element={
            <PermissionRoute perm="can_manage_stock">
              <RequisicoesPage />
            </PermissionRoute>
          }
        />
        <Route
          path="suprimentos/processar"
          element={
            <PermissionRoute perm="can_manage_procurement">
              <ProcessarRequisicoesPage />
            </PermissionRoute>
          }
        />
        <Route
          path="suprimentos/cotacoes"
          element={
            <PermissionRoute perm="can_manage_procurement">
              <CotacoesPage />
            </PermissionRoute>
          }
        />
        <Route
          path="suprimentos/pedidos"
          element={
            <PermissionRoute perm="can_manage_procurement">
              <PedidosPage />
            </PermissionRoute>
          }
        />
        <Route
          path="diretoria/aprovacoes"
          element={
            <PermissionRoute perm="can_approve">
              <AprovacoesPage />
            </PermissionRoute>
          }
        />
        <Route
          path="admin/usuarios"
          element={
            <PermissionRoute perm="is_admin">
              <UsuariosPage />
            </PermissionRoute>
          }
        />
        <Route
          path="admin/configuracoes"
          element={
            <PermissionRoute perm="is_admin">
              <ConfiguracoesPage />
            </PermissionRoute>
          }
        />
        <Route
          path="admin/auditoria"
          element={
            <PermissionRoute perm="is_admin">
              <AuditoriaPage />
            </PermissionRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
