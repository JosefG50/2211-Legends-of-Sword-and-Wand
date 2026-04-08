import { useState } from 'react'
import * as api from '../api'

function LoginScreen({ onLoginSuccess }) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function handleStart() {
        if (!username || !password) {
            setError('Fill in all fields')
            return
        }

        setLoading(true)
        setError('')

        try {
            const userData = await api.login(username, password)
            onLoginSuccess(userData.user)
        } catch {
            setError('Login failed — check your username and password')
        }

        setLoading(false)
    }

    return (
        <div className="login-screen">
            <h1>⚔️ Legends of Sword and Wand</h1>

            <div className="login-form">
                <h2>Sign In</h2>

                <label>Username</label>
                <input
                    type="text"
                    value={username}
                    // onChange fires every time you type a character
                    // e.target.value is what's currently in the box
                    onChange={e => setUsername(e.target.value)}
                    placeholder="Enter username"
                />

                <label>Password</label>
                <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Enter password"
                />

                {error && <p className="error">{error}</p>}

                <button onClick={handleStart} disabled={loading}>
                    {loading ? 'Signing in...' : 'Continue'}
                </button>
            </div>
        </div>
    )
}

export default LoginScreen