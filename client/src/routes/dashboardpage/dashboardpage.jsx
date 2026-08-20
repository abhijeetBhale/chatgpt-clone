import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import './dashboardpage.css';

const DashboardPage = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [inputText, setInputText] = useState("");

  const mutation = useMutation({
    mutationFn: async (text) => {
      const token = await getToken();

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        throw new Error("Failed to create chat");
      }

      return await res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["userChats"] });
      navigate(`/dashboard/chats/${data._id}`);
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    mutation.mutate(inputText);
  };

  const handleOptionClick = (promptText) => {
    setInputText(promptText);
  };

  return (
    <div className="dashboardPage">
      <div className="texts">
        <div className="logoHeader">
          <div className="heroLogoBadge">
            <img src="/logo.png" alt="Boost AI" className="heroLogo" />
          </div>
          <div className="eyebrowMono">// FRONTIER REASONING PIPELINE</div>
          <h1>BOOST AI</h1>
          <p className="heroSubtitle">Engineered for deep reasoning, code generation & multi-modal synthesis.</p>
        </div>

        <div className="options">
          <div 
            className="optionCard"
            onClick={() => handleOptionClick("Create a structured strategy for my project")}
          >
            <div className="optionIcon">💬</div>
            <div className="optionContent">
              <span className="optionTitle">Create a New Chat</span>
              <span className="optionDesc">Start an open-ended reasoning session</span>
            </div>
          </div>

          <div 
            className="optionCard"
            onClick={() => handleOptionClick("Analyze the image and summarize key details")}
          >
            <div className="optionIcon">📷</div>
            <div className="optionContent">
              <span className="optionTitle">Analyze Images</span>
              <span className="optionDesc">Extract data & vision capabilities</span>
            </div>
          </div>

          <div 
            className="optionCard"
            onClick={() => handleOptionClick("Help me refactor and optimize my code")}
          >
            <div className="optionIcon">⚡</div>
            <div className="optionContent">
              <span className="optionTitle">Help with Code</span>
              <span className="optionDesc">Debug, refactor & generate code</span>
            </div>
          </div>
        </div>
      </div>

      <div className="formContainer">
        <form onSubmit={handleSubmit}>
          <input 
            type="text" 
            name="text" 
            placeholder="Ask anything or request code assistance..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={mutation.isPending}
            autoFocus
          />
          <button type="submit" disabled={mutation.isPending || !inputText.trim()}>
            {mutation.isPending ? (
              <span className="buttonSpinner"></span>
            ) : (
              <span className="sendArrow">↑</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default DashboardPage;
