import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import { createHttpApi } from './api'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App api={createHttpApi()} />
  </StrictMode>,
)
