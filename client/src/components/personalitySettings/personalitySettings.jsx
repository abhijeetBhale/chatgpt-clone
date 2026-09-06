import { useState, useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import "./personalitySettings.css";

const PersonalitySettings = ({ isOpen, onClose }) => {
  const { getToken } = useAuth();
  const [prefs, setPrefs] = useState({
    tone: "balanced",
    responseLength: "adaptive",
    expertiseLevel: "auto",
    humorLevel: 0.5,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [learningSummary, setLearningSummary] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchPreferences();
      fetchLearningSummary();
    }
  }, [isOpen]);

  const fetchPreferences = async () => {
    try {
      const token = await getToken();
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/preferences`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPrefs({
          tone: data.tone || "balanced",
          responseLength: data.responseLength || "adaptive",
          expertiseLevel: data.expertiseLevel || "auto",
          humorLevel: data.humorLevel ?? 0.5,
        });
      }
    } catch (err) {
      console.error("Failed to fetch preferences:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLearningSummary = async () => {
    try {
      const token = await getToken();
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/preferences/learning-summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setLearningSummary(data);
      }
    } catch (err) {
      console.error("Failed to fetch learning summary:", err);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = await getToken();
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/preferences`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          tone: prefs.tone,
          response_length: prefs.responseLength,
          expertise_level: prefs.expertiseLevel,
          humor_level: prefs.humorLevel,
        }),
      });
      if (res.ok) {
        onClose();
      }
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="personalityOverlay" onClick={onClose}>
      <div className="personalityModal" onClick={(e) => e.stopPropagation()}>
        <button className="personalityClose" onClick={onClose}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>

        <div className="personalityHeader">
          <div className="personalityIcon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
          </div>
          <h2>AI Personality</h2>
          <p>Customize how Boost AI responds to you</p>
        </div>

        {loading ? (
          <div className="personalityLoading">
            <div className="loadingSpinner"></div>
            <span>Loading preferences...</span>
          </div>
        ) : (
          <div className="personalityContent">
            {/* Tone Selection */}
            <div className="settingGroup">
              <label className="settingLabel">Tone</label>
              <p className="settingDesc">How should the AI communicate?</p>
              <div className="toneGrid">
                {[
                  { value: "formal", label: "Formal", icon: "👔", desc: "Professional & structured" },
                  { value: "casual", label: "Casual", icon: "😊", desc: "Friendly & relaxed" },
                  { value: "enthusiastic", label: "Enthusiastic", icon: "🎉", desc: "Energetic & positive" },
                  { value: "minimal", label: "Minimal", icon: "⚡", desc: "Ultra-concise & direct" },
                  { value: "balanced", label: "Balanced", icon: "⚖️", desc: "Adaptive & natural" },
                ].map((tone) => (
                  <button
                    key={tone.value}
                    className={`toneOption ${prefs.tone === tone.value ? "active" : ""}`}
                    onClick={() => setPrefs({ ...prefs, tone: tone.value })}
                  >
                    <span className="toneIcon">{tone.icon}</span>
                    <span className="toneLabel">{tone.label}</span>
                    <span className="toneDesc">{tone.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Response Length */}
            <div className="settingGroup">
              <label className="settingLabel">Response Length</label>
              <p className="settingDesc">How detailed should responses be?</p>
              <div className="radioGroup">
                {[
                  { value: "concise", label: "Concise", desc: "Short, focused answers" },
                  { value: "detailed", label: "Detailed", desc: "Comprehensive explanations" },
                  { value: "adaptive", label: "Adaptive", desc: "Matches question complexity" },
                ].map((option) => (
                  <label key={option.value} className={`radioOption ${prefs.responseLength === option.value ? "active" : ""}`}>
                    <input
                      type="radio"
                      name="responseLength"
                      value={option.value}
                      checked={prefs.responseLength === option.value}
                      onChange={(e) => setPrefs({ ...prefs, responseLength: e.target.value })}
                    />
                    <span className="radioLabel">{option.label}</span>
                    <span className="radioDesc">{option.desc}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Expertise Level */}
            <div className="settingGroup">
              <label className="settingLabel">Your Expertise</label>
              <p className="settingDesc">Adjusts explanation complexity</p>
              <div className="radioGroup">
                {[
                  { value: "beginner", label: "Beginner", desc: "Simple explanations, no jargon" },
                  { value: "intermediate", label: "Intermediate", desc: "Balanced detail" },
                  { value: "expert", label: "Expert", desc: "Technical, skip basics" },
                  { value: "auto", label: "Auto-detect", desc: "Learns from conversation" },
                ].map((option) => (
                  <label key={option.value} className={`radioOption ${prefs.expertiseLevel === option.value ? "active" : ""}`}>
                    <input
                      type="radio"
                      name="expertiseLevel"
                      value={option.value}
                      checked={prefs.expertiseLevel === option.value}
                      onChange={(e) => setPrefs({ ...prefs, expertiseLevel: e.target.value })}
                    />
                    <span className="radioLabel">{option.label}</span>
                    <span className="radioDesc">{option.desc}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Humor Level */}
            <div className="settingGroup">
              <label className="settingLabel">Humor Level</label>
              <p className="settingDesc">How much personality and wit?</p>
              <div className="sliderContainer">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={prefs.humorLevel}
                  onChange={(e) => setPrefs({ ...prefs, humorLevel: parseFloat(e.target.value) })}
                  className="humorSlider"
                />
                <div className="sliderLabels">
                  <span>Serious</span>
                  <span className="sliderValue">{Math.round(prefs.humorLevel * 100)}%</span>
                  <span>Playful</span>
                </div>
              </div>
            </div>

            {/* Learning Status */}
            {learningSummary && (
              <div className="learningStatus">
                <div className="learningHeader">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
                  </svg>
                  <span>Learning Status</span>
                </div>
                <div className="learningStats">
                  <div className="stat">
                    <span className="statValue">{learningSummary.preferences?.feedback_count || 0}</span>
                    <span className="statLabel">Feedback signals</span>
                  </div>
                  <div className="stat">
                    <span className="statValue">{learningSummary.memories_count || 0}</span>
                    <span className="statLabel">Memories</span>
                  </div>
                </div>
                {learningSummary.preferences?.feedback_count < 5 && (
                  <p className="learningNote">
                    Give {5 - learningSummary.preferences.feedback_count} more feedback signals to enable auto-learning
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <div className="personalityFooter">
          <button className="btnCancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btnSave" onClick={handleSave} disabled={saving || loading}>
            {saving ? "Saving..." : "Save Preferences"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PersonalitySettings;