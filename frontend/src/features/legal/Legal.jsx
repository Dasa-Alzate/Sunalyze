import { useEffect } from 'react'
import { Icon } from '@/shared/ui'
import { useTransition } from '@/services/transition'

const UPDATED = '22 de junio de 2026'

function LegalShell({ title, intro, children }) {
  const { navigate } = useTransition()
  useEffect(() => { document.title = `${title} · Sunalyze` }, [title])
  return (
    <div className="web web-legal">
      <a className="sun-skip-link" href="#main">Saltar al contenido</a>
      <nav className="web-nav scrolled">
        <a className="web-brand" href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>
          <span className="mark"><Icon name="sun" size={18} strokeWidth={2.4} /></span>Sunalyze
        </a>
        <div className="web-nav__spacer" />
        <div className="web-nav__links">
          <a href="/legal/privacidad" onClick={(e) => { e.preventDefault(); navigate('/legal/privacidad') }}>Privacidad</a>
          <a href="/legal/terminos" onClick={(e) => { e.preventDefault(); navigate('/legal/terminos') }}>Términos</a>
          <a href="/legal/cookies" onClick={(e) => { e.preventDefault(); navigate('/legal/cookies') }}>Cookies</a>
        </div>
      </nav>
      <main id="main" tabIndex={-1} className="web-section">
        <div className="web-wrap web-legal__doc">
          <span className="web-eyebrow">Legal</span>
          <h1 className="web-h2">{title}</h1>
          <p className="web-legal__meta">Última actualización: {UPDATED}</p>
          {intro && <p className="web-lead">{intro}</p>}
          {children}
        </div>
      </main>
      <footer className="web-footer">
        <div className="web-footer__bar">
          <span>© 2026 Sunalyze. Todos los derechos reservados.</span>
          <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>Volver al inicio</a>
        </div>
      </footer>
    </div>
  )
}

function Section({ heading, children }) {
  return (
    <section className="web-legal__section">
      <h2>{heading}</h2>
      {children}
    </section>
  )
}

export function PrivacyPolicy() {
  return (
    <LegalShell
      title="Política de privacidad"
      intro="En Sunalyze tratamos los datos de las cuentas profesionales y de los proyectos fotovoltaicos conforme al Reglamento (UE) 2016/679 (RGPD) y a la normativa española de protección de datos."
    >
      <Section heading="Responsable del tratamiento">
        <p>Sunalyze actúa como responsable del tratamiento de los datos de las cuentas de usuario y como encargado del tratamiento respecto de los datos de clientes finales que cada organización introduce en sus proyectos. Puedes contactar en <a href="mailto:privacidad@sunalyze.es">privacidad@sunalyze.es</a>.</p>
      </Section>
      <Section heading="Datos que tratamos">
        <ul>
          <li>Datos de cuenta: nombre, apellidos, correo electrónico y organización.</li>
          <li>Datos de proyecto: ubicación, consumo, equipos y parámetros técnicos de cada instalación.</li>
          <li>Datos de seguridad: factores de doble autenticación (MFA/2FA) en accesos privilegiados.</li>
          <li>Bitácora de auditoría: registro de accesos y acciones relevantes sobre los datos.</li>
        </ul>
      </Section>
      <Section heading="Finalidad y base jurídica">
        <p>Tratamos estos datos para prestar el servicio de diseño y legalización de instalaciones, para garantizar la seguridad de las cuentas y para cumplir obligaciones legales. La base jurídica es la ejecución del contrato y el interés legítimo en la seguridad del servicio.</p>
      </Section>
      <Section heading="Tus derechos">
        <p>Puedes ejercer en cualquier momento tus derechos de acceso, rectificación, portabilidad y supresión:</p>
        <ul>
          <li><strong>Acceso y portabilidad:</strong> exporta una copia completa de tus datos en formato estructurado desde tu cuenta.</li>
          <li><strong>Supresión (derecho al olvido):</strong> solicita el borrado de tu cuenta y de los datos asociados; tramitamos la baja de forma irreversible.</li>
          <li><strong>Rectificación y oposición:</strong> corrige o limita el tratamiento escribiendo a <a href="mailto:privacidad@sunalyze.es">privacidad@sunalyze.es</a>.</li>
        </ul>
        <p>Tienes derecho a reclamar ante la Agencia Española de Protección de Datos si consideras que el tratamiento no se ajusta a la normativa.</p>
      </Section>
      <Section heading="Conservación y seguridad">
        <p>Conservamos los datos mientras la cuenta esté activa y durante los plazos legales aplicables. Aplicamos cifrado, control de accesos por organización (multi-tenant), doble autenticación en accesos privilegiados y una bitácora de auditoría para detectar usos indebidos.</p>
      </Section>
    </LegalShell>
  )
}

