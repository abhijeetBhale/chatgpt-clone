import { useEffect, useRef, useState } from "react";
import "./newPrompt.css";
import Upload from "../upload/upload";
import { IKImage } from "imagekitio-react";
import groq, { MODEL } from "../../lib/groq";
import Markdown from "react-markdown";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth, useUser } from "@clerk/clerk-react";

const NewPrompt = ({ data }) => {
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
    endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [data, question, answer, img.dbData, isThinking]);

  const queryClient = useQueryClient();
  const { getToken } = useAuth();

  const mutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/chats/${data._id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: question.length ? question : undefined,
          answer,
          img: img.dbData?.filePath || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to save chat");
      }

      return await res.json();
    },
    onSuccess: () => {
      Promise.all([
        queryClient.invalidateQueries({ queryKey: ["chat", data._id] }),
        queryClient.invalidateQueries({ queryKey: ["userChats"] }),
      ]).then(() => {
          formRef.current.reset();
          setQuestion("");
          setAnswer("");
          setIsThinking(false);
          setImg({
            isLoading: false,
            error: "",
            dbData: {},
            aiData: {},
          });
        });
    },
    onError: (err) => {
      console.log(err);
      setIsThinking(false);
    },
  });

  const add = async (text, isInitial) => {
    if (!isInitial) setQuestion(text);

    setIsThinking(true);

    try {
      const history = data?.history?.slice(0, -1) || [];

      const messages = [
        {
          role: "system",
          content: "You are a helpful AI assistant called Boost AI. Answer concisely and accurately.",
        },
        ...history.map((msg) => ({
          role: msg.role === "model" ? "assistant" : "user",
          content: msg.parts[0].text,
        })),
        { role: "user", content: text },
      ];

      const stream = await groq.chat.completions.create({
        messages,
        model: MODEL,
        stream: true,
      });

      let accumulatedText = "";
      let hasStarted = false;

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || "";

        if (!hasStarted && content) {
          setIsThinking(false);
          hasStarted = true;
        }

        accumulatedText += content;
        setAnswer(accumulatedText);
      }

      if (!hasStarted) {
        setIsThinking(false);
      }

      mutation.mutate();
    } catch (err) {
      console.log(err);
      setIsThinking(false);
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
    if (!hasRun.current) {
      if (
        data?.history?.length === 1 &&
        data.history[0]?.role === "user" &&
        data.history[0]?.parts?.length > 0 &&
        typeof data.history[0].parts[0].text === "string"
      ) {
        add(data.history[0].parts[0].text, true);
      }
      hasRun.current = true;
    }
  }, [data]);

  return (
    <>
      {img.isLoading && <div className="loading">Loading image...</div>}
      {img.dbData?.filePath && (
        <div className="message-wrapper user">
          <div className="message-avatar">
            <img src={userAvatar} alt="You" />
          </div>
          <div className="message-with-image">
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
            <img src={userAvatar} alt="You" />
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
          <input type="text" name="text" placeholder="Ask anything..." />
          <button type="submit" disabled={isThinking}>
            <img src="/arrow.png" alt="" />
          </button>
        </form>
      </div>
    </>
  );
};

export default NewPrompt;
