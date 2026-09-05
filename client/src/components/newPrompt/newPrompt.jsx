import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "./newPrompt.css";
import Upload from "../upload/upload";
import { IKImage } from "imagekitio-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth, useUser } from "@clerk/clerk-react";
import { useFeatureFlag } from "../../hooks/useFeatureFlags";

// SVG Icons
const CopyIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M16 12.9V17.1C16 20.6 14.6 22 11.1 22H6.9C3.4 22 2 20.6 2 17.1V12.9C2 9.4 3.4 8 6.9 8H11.1C14.6 8 16 9.4 16 12.9Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M22 6.9V11.1C22 14.6 20.6 16 17.1 16H16V12.9C16 9.4 14.6 8 11.1 8H8V6.9C8 3.4 9.4 2 12.9 2H17.1C20.6 2 22 3.4 22 6.9Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const EditIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path fillRule="evenodd" clipRule="evenodd" d="M12.9611 4.97827L12.9696 4.9696L12.9783 4.96107L15.0593 2.88009C15.4367 2.50264 15.7519 2.18747 16.0303 1.95108C16.3208 1.70449 16.6204 1.49984 16.9804 1.38289C17.5327 1.20343 18.1276 1.20343 18.6799 1.38289C19.0399 1.49985 19.3396 1.70459 19.6302 1.95127C19.9087 2.18777 20.224 2.50302 20.6017 2.88072L21.1192 3.39829C21.497 3.77599 21.8122 4.09126 22.0487 4.36986C22.2954 4.66042 22.5002 4.96007 22.6171 5.32007C22.7966 5.87239 22.7966 6.46734 22.6171 7.01966C22.5002 7.37965 22.2954 7.6793 22.0487 7.96987C21.8122 8.24846 21.497 8.56371 21.1193 8.94139L9.13087 20.9298C8.97204 21.0889 8.83188 21.2292 8.6676 21.3439C8.52309 21.4447 8.36722 21.5283 8.20321 21.5928C8.01677 21.6661 7.82231 21.7051 7.60193 21.7493L3.16217 22.6429C2.98735 22.6781 2.80998 22.7139 2.65927 22.7302C2.49975 22.7475 2.26511 22.7574 2.0213 22.6567C1.71417 22.5298 1.47021 22.2858 1.34332 21.9787C1.24259 21.7349 1.25253 21.5002 1.26981 21.3407C1.28614 21.19 1.32186 21.0127 1.35708 20.8379L2.2507 16.3981C2.2949 16.1777 2.3339 15.9832 2.40722 15.7968C2.47171 15.6328 2.55525 15.4769 2.65612 15.3324C2.77076 15.1681 2.90988 15.0292 3.06726 14.872L12.9611 4.97827ZM18.2164 2.80947C17.9654 2.7279 17.6949 2.7279 17.4439 2.80947C17.3472 2.84089 17.2205 2.90833 17.0011 3.09463C16.7749 3.28663 16.5029 3.55773 16.0984 3.96228L14.5607 5.5L18.5 9.43934L20.0371 7.90228C20.4418 7.49751 20.7131 7.22541 20.9052 6.9991C21.0917 6.77949 21.1591 6.6528 21.1905 6.55613C21.2721 6.30508 21.2721 6.03465 21.1905 5.78359C21.1591 5.68693 21.0917 5.56024 20.9052 5.34062C20.7131 5.11431 20.4418 4.84222 20.0371 4.43745L19.5626 3.96294C19.1578 3.55817 18.8857 3.2869 18.6594 3.09478C18.4398 2.90834 18.3131 2.84088 18.2164 2.80947ZM17.4393 10.5L13.5 6.56066L4.15955 15.9011C3.95351 16.1071 3.91538 16.149 3.88613 16.1909C3.85251 16.2391 3.82466 16.291 3.80317 16.3457C3.78451 16.3931 3.7705 16.4493 3.71224 16.7387L2.81791 21.1821L7.26126 20.2878C7.55072 20.2295 7.60686 20.2155 7.65428 20.1968C7.70895 20.1753 7.76091 20.1475 7.80908 20.1139C7.85087 20.0847 7.89362 20.0457 8.10241 19.8369L17.4393 10.5Z" fill="currentColor"/>
    <path d="M12.9999 21.2499C12.5857 21.2499 12.2499 21.5857 12.2499 21.9999C12.2499 22.4142 12.5857 22.7499 12.9999 22.7499H21.9999C22.4142 22.7499 22.7499 22.4142 22.7499 21.9999C22.7499 21.5857 22.4142 21.2499 21.9999 21.2499H12.9999Z" fill="currentColor"/>
  </svg>
);

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const CancelIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const LikeIcon = ({ filled }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"}>
    <path fillRule="evenodd" clipRule="evenodd" d="M12.4382 2.77841C12.2931 2.73181 12.1345 2.74311 11.9998 2.80804C11.8523 2.87913 11.7548 3.0032 11.7197 3.13821L11.244 4.97206C11.0777 5.61339 10.8354 6.23198 10.5235 6.81599C10.0392 7.72267 9.30632 8.42 8.62647 9.00585L7.18773 10.2456C6.96475 10.4378 6.8474 10.7258 6.87282 11.0198L7.68498 20.4125C7.72601 20.887 8.12244 21.25 8.59635 21.25H13.245C16.3813 21.25 19.0238 19.0677 19.5306 16.1371L20.2361 12.0574C20.3332 11.4959 19.9014 10.9842 19.3348 10.9842H14.1537C13.1766 10.9842 12.4344 10.1076 12.5921 9.14471L13.2548 5.10015C13.3456 4.54613 13.3197 3.97923 13.1787 3.43584C13.1072 3.16009 12.8896 2.92342 12.5832 2.82498L12.4382 2.77841L12.6676 2.06435L12.4382 2.77841ZM11.3486 1.45674C11.8312 1.2242 12.3873 1.18654 12.897 1.35029L13.042 1.39686L12.8126 2.11092L13.042 1.39686C13.819 1.64648 14.4252 2.26719 14.6307 3.0592C14.8241 3.80477 14.8596 4.58256 14.7351 5.34268L14.0724 9.38724C14.0639 9.439 14.1038 9.4842 14.1537 9.4842H19.3348C20.8341 9.4842 21.9695 10.8365 21.7142 12.313L21.0087 16.3928C20.3708 20.081 17.0712 22.75 13.245 22.75H8.59635C7.3427 22.75 6.29852 21.7902 6.19056 20.5417L5.3784 11.149C5.31149 10.3753 5.62022 9.61631 6.20855 9.10933L7.64729 7.86954C8.3025 7.30492 8.85404 6.75767 9.20042 6.10924C9.45699 5.62892 9.65573 5.12107 9.79208 4.59542L10.2678 2.76157C10.417 2.18627 10.8166 1.71309 11.3486 1.45674ZM2.96767 9.4849C3.36893 9.46758 3.71261 9.76945 3.74721 10.1696L4.71881 21.4061C4.78122 22.1279 4.21268 22.75 3.48671 22.75C2.80289 22.75 2.25 22.1953 2.25 21.5127V10.2342C2.25 9.83256 2.5664 9.50221 2.96767 9.4849Z" fill="currentColor"/>
  </svg>
);

