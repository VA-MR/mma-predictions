import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import EventPage from './pages/EventPage'
import FightPage from './pages/FightPage'
import ProfilePage from './pages/ProfilePage'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="events/:slug" element={<EventPage />} />
          <Route path="fights/:id" element={<FightPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App

