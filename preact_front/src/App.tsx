// src/App.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { Router, Route, useLocation } from 'preact-iso';
import { getAuthToken } from './lib/apiClient';
import { LoginForm } from './components/LoginForm';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Footer } from './components/Footer';
import { ItemListView } from './pages/ItemListView';
import { ItemDetailView } from './pages/ItemDetailView';
import { ItemCreateForm } from './pages/ItemCreateForm';
import { ItemUpdateForm } from './pages/ItemUpdateForm';
import { HandbookList } from './pages/HandbookList';
import { HandbookDetail } from './pages/HandbookDetail';
import { HandbookCreateForm } from './pages/HandbookCreateForm';
import { HandbookUpdateForm } from './pages/HandbookUpdateForm';
import { HandbookTypeList } from './pages/HandbookTypeList';
import { Home } from './pages/Home';
import { NotFound } from './pages/_404';
import './styles/tailwind-to-css.css';

// Wrapper component for ItemCreateForm to handle routing
function ItemCreateFormWrapper() {
  const { route } = useLocation();

  const handleClose = () => {
    route('/items');
  };

  const handleCreated = () => {
    // Optionally can add notification or other logic here
    // For now just navigate back to items list
    route('/items');
  };

  return <ItemCreateForm onClose={handleClose} onCreated={handleCreated} />;
}

// Wrapper component for ItemUpdateForm to handle routing
function ItemUpdateFormWrapper() {
  const { route } = useLocation();

  const handleClose = () => {
    route('/items');
  };

  const handleUpdated = () => {
    // Optionally can add notification or other logic here
    // For now just navigate back to items list
    route('/items');
  };

  return <ItemUpdateForm onClose={handleClose} onUpdated={handleUpdated} />;
}

function HomeRedirect() {
  const { route } = useLocation();

  // Redirect to /items immediately
  route('/items', true); // true for replace (equivalent to { replace: true })

  return null; // Return null while redirecting
}

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const location = useLocation(); // Get location outside of useEffect

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  // Ensure sidebar stays visible after route changes
  useEffect(() => {
    // When route changes, ensure sidebar remains visible
    // This prevents the sidebar from closing automatically during navigation
    if (!sidebarVisible) {
      setSidebarVisible(true);
    }
  }, [location.url]); // This will run when the route changes

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-base-100 flex items-center justify-center p-4">
        <div className="card bg-base-100 w-full max-w-md p-6 shadow-lg">
          <LoginForm onLogin={() => setIsAuthenticated(true)} />
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header
        sidebarVisible={sidebarVisible}
        setSidebarVisible={setSidebarVisible}
      />

      <div className="main-body">
        <div className={`navbar ${sidebarVisible ? '' : 'hidden'}`}>
          <Sidebar onClose={() => setSidebarVisible(false)} />
        </div>

        <div className="content-area">
          <div className="w-full">
            <Router>
              <Route path="/" component={isAuthenticated ? HomeRedirect : Home} />

              <Route path="/items/create" component={ItemCreateFormWrapper} />
              <Route path="/items/edit/:id" component={ItemUpdateFormWrapper} />
              <Route path="/items/:id" component={ItemDetailView} />
              <Route path="/items" component={ItemListView} />
              <Route path="/handbooks" component={HandbookList} />

              <Route path="/handbooks/:type/create" component={HandbookCreateForm} />
              <Route path="/handbooks/:type/edit/:id" component={HandbookUpdateForm} />
              <Route path="/handbooks/:type/:id" component={HandbookDetail} />
              <Route path="/handbooks/:type" component={HandbookTypeList} />

              <Route default component={NotFound} />
            </Router>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}