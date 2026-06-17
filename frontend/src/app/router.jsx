import { createBrowserRouter } from 'react-router-dom'
import { RootLayout } from './RootLayout'
import { AppLayout } from './AppLayout'
import { RequireAuth, RequirePlatformAdmin } from '@/services/auth'
import Landing from '@/features/marketing/Landing'
import { Login, Signup, ForgotPassword, ResetPassword, VerifyEmail } from '@/features/auth/Auth'
import Dashboard from '@/features/dashboard/Dashboard'
import ProjectList from '@/features/projects/ProjectList'
import Wizard from '@/features/design/Wizard'
import EquipmentLibrary from '@/features/equipment/EquipmentLibrary'
import MemoriaPreview from '@/features/memoria/MemoriaPreview'
import Team from '@/features/team/Team'
import AcceptInvitation from '@/features/team/AcceptInvitation'
import Flags from '@/features/admin/Flags'

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: '/', element: <Landing /> },
      { path: '/login', element: <Login /> },
      { path: '/signup', element: <Signup /> },
      { path: '/recuperar', element: <ForgotPassword /> },
      { path: '/reset-password', element: <ResetPassword /> },
      { path: '/verificar', element: <VerifyEmail /> },
      { path: '/invitacion', element: <AcceptInvitation /> },
      {
        path: '/app',
        element: <RequireAuth><AppLayout /></RequireAuth>,
        children: [
          { index: true, element: <Dashboard /> },
          { path: 'proyectos', element: <ProjectList /> },
          { path: 'diseno', element: <Wizard /> },
          { path: 'diseno/:id', element: <Wizard /> },
          { path: 'equipos', element: <EquipmentLibrary /> },
          { path: 'equipo', element: <Team /> },
          { path: 'memoria', element: <MemoriaPreview /> },
          { path: 'memoria/:id', element: <MemoriaPreview /> },
          { path: 'admin/flags', element: <RequirePlatformAdmin><Flags /></RequirePlatformAdmin> },
        ],
      },
    ],
  },
])
