import './chatpage.css';
import React, { useState } from 'react';
import NewPrompt from '../../components/newPrompt/newPrompt';
import ChatInput from '../../components/chatInput/chatInput';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/clerk-react';
import { useLocation } from 'react-router-dom';

const Chatpage = () => {
  const path = useLocation().pathname;
  const chatId = path.split("/").pop();

  const { getToken } = useAuth();
  const [formState, setFormState] = useState(null);

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

  return (
    <div className="chatPage">
      <div className="wrapper">
        <div className="chat">
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
      </div>
      <ChatInput formState={formState} />
    </div>
  );
};

export default Chatpage;
