import { useEffect, useRef, useState } from "react";
import "./newPrompt.css";
import Upload from "../upload/upload";
import { IKImage } from "imagekitio-react";
import Markdown from "react-markdown";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth, useUser } from "@clerk/clerk-react";

const NewPrompt = ({ data, onMessagesChange }) => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [img, setImg] = useState({
    isLoading: false,
    error: "",
    dbData: {},
    aiData: {},
  });

  const endRef = useRef(null);
  const formRef = useRef(null);

  const { user } = useUser();
  const userAvatar = user?.imageUrl;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data, question, answer, img.dbData, isThinking]);

  const queryClient = useQueryClient();
  const { getToken } = useAuth();

  const add = async (text, isInitial) => {
    if (!isInitial) setQuestion(text);
    setIsThinking(true);
    setAnswer("");

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
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const text = e.target.text.value;
    if (!text) return;

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

  return (
    <>
      {img.isLoading && <div className="loadingImage">Uploading asset...</div>}
      {img.dbData?.filePath && (
        <div className="message-wrapper user">
          <div className="message-avatar">
            <img src={userAvatar || "/human1.jpeg"} alt="You" />
          </div>
          <div className="messageImageContainer">
            <IKImage
              urlEndpoint={import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT}
              path={img.dbData?.filePath}
              width="380"
              transformation={[{ width: 380 }]}
            />
          </div>
        </div>
      )}

      {question && (
        <div className="message-wrapper user">
          <div className="message-avatar">
            <img src={userAvatar || "/human1.jpeg"} alt="You" />
          </div>
          <div className="message">{question}</div>
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

      {answer && (
        <div className="message-wrapper ai">
          <div className="message-avatar">
            <img src="/logo.png" alt="Boost AI" />
          </div>
          <div className="message">
            <Markdown>{answer}</Markdown>
          </div>
        </div>
      )}

      <div className="endChat" ref={endRef}></div>

      <div className="newForm">
        <form onSubmit={handleSubmit} ref={formRef}>
          <Upload setImg={setImg} />
          <input id="file" type="file" multiple={false} hidden />
          <input type="text" name="text" placeholder="Ask anything or request assistance..." autoFocus />
          <button type="submit" disabled={isThinking} aria-label="Send message">
            <span className="sendIcon">↑</span>
          </button>
        </form>
      </div>
    </>
  );
};

export default NewPrompt;
