import { useState } from 'react';
import LandingPage from './pages/LandingPage/LandingPage';
import Dashboard from './pages/Dashboard/Dashboard';
import { Gauge, Radio, Flag, ChevronRight, ShieldCheck } from 'lucide-react';
import Button from './components/ui/Button';
import './index.css';

function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'console'>('landing');

  return (
    <div className="sc-app-wrapper">
      {/* Top Product Command & Navigation Bar */}
      <nav className="sc-app-nav">
        <div className="sc-app-nav__left">
          <div className="sc-app-nav__logo" onClick={() => setCurrentView('landing')} style={{ cursor: 'pointer' }}>
            <div className="sc-app-nav__logo-icon">
              <Radio size={16} />
            </div>
            <div>
              <span className="sc-app-nav__brand font-telemetry">SILENT CO-DRIVER</span>
            </div>
          </div>

          <div className="sc-app-nav__nav-items">
            <button
              className={`sc-app-nav__item ${currentView === 'landing' ? 'sc-app-nav__item--active' : ''}`}
              onClick={() => setCurrentView('landing')}
            >
              Product
            </button>
            <a
              href="#ai-engineer"
              className="sc-app-nav__item"
              onClick={() => { if (currentView !== 'landing') setCurrentView('landing'); }}
            >
              Intelligence
            </a>
            <a
              href="#telemetry-chart"
              className="sc-app-nav__item"
              onClick={() => { if (currentView !== 'landing') setCurrentView('landing'); }}
            >
              Telemetry
            </a>
            <button
              className={`sc-app-nav__item ${currentView === 'console' ? 'sc-app-nav__item--active' : ''}`}
              onClick={() => setCurrentView('console')}
            >
              Command Console
            </button>
          </div>
        </div>

        <div className="sc-app-nav__right">
          <div className="sc-app-nav__status font-telemetry text-micro text-lime">
            <Flag size={12} />
            <span>BAHRAIN GP · PRACTICE 2</span>
          </div>

          <div className="sc-app-nav__status">
            <ShieldCheck size={13} className="text-lime" />
            <span className="text-micro font-telemetry" style={{ color: 'var(--color-text-secondary)' }}>
              LIVE RACE ENGINE v2.5
            </span>
          </div>

          <Button
            variant={currentView === 'console' ? 'secondary' : 'primary'}
            size="sm"
            onClick={() => setCurrentView(currentView === 'landing' ? 'console' : 'landing')}
          >
            {currentView === 'landing' ? (
              <>
                Enter Console <Gauge size={13} />
              </>
            ) : (
              <>
                Return to Story <ChevronRight size={13} />
              </>
            )}
          </Button>
        </div>
      </nav>

      {/* Main Experience View */}
      <main>
        {currentView === 'landing' ? (
          <LandingPage onEnterConsole={() => setCurrentView('console')} />
        ) : (
          <Dashboard />
        )}
      </main>
    </div>
  );
}

export default App;



