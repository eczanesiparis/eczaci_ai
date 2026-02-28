import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Auth } from './components/Auth';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [username, setUsername] = useState('');
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    // Check local storage or session storage on mount
    let storedAuth = localStorage.getItem('eczaci_auth');
    if (!storedAuth) storedAuth = sessionStorage.getItem('eczaci_auth');

    if (storedAuth) {
      try {
        const { loggedIn, admin, user } = JSON.parse(storedAuth);
        setIsLoggedIn(loggedIn);
        setIsAdmin(admin);
        setUsername(user || '');
      } catch (e) {
        console.error("Auth parse error:", e);
      }
    }
    setIsInitializing(false);
  }, []);

  const handleLoginSuccess = (adminStatus: boolean, user: string = "Kullanıcı") => {
    setIsAdmin(adminStatus);
    setUsername(user);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('eczaci_auth');
    sessionStorage.removeItem('eczaci_auth');
    setIsLoggedIn(false);
    setIsAdmin(false);
    setUsername('');
  };

  if (isInitializing) {
    return <div className="w-full min-h-screen bg-slate-900 flex items-center justify-center p-4"></div>;
  }

  if (!isLoggedIn) {
    return <Auth onLoginSuccess={(admin, user) => handleLoginSuccess(admin, user)} />;
  }

  return (
    <div className="w-full min-h-screen bg-slate-900">
      <ChatInterface isAdmin={isAdmin} username={username} onLogout={handleLogout} />
    </div>
  );
}

export default App;
