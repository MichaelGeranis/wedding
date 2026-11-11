import { BrowserRouter as Router, Routes, Route } from 'react-router'
import { AuthProvider } from './context/AuthContext'
import { WeddingNav } from './components/wedding/WeddingNav'
import Invitation from './pages/Invitation'
import RSVPForm from './pages/RSVPForm'
import AdminPanel from './pages/AdminPanel'
import InvitedGuestsPage from './pages/InvitedGuestsPage'

function App() {
  return (
    <AuthProvider>
      <Router>
        <WeddingNav />
        <Routes>
          <Route path="/" element={<Invitation />} />
          <Route path="/rsvp" element={<RSVPForm />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/admin/invited" element={<InvitedGuestsPage />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
