import React from "react";
import "./chatInput.css";
import Upload from "../upload/upload";
import { useUser } from "@clerk/clerk-react";

const ChatInput = ({ formState }) => {
  const { handleSubmit, formRef, isThinking, img, setImg } = formState || {};
  const { user } = useUser();
  const userAvatar = user?.imageUrl;

  if (!handleSubmit) return null;

  return (
    <div className="chatInput">
      <div className="chatInputInner">
        <form onSubmit={handleSubmit} ref={formRef}>
          <Upload setImg={setImg} />
          <input id="file" type="file" multiple={false} hidden />
          <input type="text" name="text" placeholder="Ask anything or request assistance..." autoFocus />
          <button type="submit" disabled={isThinking} aria-label="Send message">
            <span className="sendIcon">↑</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInput;