export function Terms() {
  return (
    <LegalShell
      title="Términos y condiciones"
      intro="Estas condiciones regulan el acceso y uso de Sunalyze, la plataforma de diseño y legalización de instalaciones fotovoltaicas."
    >
      <Section heading="Objeto del servicio">
        <p>Sunalyze ofrece herramientas de dimensionado, validación normativa, análisis financiero y generación de documentación técnica. Los cálculos y documentos generados son una ayuda profesional; la validación y firma final corresponden al técnico competente.</p>
      </Section>
      <Section heading="Cuentas y organizaciones">
        <p>El acceso requiere una cuenta. Cada organización es responsable de sus usuarios, de la veracidad de los datos introducidos y de la confidencialidad de sus credenciales. Las capacidades disponibles pueden variar según el plan y los módulos activados para cada organización.</p>
      </Section>
      <Section heading="Uso aceptable">
        <ul>
          <li>No utilizar la plataforma para fines ilícitos ni para vulnerar derechos de terceros.</li>
          <li>No intentar acceder a datos de otras organizaciones ni eludir los controles de seguridad.</li>
          <li>Respetar las licencias del equipamiento y de los contenidos de terceros.</li>
        </ul>
      </Section>
      <Section heading="Responsabilidad">
        <p>El servicio se presta "tal cual". Sunalyze no se responsabiliza de las decisiones técnicas o económicas adoptadas a partir de los resultados, que deben ser revisados por un profesional. La responsabilidad se limita en la medida que permita la ley aplicable.</p>
      </Section>
      <Section heading="Cambios y ley aplicable">
        <p>Podemos actualizar estas condiciones; los cambios relevantes se notificarán en la plataforma. Estas condiciones se rigen por la legislación española. Para cualquier consulta escribe a <a href="mailto:legal@sunalyze.es">legal@sunalyze.es</a>.</p>
      </Section>
    </LegalShell>
  )
}

export function Cookies() {
  return (
    <LegalShell
      title="Política de cookies"
      intro="Sunalyze utiliza un número mínimo de cookies, centradas en el funcionamiento del servicio."
    >
      <Section heading="Qué cookies usamos">
        <ul>
          <li><strong>Técnicas y de sesión:</strong> imprescindibles para mantener la sesión iniciada y la seguridad de la cuenta.</li>
          <li><strong>De preferencias:</strong> recuerdan ajustes como el idioma o la opción de mantener la sesión.</li>
        </ul>
        <p>No utilizamos cookies publicitarias ni de seguimiento de terceros con fines de marketing.</p>
      </Section>
      <Section heading="Gestión de cookies">
        <p>Puedes bloquear o eliminar las cookies desde la configuración de tu navegador. Si desactivas las cookies técnicas, es posible que algunas funciones, como el inicio de sesión, dejen de funcionar correctamente.</p>
      </Section>
      <Section heading="Más información">
        <p>Para cualquier duda sobre el uso de cookies o el tratamiento de datos consulta nuestra <a href="/legal/privacidad">Política de privacidad</a> o escribe a <a href="mailto:privacidad@sunalyze.es">privacidad@sunalyze.es</a>.</p>
      </Section>
    </LegalShell>
  )
}
