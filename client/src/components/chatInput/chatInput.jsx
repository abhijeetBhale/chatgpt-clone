import React from "react";
import "./chatInput.css";
import Upload from "../upload/upload";
import { useUser } from "@clerk/clerk-react";
import { IKImage } from "imagekitio-react";

const ChatInput = ({ formState }) => {
  const { handleSubmit, formRef, isThinking, img, setImg } = formState || {};
  const { user } = useUser();
  const userAvatar = user?.imageUrl;

  if (!handleSubmit) return null;

  const handleRemoveImage = () => {
    setImg({ isLoading: false, error: "", dbData: {}, aiData: {} });
  };

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
        <form onSubmit={handleSubmit} ref={formRef}>
          <Upload setImg={setImg} />
          <input id="file" type="file" multiple={false} hidden />
          <input type="text" name="text" placeholder={img.isLoading ? "Waiting for image..." : "Ask anything or request assistance..."} autoFocus disabled={img.isLoading} />
          <button type="submit" disabled={isThinking || img.isLoading} aria-label="Send message">
            <span className="sendIcon">↑</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInput;
