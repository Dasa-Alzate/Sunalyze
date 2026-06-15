import { createBrowserRouter } from 'react-router-dom'
import { RootLayout } from './RootLayout'
import { AppLayout } from './AppLayout'
import { RequireAuth, RequirePlatformAdmin, RequireFlag } from '@/services/auth'
import Landing from '@/features/marketing/Landing'
import { Login, Signup, ForgotPassword, ResetPassword, VerifyEmail } from '@/features/auth/Auth'
import Dashboard from '@/features/dashboard/Dashboard'
import ProjectList from '@/features/projects/ProjectList'
import Wizard from '@/features/design/Wizard'
import CircuitDiagram from '@/features/design/CircuitDiagram'
import EquipmentLibrary from '@/features/equipment/EquipmentLibrary'
import MemoriaPreview from '@/features/memoria/MemoriaPreview'
import Team from '@/features/team/Team'
import AcceptInvitation from '@/features/team/AcceptInvitation'
import Flags from '@/features/admin/Flags'
import Marketplace from '@/features/marketplace/Marketplace'
import TemplatesGallery from '@/features/templates/TemplatesGallery'
import TemplateBuilder from '@/features/templates/TemplateBuilder'
import FinanceWorkspace from '@/features/finance/FinanceWorkspace'
import InstallationsWorkspace from '@/features/posventa/InstallationsWorkspace'
import BrandingSettings from '@/features/settings/BrandingSettings'
import ActivityFeed from '@/features/activity/ActivityFeed'
import Trash from '@/features/activity/Trash'
import { PrivacyPolicy, Terms, Cookies } from '@/features/legal/Legal'

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
      { path: '/legal/privacidad', element: <PrivacyPolicy /> },
      { path: '/legal/terminos', element: <Terms /> },
      { path: '/legal/cookies', element: <Cookies /> },
      {
        path: '/app',
        element: <RequireAuth><AppLayout /></RequireAuth>,
        children: [
          { index: true, element: <Dashboard /> },
          { path: 'proyectos', element: <ProjectList /> },
          { path: 'diseno', element: <Wizard /> },
          { path: 'diseno/:id', element: <Wizard /> },
          { path: 'diagrama', element: <CircuitDiagram /> },
          { path: 'diagrama/:id', element: <CircuitDiagram /> },
          { path: 'equipos', element: <EquipmentLibrary /> },
          { path: 'equipo', element: <Team /> },
          { path: 'memoria', element: <MemoriaPreview /> },
          { path: 'memoria/:id', element: <MemoriaPreview /> },
          { path: 'modulos', element: <Marketplace /> },
          { path: 'plantillas', element: <RequireFlag flag="templates"><TemplatesGallery /></RequireFlag> },
          { path: 'plantillas/:id', element: <RequireFlag flag="templates"><TemplateBuilder /></RequireFlag> },
          { path: 'finanzas', element: <RequireFlag flag="finance"><FinanceWorkspace /></RequireFlag> },
          { path: 'posventa', element: <RequireFlag flag="posventa"><InstallationsWorkspace /></RequireFlag> },
          { path: 'organizacion/marca', element: <BrandingSettings /> },
          { path: 'actividad', element: <ActivityFeed /> },
          { path: 'papelera', element: <Trash /> },
          { path: 'admin/flags', element: <RequirePlatformAdmin><Flags /></RequirePlatformAdmin> },
        ],
      },
    ],
  },
])
