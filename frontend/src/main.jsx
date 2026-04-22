import React from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'

import './styles/tokens.css'
import './styles/components.css'
import './styles/kit.css'
import './styles/app.css'
import './styles/web.css'

import { router } from './app/router'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
