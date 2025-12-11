import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import Search from './pages/Search'
import Chat from './pages/Chat'
import Reports from './pages/Reports'
import Company from './pages/Company'

function App() {
    return (
        <div className="min-h-screen">
            <Header />
            <main className="pt-20">
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/search" element={<Search />} />
                    <Route path="/chat" element={<Chat />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/company/:id" element={<Company />} />
                </Routes>
            </main>
        </div>
    )
}

export default App
