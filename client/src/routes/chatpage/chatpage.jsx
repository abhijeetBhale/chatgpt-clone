import './chatpage.css';
import React, { useState, useRef, useCallback, useEffect } from 'react';
import NewPrompt from '../../components/newPrompt/newPrompt';
import ChatInput from '../../components/chatInput/chatInput';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/clerk-react';
import { useLocation } from 'react-router-dom';

const ScrollDownIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 5v14M19 12l-7 7-7-7" />
  </svg>
);

const Chatpage = () => {
  const path = useLocation().pathname;
  const chatId = path.split("/").pop();

  const { getToken } = useAuth();
  const [formState, setFormState] = useState(null);

  const scrollRef = useRef(null);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const { isPending, error, data } = useQuery({
    queryKey: ["chat", chatId],
    queryFn: async () => {
      const token = await getToken();

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/chats/${chatId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Failed to fetch");

      return res.json();
    },
  });

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollButton(distanceFromBottom > 200);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => el.removeEventListener("scroll", handleScroll);
  }, [handleScroll, data]);

  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, []);

  return (
    <div className="chatPage">
      <div className="wrapper chat-conversation" ref={scrollRef}>
        <div className="chat chat-conversation__content">
          {isPending ? (
            <div className="chatLoadingState">
              <div className="chatSpinner"></div>
              <span>Loading conversation...</span>
            </div>
          ) : error ? (
            <div className="chatErrorState">
              <span>Unable to load conversation history.</span>
            </div>
          ) : (
            data && <NewPrompt data={data} onFormReady={setFormState} />
          )}
        </div>
        <div className="chat-conversation__scroll-button-container">
          <button
            className={`chat-conversation__scroll-button ${showScrollButton ? "visible" : ""}`}
            onClick={scrollToBottom}
            aria-label="Scroll to bottom"
            type="button"
          >
            <ScrollDownIcon />
          </button>
        </div>
      </div>
      <ChatInput formState={formState} />
    </div>
  );
};

export default Chatpage;
