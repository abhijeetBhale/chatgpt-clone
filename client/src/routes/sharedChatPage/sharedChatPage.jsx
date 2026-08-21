import { useParams, useNavigate } from "react-router-dom";
import { SignIn, useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import "./sharedChatPage.css";

const SharedChatPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { userId, isLoaded } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(true);

  useEffect(() => {
    if (isLoaded && userId) {
      // User is logged in, redirect to shared chat view
      navigate(`/dashboard/shared/${id}`, { replace: true });
    }
  }, [isLoaded, userId, navigate, id]);

  const handleCloseModal = () => {
    setShowLoginModal(false);
    navigate("/");
  };

  if (!isLoaded) {
    return (
      <div className="sharedChatLoading">
        <div className="loadingSpinner"></div>
        <span>Loading...</span>
      </div>
    );
  }

  if (userId) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="sharedChatPage">
      <div className="sharedChatOverlay" onClick={handleCloseModal}>
        <div className="sharedChatModal" onClick={(e) => e.stopPropagation()}>
          <button className="modalCloseBtn" onClick={handleCloseModal}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
          
          <div className="modalHeader">
            <img src="/logo.png" alt="Boost AI" className="modalLogo" />
            <h2>Sign in to view this chat</h2>
            <p>This chat was shared with you. Sign in or create an account to continue the conversation.</p>
          </div>

          <div className="modalSignIn">
            <SignIn 
              path="/sign-in" 
              signUpUrl="/sign-up" 
              forceRedirectUrl={`/dashboard/shared/${id}`}
              routing="path"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SharedChatPage;
