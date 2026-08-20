import { Link } from "react-router-dom";
import "./homepage.css";
import { TypeAnimation } from "react-type-animation";
import { useState } from "react";

const Homepage = () => {
  const [typingStatus, setTypingStatus] = useState("human1");

  return (
    <div className="homepage">
      <div className="heroContainer">
        <div className="left">
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

        <div className="right">
          <div className="mockupCard">
            <div className="mockupHeader">
              <div className="windowDots">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
              </div>
              <div className="windowTitle">boost-ai-frontier.ts</div>
            </div>

            <div className="mockupBody">
              <div className="codePreview">
                <div><span className="lineNum">01</span><span className="tokenKeyword">import</span> {'{'} BoostAI {'}'} <span className="tokenKeyword">from</span> <span className="tokenString">'@xai/boost'</span>;</div>
                <div><span className="lineNum">02</span></div>
                <div><span className="lineNum">03</span><span className="tokenComment">// Initialize Grok-level reasoning engine</span></div>
                <div><span className="lineNum">04</span><span className="tokenKeyword">const</span> agent = <span className="tokenKeyword">new</span> BoostAI({'{'} engine: <span className="tokenString">'grok-3.0'</span> {'}'});</div>
                <div><span className="lineNum">05</span><span className="tokenKeyword">const</span> res = <span className="tokenKeyword">await</span> agent.reason(prompt);</div>
              </div>

              <div className="chatOverlay">
                <div className="chatAvatar">
                  <img
                    src={typingStatus === "human1" ? "/human1.jpeg" : "/logo.png"}
                    alt="Avatar"
                  />
                </div>
                <div className="chatBubble">
                  <TypeAnimation
                    sequence={[
                      "Which AI workspace provides the fastest reasoning?",
                      2200,
                      () => setTypingStatus("bot"),
                      "Boost AI executes instant streaming and multi-modal problem solving.",
                      2500,
                      () => setTypingStatus("human1"),
                      "Can you solve (2 + 3i)x + 5 = 10 - 2i?",
                      2200,
                      () => setTypingStatus("bot"),
                      "x = 4/13 - (19/13)i. Solved in 12ms.",
                      2500,
                      () => setTypingStatus("human1"),
                    ]}
                    wrapper="span"
                    repeat={Infinity}
                    cursor={true}
                    omitDeletionAnimation={true}
                  />
                </div>
              </div>
            </div>
          </div>
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
