import { Link, Outlet } from 'react-router-dom';
import './rootLayout.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ClerkProvider, SignedIn, SignedOut, UserButton, SignInButton } from '@clerk/clerk-react';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!PUBLISHABLE_KEY) {
  throw new Error('Missing Publishable Key');
}

const queryClient = new QueryClient();

const RootLayout = () => {
  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
      <QueryClientProvider client={queryClient}>
        <div className="rootLayout">
          <header className="rootHeader">
            <div className="logoCluster">
              <Link to="/" className="logo">
                <div className="logoBadge">
                  <img src="/logo.png" alt="Boost AI Logo" />
                </div>
                <span className="brandName">Boost AI</span>
                <span className="sparkle">✦</span>
              </Link>
              <span className="versionBadge">xAI ENGINE</span>
            </div>

            <div className="userCluster">
              <SignedIn>
                <UserButton 
                  appearance={{
                    elements: {
                      userButtonAvatarBox: {
                        width: '34px',
                        height: '34px',
                        borderRadius: '50%',
                        border: '1px solid var(--color-hairline-translucent)'
                      }
                    }
                  }} 
                />
              </SignedIn>
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="signInPill">Sign In</button>
                </SignInButton>
              </SignedOut>
            </div>
          </header>
          <main className="rootMain">
            <Outlet />
          </main>
        </div>
      </QueryClientProvider>
    </ClerkProvider>
  );
};

export default RootLayout;