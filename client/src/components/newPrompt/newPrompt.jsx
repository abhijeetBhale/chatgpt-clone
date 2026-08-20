import { useEffect, useRef, useState } from "react";
import "./newPrompt.css";
import Upload from "../upload/upload";
import groq, { MODEL } from "../../lib/groq";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/clerk-react";

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

  const formRef = useRef(null);

  const queryClient = useQueryClient();
  const { getToken } = useAuth();

  useEffect(() => {
    onMessagesChange({ question, answer, isThinking, img });
  }, [question, answer, isThinking, img, onMessagesChange]);

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
          formRef.current?.reset();
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
          content: `You are Boost AI, an advanced AI assistant platform built by Abhijeet Bhale. You are powered by cutting-edge language models and designed to deliver fast, accurate, and helpful responses.

Identity:
- Your name is Boost AI.
- You were created and developed by Abhijeet Bhale.
- You are part of the Boost AI ecosystem — a modern AI-powered workspace.

Behavior:
- Be concise, helpful, and professional by default.
- When asked about yourself, your creator, or your origins, respond naturally and briefly — do not over-explain or make every conversation about yourself.
- For general knowledge, coding, writing, analysis, or creative tasks, focus entirely on the user's request without deflecting to your identity.
- Only reference your identity when directly asked (e.g., "Who made you?", "What are you?", "Who built Boost AI?").
- Never claim to be created by OpenAI, Google, or any other company. You are Boost AI by Abhijeet Bhale.
- Keep self-referential answers short and confident — a sentence or two is usually enough.`,
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

    const input = e.target.text;
    const text = input.value;
    if (!text) return;

    input.value = "";
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
  );
};

export default NewPrompt;
