import { Link } from "react-router-dom";
import "./upgradeModal.css";

const UpgradeModal = ({ isOpen, onClose, title, description, currentPlan, maxFileSizeMB }) => {
  if (!isOpen) return null;

  return (
    <div className="upgradeModalOverlay" onClick={onClose}>
      <div className="upgradeModal" onClick={(e) => e.stopPropagation()}>
        <button className="upgradeModalClose" onClick={onClose} title="Close">
          ×
        </button>
        <div className="upgradeModalIcon">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h2 className="upgradeModalTitle">{title || "Upgrade to Pro"}</h2>
        <p className="upgradeModalDesc">
          {description || (
            <>
              You've reached the <strong>{maxFileSizeMB}MB</strong> file size limit on the <strong>{currentPlan || "Free"}</strong> plan.
              Upgrade to Pro for larger file uploads and more features.
            </>
          )}
        </p>
        <div className="upgradeModalFeatures">
          <div className="upgradeFeature">
            <span className="upgradeFeatureIcon">✓</span>
            <span>Up to 20MB image uploads</span>
          </div>
          <div className="upgradeFeature">
            <span className="upgradeFeatureIcon">✓</span>
            <span>4x higher rate limits</span>
          </div>
          <div className="upgradeFeature">
            <span className="upgradeFeatureIcon">✓</span>
            <span>Priority AI response</span>
          </div>
        </div>
        <div className="upgradeModalActions">
          <Link to="/pricing" className="upgradeModalBtn primary">
            Upgrade to Pro
          </Link>
          <button className="upgradeModalBtn secondary" onClick={onClose}>
            Continue with Free
          </button>
        </div>
      </div>
    </div>
  );
};

export default UpgradeModal;
