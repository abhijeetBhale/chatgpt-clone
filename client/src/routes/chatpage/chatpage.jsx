import './chatpage.css';
import React from 'react';
import NewPrompt from '../../components/newPrompt/newPrompt';
import { useQuery } from '@tanstack/react-query';
import { useAuth, useUser } from '@clerk/clerk-react';
import { useLocation } from 'react-router-dom';
import Markdown from "react-markdown";
import { IKImage } from 'imagekitio-react';

const Chatpage = () => {
  const path = useLocation().pathname;
  const chatId = path.split("/").pop();

  const { getToken } = useAuth();
  const { user } = useUser();
  const userAvatar = user?.imageUrl;

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
            data?.history?.map((message, i) => (
              <React.Fragment key={i}>
                {message.img && (
                  <div className="message-wrapper user">
                    <div className="message-avatar">
                      <img src={userAvatar || "/human1.jpeg"} alt="You" />
                    </div>
                    <div className="messageImageContainer">
                      <IKImage
                        urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
                        path={message.img}
                        height="300"
                        width="400"
                        transformation={[{ height: 300, width: 400 }]}
                        loading="lazy"
                        lqip={{ active: true, quality: 20 }}
                      />
                    </div>
                  </div>
                )}
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
                  <div className="message">
                    <Markdown>{message.parts[0].text}</Markdown>
                  </div>
                </div>
              </React.Fragment>
            ))
          )}

          {data && <NewPrompt data={data} />}
        </div>
      </div>
    </div>
  );
};

export default Chatpage;
