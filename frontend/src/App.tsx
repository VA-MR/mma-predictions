import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { AdminAuthProvider } from './hooks/useAdminAuth'
import Layout from './components/Layout'
import { AdminLayout } from './components/AdminLayout'
import HomePage from './pages/HomePage'
import EventPage from './pages/EventPage'
import FightPage from './pages/FightPage'
import ProfilePage from './pages/ProfilePage'
import { AdminLoginPage } from './pages/AdminLoginPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { AdminOrganizationsPage } from './pages/AdminOrganizationsPage'
import { AdminEventsPage } from './pages/AdminEventsPage'
import { AdminFightsPage } from './pages/AdminFightsPage'
import { AdminFightersPage } from './pages/AdminFightersPage'

function App() {
  return (
    <AuthProvider>
      <AdminAuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="events/:slug" element={<EventPage />} />
            <Route path="fights/:id" element={<FightPage />} />
            <Route path="profile" element={<ProfilePage />} />
          </Route>
          
          {/* Admin login route (public) */}
          <Route path="/admin/login" element={<AdminLoginPage />} />
          
          {/* Protected admin routes */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="organizations" element={<AdminOrganizationsPage />} />
            <Route path="events" element={<AdminEventsPage />} />
            <Route path="fights" element={<AdminFightsPage />} />
            <Route path="fighters" element={<AdminFightersPage />} />
          </Route>
        </Routes>
      </AdminAuthProvider>
    </AuthProvider>
  )
}

export default App
