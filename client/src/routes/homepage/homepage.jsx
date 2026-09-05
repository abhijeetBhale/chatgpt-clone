import { Link } from "react-router-dom";
import "./homepage.css";
import PlasmaWave from "../../components/plasmaWave/PlasmaWave";

const Homepage = () => {
  return (
    <div className="homepage">
      <div className="homepagePlasmaBg">
        <PlasmaWave
          colors={["#ff7a17", "#7c3aed"]}
          speed1={0.04}
          speed2={0.03}
          focalLength={0.8}
          bend1={1}
          bend2={0.5}
          dir2={1.0}
          rotationDeg={0}
        />
      </div>
      <div className="heroContainer">
        <div className="eyebrowMono">
          // FRONTIER INTELLIGENCE WORKSPACE
        </div>
        <h1 className="heroDisplayTitle">
          Supercharge your creativity & intelligence
        </h1>
        <h2 className="heroSubtitle">
          Boost AI is your frontier reasoning partner — built for rapid synthesis, 
          intelligent code generation, and multi-modal execution.
        </h2>
        <div className="ctaGroup">
          <Link to="/dashboard" className="btnPillOutline">
            Get Started Free <span className="arrowSunset">→</span>
          </Link>
          <Link to="/dashboard" className="btnPillGhost">
            Explore Intelligence
          </Link>
        </div>
      </div>

      <footer className="homepageFooter">
        <div className="footerLeft">
          <div className="logoBadge">
            <img src="/logo.png" alt="Boost AI" className="footerLogo" />
          </div>
          <span>© 2026 Boost AI Inc. All rights reserved.</span>
        </div>
        <div className="footerRight">
          <Link to="/">Terms of Service</Link>
          <span className="divider">•</span>
          <Link to="/">Privacy Policy</Link>
          <span className="divider">•</span>
          <Link to="/">API Reference</Link>
        </div>
      </footer>
    </div>
  );
};

export default Homepage;