const DislikeIcon = ({ filled }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"}>
    <path fillRule="evenodd" clipRule="evenodd" d="M12.4382 21.2216C12.2931 21.2682 12.1345 21.2569 11.9998 21.192C11.8523 21.1209 11.7548 20.9968 11.7197 20.8618L11.244 19.0279C11.0777 18.3866 10.8354 17.768 10.5235 17.184C10.0392 16.2773 9.30632 15.58 8.62647 14.9942L7.18773 13.7544C6.96475 13.5622 6.8474 13.2742 6.87282 12.9802L7.68498 3.58754C7.72601 3.11303 8.12244 2.75 8.59635 2.75H13.245C16.3813 2.75 19.0238 4.93226 19.5306 7.86285L20.2361 11.9426C20.3332 12.5041 19.9014 13.0158 19.3348 13.0158H14.1537C13.1766 13.0158 12.4344 13.8924 12.5921 14.8553L13.2548 18.8998C13.3456 19.4539 13.3197 20.0208 13.1787 20.5642C13.1072 20.8399 12.8896 21.0766 12.5832 21.175L12.4382 21.2216L12.6676 21.9356L12.4382 21.2216ZM11.3486 22.5433C11.8312 22.7758 12.3873 22.8135 12.897 22.6497L13.042 22.6031L12.8126 21.8891L13.042 22.6031C13.819 22.3535 14.4252 21.7328 14.6307 20.9408C14.8241 20.1952 14.8596 19.4174 14.7351 18.6573L14.0724 14.6128C14.0639 14.561 14.1038 14.5158 14.1537 14.5158H19.3348C20.8341 14.5158 21.9695 13.1635 21.7142 11.687L21.0087 7.60725C20.3708 3.91896 17.0712 1.25 13.245 1.25H8.59635C7.3427 1.25 6.29852 2.20975 6.19056 3.45832L5.3784 12.851C5.31149 13.6247 5.62022 14.3837 6.20855 14.8907L7.64729 16.1305C8.3025 16.6951 8.85404 17.2423 9.20042 17.8908C9.45699 18.3711 9.65573 18.8789 9.79208 19.4046L10.2678 21.2384C10.417 21.8137 10.8166 22.2869 11.3486 22.5433ZM2.96767 14.5151C3.36893 14.5324 3.71261 14.2306 3.74721 13.8304L4.71881 2.59389C4.78122 1.8721 4.21268 1.25 3.48671 1.25C2.80289 1.25 2.25 1.80474 2.25 2.48726V13.7658C2.25 14.1674 2.5664 14.4978 2.96767 14.5151Z" fill="currentColor"/>
  </svg>
);

const ShareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path fillRule="evenodd" clipRule="evenodd" d="M16.5 2.25C14.7051 2.25 13.25 3.70507 13.25 5.5C13.25 5.69591 13.2673 5.88776 13.3006 6.07412L8.56991 9.38558C8.54587 9.4024 8.52312 9.42038 8.50168 9.43939C7.94993 9.00747 7.25503 8.75 6.5 8.75C4.70507 8.75 3.25 10.2051 3.25 12C3.25 13.7949 4.70507 15.25 6.5 15.25C7.25503 15.25 7.94993 14.9925 8.50168 14.5606C8.52312 14.5796 8.54587 14.5976 8.56991 14.6144L13.3006 17.9259C13.2673 18.1122 13.25 18.3041 13.25 18.5C13.25 20.2949 14.7051 21.75 16.5 21.75C18.2949 21.75 19.75 20.2949 19.75 18.5C19.75 16.7051 18.2949 15.25 16.5 15.25C15.4472 15.25 14.5113 15.7506 13.9174 16.5267L9.43806 13.3911C9.63809 12.9694 9.75 12.4978 9.75 12C9.75 11.5022 9.63809 11.0306 9.43806 10.6089L13.9174 7.4733C14.5113 8.24942 15.4472 8.75 16.5 8.75C18.2949 8.75 19.75 7.29493 19.75 5.5C19.75 3.70507 18.2949 2.25 16.5 2.25ZM14.75 5.5C14.75 4.5335 15.5335 3.75 16.5 3.75C17.4665 3.75 18.25 4.5335 18.25 5.5C18.25 6.4665 17.4665 7.25 16.5 7.25C15.5335 7.25 14.75 6.4665 14.75 5.5ZM6.5 10.25C5.5335 10.25 4.75 11.0335 4.75 12C4.75 12.9665 5.5335 13.75 6.5 13.75C7.4665 13.75 8.25 12.9665 8.25 12C8.25 11.0335 7.4665 10.25 6.5 10.25ZM16.5 16.75C15.5335 16.75 14.75 17.5335 14.75 18.5C14.75 19.4665 15.5335 20.25 16.5 20.25C17.4665 20.25 18.25 19.4665 18.25 18.5C18.25 17.5335 17.4665 16.75 16.5 16.75Z" fill="currentColor"/>
  </svg>
);

