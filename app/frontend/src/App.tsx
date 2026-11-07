import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router'
import { Nav } from './components/Nav'
import { GlobalBanners } from './components/Banners'
import { Footer } from './components/Footer'
import { Spinner } from './components/ui'
import { ScanPage } from './pages/ScanPage'
import { ThemeProvider } from './providers/ThemeProvider'
import { StatusProvider } from './providers/StatusProvider'
import { ToastProvider } from './providers/ToastProvider'

const TriagePage = lazy(() => import('./pages/TriagePage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const ScanDetailPage = lazy(() => import('./pages/ScanDetailPage'))
const Curb65Page = lazy(() => import('./pages/Curb65Page'))
const LearnPage = lazy(() => import('./pages/LearnPage'))
const ModelPage = lazy(() => import('./pages/ModelPage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

const TITLES: Record<string, string> = {
  '/': 'Scan',
  '/triage': 'Triage',
  '/history': 'History',
  '/curb-65': 'CURB-65 calculator',
  '/learn': 'Learn about pneumonia',
  '/model': 'Model',
  '/about': 'About',
}

function RouteEffects() {
  const { pathname } = useLocation()
  useEffect(() => {
    const t = TITLES[pathname] ?? (pathname.startsWith('/history/') ? 'Scan details' : 'PneumoScan AI')
    document.title = `${t} · PneumoScan AI`
    window.scrollTo({ top: 0 })
  }, [pathname])
  return null
}

function PageFallback() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center text-ink-3" role="status" aria-label="Loading page">
      <Spinner className="size-6" />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <StatusProvider>
          <BrowserRouter>
            <RouteEffects />
            <div className="flex min-h-dvh flex-col">
              <Nav />
              <GlobalBanners />
              <main id="main" className="mx-auto w-full max-w-[1240px] 2xl:max-w-[1400px] flex-1 px-4 sm:px-6">
                <Suspense fallback={<PageFallback />}>
                  <Routes>
                    <Route path="/" element={<ScanPage />} />
                    <Route path="/triage" element={<TriagePage />} />
                    <Route path="/history" element={<HistoryPage />} />
                    <Route path="/history/:id" element={<ScanDetailPage />} />
                    <Route path="/curb-65" element={<Curb65Page />} />
                    <Route path="/learn" element={<LearnPage />} />
                    <Route path="/model" element={<ModelPage />} />
                    <Route path="/about" element={<AboutPage />} />
                    <Route path="*" element={<NotFoundPage />} />
                  </Routes>
                </Suspense>
              </main>
              <Footer />
            </div>
          </BrowserRouter>
        </StatusProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}
