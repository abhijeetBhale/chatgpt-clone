import React from 'react'
import ReactDOM from 'react-dom/client'
// import App from './App.jsx'
import './index.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import Homepage from './routes/homepage/homepage'
import Dashboardpage from './routes/dashboardpage/dashboardpage'
import Chatpage from './routes/chatpage/chatpage'
import RootLayout from './layouts/rootLayout/rootLayout'
import DashboardLayout from './layouts/dashboardLayouts/dashboardLayout'
import SignInPage from './routes/signInPage/signInPage'
import SignUpPage from './routes/signUpPage/signUpPage'


const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: '/', element: <Homepage /> },
      { path: '/sign-in/*', element: <SignInPage /> },
      { path: '/sign-up/*', element: <SignUpPage /> },
      {
        element: <DashboardLayout />,
        children: [{
          path: '/dashboard',
          element: <Dashboardpage />,
        }, {
          path: '/dashboard/chats/:id',
          element: <Chatpage />,
        }]
      }
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