const NewPrompt = ({ data, onFormReady }) => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [img, setImg] = useState({
    isLoading: false,
    error: "",
    dbData: {},
    aiData: {},
  });
  
  // Edit state
  const [editingIndex, setEditingIndex] = useState(null);
  const [editingText, setEditingText] = useState("");
  
  // Pending send — stores text when user presses Enter while image is uploading
  const pendingText = useRef(null);
  
  // Feedback state - initialize from backend data
  const [feedback, setFeedback] = useState(data?.feedback || {});

  // Rate-limit state — shows an upgrade prompt when the free plan quota is hit
  const [isRateLimited, setIsRateLimited] = useState(false);

  // Feature flag: sharing UI hides platform-wide while the flag is off
  const { enabled: sharingEnabled } = useFeatureFlag("enable_chat_sharing");

  const endRef = useRef(null);
  const formRef = useRef(null);

  const { user } = useUser();
  const userAvatar = user?.imageUrl;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data, question, answer, img.dbData, isThinking]);

  // Sync feedback from backend data
  useEffect(() => {
    if (data?.feedback) {
      setFeedback(data.feedback);
    }
  }, [data?.feedback]);

  const queryClient = useQueryClient();
  const { getToken, userId } = useAuth();

  const add = async (text, isInitial) => {
    if (!isInitial) setQuestion(text);
    setIsThinking(true);
    setAnswer("");
    setIsRateLimited(false);

    // Clear form input
    if (formRef.current) {
      formRef.current.reset();
    }

    try {
      const token = await getToken();

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/chats/${data._id}/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: isInitial ? undefined : text,
          img: img.dbData?.filePath || undefined,
        }),
      });

      if (!response.ok) {
        if (response.status === 429) {
          const limitError = new Error("RATE_LIMITED");
          limitError.isRateLimit = true;
          throw limitError;
        }
        throw new Error("Failed to stream AI response from backend");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";
      let hasStarted = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "").trim();
            if (dataStr === "[DONE]") {
              break;
            }
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.content) {
                if (!hasStarted) {
                  setIsThinking(false);
                  hasStarted = true;
                }
                accumulatedText += parsed.content;
                setAnswer(accumulatedText);
              }
            } catch (e) {
              // chunk boundary parse error ignored
            }
          }
        }
      }

      setIsThinking(false);

      Promise.all([
        queryClient.invalidateQueries({ queryKey: ["chat", data._id] }),
        queryClient.invalidateQueries({ queryKey: ["userChats"] }),
      ]).then(() => {
        formRef.current?.reset();
        setQuestion("");
        setAnswer("");
        setImg({
          isLoading: false,
          error: "",
          dbData: {},
          aiData: {},
        });
      });
    } catch (err) {
      console.error("Backend streaming error:", err);
      setIsThinking(false);
      hasRun.current = false;
      if (err.isRateLimit) {
        setQuestion("");
        setIsRateLimited(true);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const text = e.target.text.value;
    if (!text) return;

    // If image is still uploading, wait for it
    if (img.isLoading) {
      pendingText.current = text;
      return;
    }

    add(text, false);
  };

  const hasRun = useRef(false);

  useEffect(() => {
    if (!hasRun.current && data?.history?.length > 0) {
      const lastMessage = data.history[data.history.length - 1];
      const isLastMessageUser = lastMessage?.role === "user";
      const hasNoAiResponse = data.history.filter(m => m.role === "model").length === 0;

      if (isLastMessageUser && hasNoAiResponse && lastMessage?.parts?.length > 0) {
        add(lastMessage.parts[0].text, true);
      }
      hasRun.current = true;
    }
  }, [data]);

  useEffect(() => {
    if (onFormReady) {
      onFormReady({ handleSubmit, formRef, isThinking, img, setImg, userAvatar });
    }
  }, [isThinking, img, userAvatar]);

  // Auto-send when image finishes uploading (if user pressed Enter during upload)
  // Also clear pending text on upload error so user can retry
  useEffect(() => {
    if (!pendingText.current) return;

    if (img.isLoading) return;

    if (img.error) {
      pendingText.current = null;
      return;
    }

    if (img.dbData?.filePath) {
      const text = pendingText.current;
      pendingText.current = null;
      add(text, false);
    }
  }, [img.dbData, img.isLoading, img.error]);

  // Copy to clipboard
  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
  };

  // Start editing
  const handleEditStart = (index, text) => {
    setEditingIndex(index);
    setEditingText(text);
  };

  // Cancel editing
  const handleEditCancel = () => {
    setEditingIndex(null);
    setEditingText("");
  };

  // Confirm and resend edited message
  const handleEditConfirm = async () => {
    if (!editingText.trim()) return;
    
    const confirmed = window.confirm("Are you sure you want to resend this edited message?");
    if (!confirmed) return;
    
    const originalText = data.history[editingIndex]?.parts[0]?.text;
    
    try {
      const token = await getToken();
      
      // Save edit to backend
      await fetch(`${import.meta.env.VITE_API_URL}/api/chats/${data._id}/edit`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message_index: editingIndex,
          original_text: originalText,
          edited_text: editingText,
        }),
      });
      
      // Invalidate cache to refresh data
      queryClient.invalidateQueries({ queryKey: ["chat", data._id] });
    } catch (err) {
      console.error("Failed to save edit:", err);
    }
    
    setEditingIndex(null);
    setEditingText("");
    add(editingText, false);
  };

  // Feedback handlers
  const handleFeedback = async (messageIndex, type) => {
    const currentFeedback = feedback[messageIndex];
    const newFeedback = currentFeedback === type ? null : type;
    
    setFeedback(prev => ({
      ...prev,
      [messageIndex]: newFeedback
    }));

    try {
      const token = await getToken();
      
      await fetch(`${import.meta.env.VITE_API_URL}/api/chats/${data._id}/feedback`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message_index: messageIndex,
          feedback_type: newFeedback || "none",
        }),
      });
    } catch (err) {
      console.error("Failed to save feedback:", err);
    }
  };

  // Share handler - copy shared chat URL and mark as shared
  const handleShare = async () => {
    const chatUrl = `${window.location.origin}/shared/${data._id}`;
    navigator.clipboard.writeText(chatUrl);
    
    try {
      const token = await getToken();
      
      await fetch(`${import.meta.env.VITE_API_URL}/api/chats/${data._id}/share`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          is_shared: true,
        }),
      });
      
      // Invalidate cache to refresh data
      queryClient.invalidateQueries({ queryKey: ["chat", data._id] });
      queryClient.invalidateQueries({ queryKey: ["userChats"] });
    } catch (err) {
      console.error("Failed to update share status:", err);
    }
    
    alert("Chat link copied to clipboard!");
  };

  return (
    <>
      {data?.history?.map((message, i) => (
        <React.Fragment key={i}>
          <div
            className={
              message.role === "user"
                ? "message-wrapper user"
                : "message-wrapper ai"
            }
          >
            <div className="message-avatar">
              <img
                src={message.role === "user" ? (userAvatar || "/human1.jpeg") : "/logo.png"}
                alt={message.role === "user" ? "You" : "AI"}
              />
            </div>
            {message.role === "user" ? (
              <div className="message-content-wrapper">
                {editingIndex === i ? (
                  <div className="message editing">
                    <textarea
                      className="edit-textarea"
                      value={editingText}
                      onChange={(e) => setEditingText(e.target.value)}
                      rows={3}
                    />
                    <div className="edit-actions">
                      <button className="edit-btn confirm" onClick={handleEditConfirm} title="Send edited message">
                        <CheckIcon />
                      </button>
                      <button className="edit-btn cancel" onClick={handleEditCancel} title="Cancel edit">
                        <CancelIcon />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    {message.img && (
                      <div className="message-attachment">
                        <IKImage
                          urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
                          publicKey={import.meta.env.VITE_IMAGEKIT_URL_PUBLIC_KEY}
                          path={message.img}
                          width="300"
                          transformation={[{ width: 300 }]}
                          loading="lazy"
                          lqip={{ active: true, quality: 20 }}
                        />
                      </div>
                    )}
                    <div className="message">
                      <Markdown remarkPlugins={[remarkGfm]}>{message.parts[0].text}</Markdown>
                    </div>
                    <div className="message-actions">
                      <button className="action-btn" onClick={() => handleCopy(message.parts[0].text)} title="Copy">
                        <CopyIcon />
                      </button>
                      <button className="action-btn" onClick={() => handleEditStart(i, message.parts[0].text)} title="Edit">
                        <EditIcon />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="message-content-wrapper">
                <div className="message">
                  <Markdown remarkPlugins={[remarkGfm]}>{message.parts[0].text}</Markdown>
                </div>
                <div className="message-actions">
                  <button 
                    className={`action-btn ${feedback[i] === 'like' ? 'active' : ''}`} 
                    onClick={() => handleFeedback(i, 'like')} 
                    title="Like"
                  >
                    <LikeIcon filled={feedback[i] === 'like'} />
                  </button>
                  <button 
                    className={`action-btn ${feedback[i] === 'dislike' ? 'active' : ''}`} 
                    onClick={() => handleFeedback(i, 'dislike')} 
                    title="Dislike"
                  >
                    <DislikeIcon filled={feedback[i] === 'dislike'} />
                  </button>
                  {sharingEnabled && (
                    <button className="action-btn" onClick={handleShare} title="Share">
                      <ShareIcon />
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </React.Fragment>
      ))}

      {img.isLoading && <div className="loadingImage">Uploading image...</div>}

      {question && (
        <div className="message-wrapper user">
          <div className="message-avatar">
            <img src={userAvatar || "/human1.jpeg"} alt="You" />
          </div>
          <div className="message-content-wrapper">
            {img.dbData?.filePath && (
              <div className="message-attachment">
                <IKImage
                  urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
                  publicKey={import.meta.env.VITE_IMAGEKIT_URL_PUBLIC_KEY}
                  path={img.dbData?.filePath}
                  width="300"
                  transformation={[{ width: 300 }]}
                  loading="lazy"
                  lqip={{ active: true, quality: 20 }}
                />
              </div>
            )}
            <div className="message">{question}</div>
          </div>
        </div>
      )}

      {isThinking && !answer && (
        <div className="message-wrapper ai">
          <div className="message-avatar">
            <img src="/logo.png" alt="Boost AI" />
          </div>
          <div className="thinking-content">
            <div className="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}

      {isRateLimited && (
        <div className="message-wrapper ai">
          <div className="message-avatar">
            <img src="/logo.png" alt="Boost AI" />
          </div>
          <div className="message-content-wrapper">
            <div className="rateLimitBanner">
              <strong>You&apos;ve hit your free plan limit.</strong>
              <span>Upgrade to Pro for up to 40 AI messages per minute.</span>
              <Link to="/pricing" className="upgradeBtn">Upgrade to Pro</Link>
            </div>
          </div>
        </div>
      )}

      {answer && (
        <div className="message-wrapper ai">
          <div className="message-avatar">
            <img src="/logo.png" alt="Boost AI" />
          </div>
          <div className="message-content-wrapper">
            <div className="message">
              <Markdown remarkPlugins={[remarkGfm]}>{answer}</Markdown>
            </div>
            <div className="message-actions">
              <button 
                className={`action-btn ${feedback['streaming'] === 'like' ? 'active' : ''}`} 
                onClick={() => handleFeedback('streaming', 'like')} 
                title="Like"
              >
                <LikeIcon filled={feedback['streaming'] === 'like'} />
              </button>
              <button 
                className={`action-btn ${feedback['streaming'] === 'dislike' ? 'active' : ''}`} 
                onClick={() => handleFeedback('streaming', 'dislike')} 
                title="Dislike"
              >
                <DislikeIcon filled={feedback['streaming'] === 'dislike'} />
              </button>
              {sharingEnabled && (
                <button className="action-btn" onClick={handleShare} title="Share">
                  <ShareIcon />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="endChat" ref={endRef}></div>
    </>
  );
};

export default NewPrompt;
