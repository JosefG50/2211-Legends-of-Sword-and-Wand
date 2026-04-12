import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import LoginScreen from './screens/LoginScreen'
import CampaignHubScreen from './screens/CampaignHubScreen'
import CampaignScreen from './screens/CampaignScreen'
import BattleScreen from './screens/BattleScreen'
import InnScreen from './screens/InnScreen'
import ScoreScreen from './screens/ScoreScreen'

// user holds the logged-in user's info
// campaignId tracks the active campaign
// roomData holds whatever the last /next-room returned

function App() {
    const navigate = useNavigate()
    const [user, setUser] = useState(null)
    const [campaignId, setCampaignId] = useState(null)
    const [roomData, setRoomData] = useState(null)

    function handleLoginSuccess(userData) {
        setUser(userData)
        setCampaignId(null)
        navigate('/hub')
    }

    function handleCampaignSelected(selectedCampaignId) {
        setCampaignId(selectedCampaignId)
        navigate('/campaign')
    }

    function handleBattleRoom(room) {
        setRoomData(room)
        navigate('/battle')
    }

    function handleInnRoom(room) {
        setRoomData(room)
        navigate('/inn')
    }

    function handleCampaignComplete() {
        navigate('/score')
    }

    function handleReturnToCampaign() {
        navigate('/campaign')
    }

    function handleExitToHub() {
        navigate('/hub')
    }

    function requiresActiveRun() {
        return Boolean(user && campaignId)
    }

    return (
        <div className="app">
            <Routes>
                <Route
                    path="/"
                    element={<LoginScreen onLoginSuccess={handleLoginSuccess} />}
                />
                <Route
                    path="/hub"
                    element={
                        user ? (
                            <CampaignHubScreen
                                user={user}
                                onCampaignSelected={handleCampaignSelected}
                            />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    }
                />
                <Route
                    path="/campaign"
                    element={
                        requiresActiveRun() ? (
                            <CampaignScreen
                                campaignId={campaignId}
                                onBattleRoom={handleBattleRoom}
                                onInnRoom={handleInnRoom}
                                onComplete={handleCampaignComplete}
                                onSavedExit={handleExitToHub}
                            />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    }
                />
                <Route
                    path="/battle"
                    element={
                        requiresActiveRun() ? (
                            <BattleScreen
                                campaignId={campaignId}
                                roomData={roomData}
                                onFinished={handleReturnToCampaign}
                            />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    }
                />
                <Route
                    path="/inn"
                    element={
                        requiresActiveRun() ? (
                            <InnScreen
                                campaignId={campaignId}
                                onLeave={handleReturnToCampaign}
                            />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    }
                />
                <Route
                    path="/score"
                    element={
                        requiresActiveRun() ? (
                            <ScoreScreen campaignId={campaignId} user={user} />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </div>
    )
}

export default App