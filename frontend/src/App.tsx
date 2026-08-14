import { useState, useEffect } from 'react';
import LandingPage from './pages/LandingPage/LandingPage';
import Dashboard from './pages/Dashboard/Dashboard';
import { Gauge, Radio, Flag, ChevronRight } from 'lucide-react';
import Button from './components/ui/Button';
import SignalIndicator from './components/ui/SignalIndicator';
import { healthCheck } from './services/api';
import './index.css';

function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'console'>('landing');
  const [healthStatus, setHealthStatus] = useState<'CHECKING' | 'CONNECTED' | 'OFFLINE'>('CHECKING');

  useEffect(() => {
    let active = true;
    async function checkHealth() {
      try {
        const res = await healthCheck();
        if (active) {
          if (res && (res.status === 'healthy' || res.status === 'ok')) {
            setHealthStatus('CONNECTED');
          } else {
            setHealthStatus('OFFLINE');
          }
        }
      } catch {
        if (active) setHealthStatus('OFFLINE');
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

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
            <SignalIndicator
              status={healthStatus === 'CONNECTED' ? 'active' : healthStatus === 'CHECKING' ? 'processing' : 'idle'}
              label={healthStatus === 'CONNECTED' ? 'ENGINE CONNECTED' : healthStatus === 'CHECKING' ? 'CHECKING ENGINE' : 'ENGINE OFFLINE'}
            />
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



