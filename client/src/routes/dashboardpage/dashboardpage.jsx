import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import { useState, useRef, useCallback } from "react";
import { IKImage } from "imagekitio-react";
import Upload from "../../components/upload/upload";
import UpgradeModal from "../../components/upgradeModal/upgradeModal";
import './dashboardpage.css';

const DashboardPage = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [inputText, setInputText] = useState("");
  const [img, setImg] = useState({
    isLoading: false,
    error: "",
    dbData: {},
    aiData: {},
  });
  const [upgradeModal, setUpgradeModal] = useState({ isOpen: false, details: null });
  const uploadRef = useRef(null);

  const mutation = useMutation({
    mutationFn: async ({ text, imgPath }) => {
      const token = await getToken();

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text, img: imgPath }),
      });

      if (!res.ok) {
        throw new Error("Failed to create chat");
      }

      return await res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["userChats"] });
      navigate(`/dashboard/chats/${data._id}`);
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() && !img.dbData?.filePath) return;

    // If image is still uploading, wait
    if (img.isLoading) return;

    const text = inputText.trim() || "Describe this image";
    const imgPath = img.dbData?.filePath || undefined;

    mutation.mutate({ text, imgPath });

    // Reset image state after sending
    setImg({ isLoading: false, error: "", dbData: {}, aiData: {} });
    setInputText("");
  };

  const handleOptionClick = (promptText) => {
    setInputText(promptText);
  };

  const handleRemoveImage = useCallback(() => {
    setImg({ isLoading: false, error: "", dbData: {}, aiData: {} });
  }, []);

  const handlePaste = useCallback((e) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file && uploadRef.current?.uploadFile) {
          uploadRef.current.uploadFile(file);
        }
        return;
      }
    }
  }, []);

  const handleUpgradeRequired = useCallback((details) => {
    setUpgradeModal({ isOpen: true, details });
  }, []);

  const closeUpgradeModal = useCallback(() => {
    setUpgradeModal({ isOpen: false, details: null });
  }, []);

  return (
    <div className="dashboardPage">
      <div className="texts">
        <div className="logoHeader">
          <div className="heroLogoBadge">
            <img src="/logo.png" alt="Boost AI" className="heroLogo" />
          </div>
          <div className="eyebrowMono">// FRONTIER REASONING PIPELINE</div>
          <h1>BOOST AI</h1>
          <p className="heroSubtitle">Engineered for deep reasoning, code generation & multi-modal synthesis.</p>
        </div>

        <div className="options">
          <div 
            className="optionCard"
            onClick={() => handleOptionClick("Create a structured strategy for my project")}
          >
            <div className="optionIcon">💬</div>
            <div className="optionContent">
              <span className="optionTitle">Create a New Chat</span>
              <span className="optionDesc">Start an open-ended reasoning session</span>
            </div>
          </div>

          <div 
            className="optionCard"
            onClick={() => handleOptionClick("Analyze the image and summarize key details")}
          >
            <div className="optionIcon">📷</div>
            <div className="optionContent">
              <span className="optionTitle">Analyze Images</span>
              <span className="optionDesc">Extract data & vision capabilities</span>
            </div>
          </div>

          <div 
            className="optionCard"
            onClick={() => handleOptionClick("Help me refactor and optimize my code")}
          >
            <div className="optionIcon">⚡</div>
            <div className="optionContent">
              <span className="optionTitle">Help with Code</span>
              <span className="optionDesc">Debug, refactor & generate code</span>
            </div>
          </div>
        </div>
      </div>

      <div className="formContainer">
        {img.dbData?.filePath && (
          <div className="dashboardImagePreview">
            <IKImage
              urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
              publicKey={import.meta.env.VITE_IMAGEKIT_URL_PUBLIC_KEY}
              path={img.dbData?.filePath}
              width="120"
              transformation={[{ width: 120 }]}
            />
            <button
              type="button"
              className="dashboardImageRemove"
              onClick={handleRemoveImage}
              title="Remove image"
            >
              ×
            </button>
          </div>
        )}
        {img.isLoading && (
          <div className="dashboardImagePreview">
            <div className="dashboardImageLoading">Uploading image...</div>
          </div>
        )}
        {img.error && (
          <div className="dashboardImageError">{img.error}</div>
        )}
        <form onSubmit={handleSubmit}>
          <Upload ref={uploadRef} setImg={setImg} onUpgradeRequired={handleUpgradeRequired} />
          <input 
            type="text" 
            name="text" 
            placeholder={img.isLoading ? "Waiting for image..." : "Ask anything or attach an image..."}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={mutation.isPending || img.isLoading}
            autoFocus
            onPaste={handlePaste}
          />
          <button type="submit" disabled={mutation.isPending || img.isLoading || (!inputText.trim() && !img.dbData?.filePath)}>
            {mutation.isPending ? (
              <span className="buttonSpinner"></span>
            ) : (
              <span className="sendArrow">↑</span>
            )}
          </button>
        </form>
      </div>
      <UpgradeModal
        isOpen={upgradeModal.isOpen}
        onClose={closeUpgradeModal}
        currentPlan={upgradeModal.details?.currentPlan}
        maxFileSizeMB={upgradeModal.details?.maxFileSizeMB}
      />
    </div>
  );
};

export default DashboardPage;
