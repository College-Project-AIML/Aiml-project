import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { Auth0Provider } from '@auth0/auth0-react'
import { AuthProvider } from './context/AuthContext'
import App from './App'
import './App.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN || ''
const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID || ''

const appElement = (
  <React.StrictMode>
    <BrowserRouter>
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </GoogleOAuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)

ReactDOM.createRoot(document.getElementById('root')).render(
  AUTH0_DOMAIN && AUTH0_CLIENT_ID ? (
    <Auth0Provider
      domain={AUTH0_DOMAIN}
      clientId={AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
      }}
    >
      {appElement}
    </Auth0Provider>
  ) : (
    appElement
  )
)
