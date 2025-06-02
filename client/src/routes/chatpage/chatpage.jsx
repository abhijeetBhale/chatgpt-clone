import './chatpage.css'
import NewPrompt from '../../components/newPrompt/newPrompt';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/clerk-react';
import { useLocation } from 'react-router-dom';
import Markdown from "react-markdown";
import { IKImage } from 'imagekitio-react';

const Chatpage = () => {
  const path = useLocation().pathname;
  const chatId = path.split("/").pop();

  const { getToken } = useAuth();

  const { isPending, error, data } = useQuery({
     queryKey: ["chat", chatId],
    queryFn: async () => {
      const token = await getToken(); // get Clerk token

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
          {isPending
            ? "Loading..."
            : error
            ? "Something went wrong!"
            : data?.history?.map((message, i) => (
                <>
                  {message.img && (
                    <IKImage
                      urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
                      path={message.img}
                      height="300"
                      width="400"
                      transformation={[{ height: 300, width: 400 }]}
                      loading="lazy"
                      lqip={{ active: true, quality: 20 }}
                    />
                  )}
                  <div
                    className={
                      message.role === "user" ? "message user" : "message"
                    }
                    key={i}
                  >
                    <Markdown>{message.parts[0].text}</Markdown>
                  </div>
                </>
              ))}

          {data && <NewPrompt data={data}/>}
        </div>
      </div>
    </div>
  );
};

export default Chatpage