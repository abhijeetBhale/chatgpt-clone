import { Link, Outlet } from 'react-router-dom';
import './rootLayout.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ClerkProvider, SignedIn, SignedOut, UserButton, SignInButton, useAuth } from '@clerk/clerk-react';
import { useIsAdmin, useFeatureFlag } from '../../hooks/useFeatureFlags';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!PUBLISHABLE_KEY) {
  throw new Error('Missing Publishable Key');
}

// Pricing tab — hidden platform-wide while the show_pricing_page flag is off.
const PricingNavTab = () => {
  const { enabled, isLoading } = useFeatureFlag('show_pricing_page');
  if (isLoading || !enabled) return null;
  return <Link to="/pricing" className="pricingLink">Pricing</Link>;
};

const queryClient = new QueryClient();

// Lives inside <ClerkProvider> so it can read billing entitlements.
const HeaderUser = () => {
  const { has } = useAuth();
  const isPro = has?.({ plan: 'pro' });
  const { data: adminSession } = useIsAdmin();

  return (
    <>
      <SignedIn>
        {adminSession?.is_admin && (
          <Link to="/admin" className="adminNavTab">Feature Flags</Link>
        )}
      </SignedIn>
      {isPro && (
        <Link to="/pricing" className="proBadge">PRO ✦</Link>
      )}
      <div className={`avatarRing ${isPro ? 'pro' : ''}`}>
        <UserButton
          appearance={{
            elements: {
              userButtonAvatarBox: {
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                border: isPro
                  ? '2px solid #0a0a0a'
                  : '1px solid var(--color-hairline-translucent)'
              }
            }
          }}
        />
      </div>
    </>
  );
};

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
              <PricingNavTab />
              <SignedIn>
                <HeaderUser />
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