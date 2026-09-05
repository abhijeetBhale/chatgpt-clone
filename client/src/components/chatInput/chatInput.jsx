import React, { useRef, useCallback, useState } from "react";
import "./chatInput.css";
import Upload from "../upload/upload";
import UpgradeModal from "../upgradeModal/upgradeModal";
import { IKImage } from "imagekitio-react";

const ChatInput = ({ formState }) => {
  const { handleSubmit, formRef, isThinking, img, setImg } = formState || {};
  const uploadRef = useRef(null);
  const [upgradeModal, setUpgradeModal] = useState({ isOpen: false, details: null });

  const handleRemoveImage = useCallback(() => {
    setImg({ isLoading: false, error: "", dbData: {}, aiData: {} });
  }, [setImg]);

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

  if (!handleSubmit) return null;

  return (
    <div className="chatInput">
      <div className="chatInputInner">
        {img.dbData?.filePath && (
          <div className="chatInputPreview">
            <div className="chatInputPreviewImage">
              <IKImage
                urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
                publicKey={import.meta.env.VITE_IMAGEKIT_URL_PUBLIC_KEY}
                path={img.dbData?.filePath}
                width="120"
                transformation={[{ width: 120 }]}
              />
              <button
                type="button"
                className="chatInputPreviewRemove"
                onClick={handleRemoveImage}
                title="Remove image"
              >
                ×
              </button>
            </div>
          </div>
        )}
        {img.isLoading && (
          <div className="chatInputPreview">
            <div className="chatInputPreviewLoading">Uploading image...</div>
          </div>
        )}
        {img.error && (
          <div className="chatInputError">{img.error}</div>
        )}
        <form onSubmit={handleSubmit} ref={formRef}>
          <Upload ref={uploadRef} setImg={setImg} onUpgradeRequired={handleUpgradeRequired} />
          <input
            type="text"
            name="text"
            placeholder={img.isLoading ? "Waiting for image..." : "Ask anything or request assistance..."}
            autoFocus
            disabled={img.isLoading}
            onPaste={handlePaste}
          />
          <button type="submit" disabled={isThinking || img.isLoading} aria-label="Send message">
            <span className="sendIcon">↑</span>
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

export default ChatInput;
