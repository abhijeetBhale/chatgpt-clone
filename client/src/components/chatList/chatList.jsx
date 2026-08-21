import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./chatList.css";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/clerk-react";

// Shared Icon SVG
const SharedIcon = ({ className = "sharedIcon" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" className={className}>
    <path fillRule="evenodd" clipRule="evenodd" d="M16.5 2.25C14.7051 2.25 13.25 3.70507 13.25 5.5C13.25 5.69591 13.2673 5.88776 13.3006 6.07412L8.56991 9.38558C8.54587 9.4024 8.52312 9.42038 8.50168 9.43939C7.94993 9.00747 7.25503 8.75 6.5 8.75C4.70507 8.75 3.25 10.2051 3.25 12C3.25 13.7949 4.70507 15.25 6.5 15.25C7.25503 15.25 7.94993 14.9925 8.50168 14.5606C8.52312 14.5796 8.54587 14.5976 8.56991 14.6144L13.3006 17.9259C13.2673 18.1122 13.25 18.3041 13.25 18.5C13.25 20.2949 14.7051 21.75 16.5 21.75C18.2949 21.75 19.75 20.2949 19.75 18.5C19.75 16.7051 18.2949 15.25 16.5 15.25C15.4472 15.25 14.5113 15.7506 13.9174 16.5267L9.43806 13.3911C9.63809 12.9694 9.75 12.4978 9.75 12C9.75 11.5022 9.63809 11.0306 9.43806 10.6089L13.9174 7.4733C14.5113 8.24942 15.4472 8.75 16.5 8.75C18.2949 8.75 19.75 7.29493 19.75 5.5C19.75 3.70507 18.2949 2.25 16.5 2.25ZM14.75 5.5C14.75 4.5335 15.5335 3.75 16.5 3.75C17.4665 3.75 18.25 4.5335 18.25 5.5C18.25 6.4665 17.4665 7.25 16.5 7.25C15.5335 7.25 14.75 6.4665 14.75 5.5ZM6.5 10.25C5.5335 10.25 4.75 11.0335 4.75 12C4.75 12.9665 5.5335 13.75 6.5 13.75C7.4665 13.75 8.25 12.9665 8.25 12C8.25 11.0335 7.4665 10.25 6.5 10.25ZM16.5 16.75C15.5335 16.75 14.75 17.5335 14.75 18.5C14.75 19.4665 15.5335 20.25 16.5 20.25C17.4665 20.25 18.25 19.4665 18.25 18.5C18.25 17.5335 17.4665 16.75 16.5 16.75Z" fill="currentColor"/>
  </svg>
);

const PlusIcon = ({ className = "svgNavIcon" }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M12 5v14M5 12h14" />
  </svg>
);

const HomeIcon = ({ className = "svgNavIcon" }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="1.75" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1V9.5z" />
  </svg>
);

const ChatBubbleIcon = ({ className = "svgChatIcon" }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
  >
    <path 
      fillRule="evenodd" 
      clipRule="evenodd" 
      d="M10.4606 1.25H13.5394C15.1427 1.24999 16.3997 1.24999 17.4039 1.34547C18.4274 1.44279 19.2655 1.64457 20.0044 2.09732C20.7781 2.57144 21.4286 3.22194 21.9027 3.99563C22.3554 4.73445 22.5572 5.57256 22.6545 6.59611C22.75 7.60029 22.75 8.85725 22.75 10.4606V11.5278C22.75 12.6691 22.75 13.564 22.7007 14.2868C22.6505 15.0223 22.5468 15.6344 22.3123 16.2004C21.7287 17.6093 20.6093 18.7287 19.2004 19.3123C18.3955 19.6457 17.4786 19.7197 16.2233 19.7413C15.7842 19.7489 15.5061 19.7545 15.2941 19.7779C15.096 19.7999 15.0192 19.832 14.9742 19.8582C14.9268 19.8857 14.8622 19.936 14.7501 20.0898C14.6287 20.2564 14.4916 20.4865 14.2742 20.8539L13.7321 21.7697C12.9585 23.0767 11.0415 23.0767 10.2679 21.7697L9.72579 20.8539C9.50835 20.4865 9.37122 20.2564 9.24985 20.0898C9.13772 19.936 9.07313 19.8857 9.02572 19.8582C8.98078 19.832 8.90399 19.7999 8.70588 19.7779C8.49387 19.7545 8.21575 19.7489 7.77666 19.7413C6.52138 19.7197 5.60454 19.6457 4.79957 19.3123C3.39066 18.7287 2.27128 17.6093 1.68769 16.2004C1.45323 15.6344 1.3495 15.0223 1.29932 14.2868C1.24999 13.564 1.25 12.6691 1.25 11.5278L1.25 10.4606C1.24999 8.85726 1.24999 7.60029 1.34547 6.59611C1.44279 5.57256 1.64457 4.73445 2.09732 3.99563C2.57144 3.22194 3.22194 2.57144 3.99563 2.09732C4.73445 1.64457 5.57256 1.44279 6.59611 1.34547C7.60029 1.24999 8.85726 1.24999 10.4606 1.25ZM6.73809 2.83873C5.82434 2.92561 5.24291 3.09223 4.77938 3.37628C4.20752 3.72672 3.72672 4.20752 3.37628 4.77938C3.09223 5.24291 2.92561 5.82434 2.83873 6.73809C2.75079 7.663 2.75 8.84876 2.75 10.5V11.5C2.75 12.6751 2.75041 13.5189 2.79584 14.1847C2.84081 14.8438 2.92737 15.2736 3.07351 15.6264C3.50486 16.6678 4.33223 17.4951 5.3736 17.9265C5.88923 18.1401 6.54706 18.2199 7.8025 18.2416L7.83432 18.2421C8.23232 18.249 8.58109 18.2549 8.87097 18.287C9.18246 18.3215 9.4871 18.3912 9.77986 18.5615C10.0702 18.7304 10.2795 18.9559 10.4621 19.2063C10.6307 19.4378 10.804 19.7306 11.0004 20.0623L11.5587 21.0057C11.7515 21.3313 12.2485 21.3313 12.4412 21.0057L12.9996 20.0623C13.1959 19.7306 13.3692 19.4378 13.5379 19.2063C13.7204 18.9559 13.9298 18.7304 14.2201 18.5615C14.5129 18.3912 14.8175 18.3215 15.129 18.287C15.4189 18.2549 15.7676 18.249 16.1656 18.2421L16.1975 18.2416C17.4529 18.2199 18.1108 18.1401 18.6264 17.9265C19.6678 17.4951 20.4951 16.6678 20.9265 15.6264C21.0726 15.2736 21.1592 14.8438 21.2042 14.1847C21.2496 13.5189 21.25 12.6751 21.25 11.5V10.5C21.25 8.84876 21.2492 7.663 21.1613 6.73809C21.0744 5.82434 20.9078 5.24291 20.6237 4.77938C20.2733 4.20752 19.7925 3.72672 19.2206 3.37628C18.7571 3.09223 18.1757 2.92561 17.2619 2.83873C16.337 2.75079 15.1512 2.75 13.5 2.75H10.5C8.84876 2.75 7.663 2.75079 6.73809 2.83873ZM7.25 9C7.25 8.58579 7.58579 8.25 8 8.25H16C16.4142 8.25 16.75 8.58579 16.75 9C16.75 9.41421 16.4142 9.75 16 9.75H8C7.58579 9.75 7.25 9.41421 7.25 9ZM7.25 12.5C7.25 12.0858 7.58579 11.75 8 11.75H13.5C13.9142 11.75 14.25 12.0858 14.25 12.5C14.25 12.9142 13.9142 13.25 13.5 13.25H8C7.58579 13.25 7.25 12.9142 7.25 12.5Z" 
      fill="currentColor" 
    />
  </svg>
);

const ChatList = () => {
  const { getToken } = useAuth();
  const location = useLocation();
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  const { isPending, error, data } = useQuery({
    queryKey: ["userChats"],
    queryFn: async () => {
      const token = await getToken();

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/userchats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Failed to fetch");

      return res.json();
    },
  });

  return (
    <div className="chatList">
      <div className="chatListSection">
        <span className="eyebrowMono">// DASHBOARD</span>
        <nav className="navGroup">
          <Link 
            to="/dashboard" 
            className={`navItem ${location.pathname === "/dashboard" ? "active" : ""}`}
          >
            <PlusIcon /> Create new chat
          </Link>
          <Link 
            to="/" 
            className={`navItem ${location.pathname === "/" ? "active" : ""}`}
          >
            <HomeIcon /> Home Page
          </Link>
        </nav>
      </div>

      <hr className="dividerHairline" />

      <div className="chatListSection flex1">
        <div className="recentHeader">
          <span className="eyebrowMono">// RECENT CHATS</span>
          <span className="countBadge">{data?.length || 0}</span>
        </div>

        <div className="list">
          {isPending ? (
            <div className="listSkeleton">
              <div className="skeletonItem"></div>
              <div className="skeletonItem"></div>
              <div className="skeletonItem"></div>
            </div>
          ) : error ? (
            <div className="listError">Unable to load chats</div>
          ) : !data || data.length === 0 ? (
            <div className="emptyState">No recent conversations</div>
          ) : (
            data.map((chat) => {
              const isActive = location.pathname.includes(chat._id);
              return (
                <Link 
                  to={`/dashboard/chats/${chat._id}`} 
                  key={chat._id}
                  className={`chatItem ${isActive ? "active" : ""}`}
                >
                  <ChatBubbleIcon className={`svgChatIcon ${isActive ? "activeIcon" : ""}`} />
                  <span className="chatTitle">{chat.title || "Untitled Chat"}</span>
                  {chat.isShared && <SharedIcon className="sharedChatIcon" />}
                </Link>
              );
            })
          )}
        </div>
      </div>

      <hr className="dividerHairline" />

      <div className="upgradeCard" onClick={() => setShowUpgradeModal(true)}>
        <div className="upgradeIcon">
          <img src="/logo.png" alt="Pro" />
        </div>
        <div className="upgradeTexts">
          <span className="title">Upgrade to Pro <span className="sparkle">✦</span></span>
          <span className="sub">Unlimited access & Grok reasoning</span>
        </div>
      </div>

      {showUpgradeModal && (
        <div className="upgradeModalOverlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="upgradeModal" onClick={(e) => e.stopPropagation()}>
            <button className="upgradeModalClose" onClick={() => setShowUpgradeModal(false)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
            <div className="upgradeModalHeader">
              <img src="/logo.png" alt="Pro" className="upgradeModalLogo" />
              <h2 className="upgradeModalTitle">Upgrade to Pro <span className="sparkle">✦</span></h2>
              <p className="upgradeModalSub">Unlock the full power of Boost AI</p>
            </div>
            <div className="upgradeModalPlans">
              <div className="planCard">
                <span className="planBadge">Popular</span>
                <span className="planName">Monthly</span>
                <span className="planPrice">$19<span className="planPeriod">/mo</span></span>
                <ul className="planFeatures">
                  <li>Unlimited conversations</li>
                  <li>Grok reasoning engine</li>
                  <li>Priority support</li>
                  <li>Custom instructions</li>
                </ul>
                <button className="planButton primary">Get Started</button>
              </div>
              <div className="planCard">
                <span className="planBadge save">Save 20%</span>
                <span className="planName">Annual</span>
                <span className="planPrice">$15<span className="planPeriod">/mo</span></span>
                <ul className="planFeatures">
                  <li>Everything in Monthly</li>
                  <li>Early access to features</li>
                  <li>Advanced analytics</li>
                  <li>API access</li>
                </ul>
                <button className="planButton">Get Started</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatList;