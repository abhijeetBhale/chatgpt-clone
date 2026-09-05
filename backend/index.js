import express from "express";
import ImageKit from "imagekit";
import cors from "cors";
import dotenv from "dotenv";
import mongoose from "mongoose";
import Groq from "groq-sdk";
import Chat from "./models/chat.js";
import UserChats from "./models/userChats.js";
import { ClerkExpressRequireAuth } from "@clerk/clerk-sdk-node";

// Load environment variables first
dotenv.config();

// Configure Clerk with secret key
const CLERK_SECRET_KEY = process.env.CLERK_SECRET_KEY;
if (!CLERK_SECRET_KEY) {
  console.error("Missing CLERK_SECRET_KEY environment variable");
  process.exit(1);
}

const GROQ_API_KEY = process.env.GROQ_API_KEY;
if (!GROQ_API_KEY) {
  console.warn("Warning: Missing GROQ_API_KEY environment variable");
}

const groq = new Groq({
  apiKey: GROQ_API_KEY || "",
});
const MODEL = "qwen/qwen3.6-27b";

const VISION_MODELS = new Set([
  "qwen/qwen3.6-27b",
  "qwen/qwen3.8-27b",
  "llama-3.2-90b-vision-preview",
  "llama-3.2-11b-vision-preview",
]);

const port = process.env.PORT || 3000;
const app = express();

app.use(
  cors({
    origin: [
      process.env.CLIENT_URL, 
      "http://localhost:5173", 
      "https://chatgpt-clone-production.up.railway.app",
      "https://boost-ai-chat.vercel.app"
    ],
    credentials: true, 
  })
);

app.use(express.json());

// Health check route
app.get("/", (req, res) => {
  res.json({ 
    message: "Boost AI Backend Engine is running!", 
    status: "healthy",
    timestamp: new Date().toISOString()
  });
});

const connect = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URL);
    console.log("Connected to MongoDB");
  } catch (err) {
    console.log("MongoDB connection error:", err);
  }
};

const imagekit = new ImageKit({
  publicKey: process.env.IMAGEKIT_URL_PUBLIC_KEY,
  privateKey: process.env.IMAGEKIT_URL_PRIVATE_KEY,
  urlEndpoint: process.env.IMAGEKIT_URL_ENDPOINT,
});

// Helper: fetch an image from ImageKit and return base64 data URL
const fetchImageAsBase64 = async (filePath) => {
  try {
    const url = `${process.env.IMAGEKIT_URL_ENDPOINT}${filePath}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Failed to fetch image: ${response.status}`);
    const buffer = await response.arrayBuffer();
    const base64 = Buffer.from(buffer).toString("base64");
    const contentType = response.headers.get("content-type") || "image/jpeg";
    return `data:${contentType};base64,${base64}`;
  } catch (err) {
    console.error("Error fetching image as base64:", err);
    return null;
  }
};

app.get("/api/upload", (req, res) => {
  const result = imagekit.getAuthenticationParameters();
  res.send(result);
});

// Helper to safely find chat by ID without casting errors
const findChatSafely = async (id, userId) => {
  try {
    if (!mongoose.Types.ObjectId.isValid(id)) {
      return null;
    }
    let chat = await Chat.findOne({ _id: id, userId });
    return chat;
  } catch (err) {
    console.error("findChatSafely error:", err);
    return null;
  }
};

// CREATE A NEW CHAT
app.post("/api/chats", ClerkExpressRequireAuth(), async (req, res) => {
  const userId = req.auth.userId;
  const { text } = req.body;

  try {
    const newChat = new Chat({
      userId: userId,
      history: [{ role: "user", parts: [{ text: text || "New Chat" }] }],
    });

    const savedChat = await newChat.save();

    const userChats = await UserChats.find({ userId: userId });

    if (!userChats.length) {
      const newUserChats = new UserChats({
        userId: userId,
        chats: [
          {
            _id: savedChat._id.toString(),
            title: (text || "New Chat").substring(0, 40),
          },
        ],
      });

      await newUserChats.save();
    } else {
      await UserChats.updateOne(
        { userId: userId },
        {
          $push: {
            chats: {
              _id: savedChat._id.toString(),
              title: (text || "New Chat").substring(0, 40),
            },
          },
        }
      );
    }

    res.status(201).json({ _id: savedChat._id.toString() });
  } catch (err) {
    console.error("Error creating chat:", err);
    res.status(500).send("Error creating chat!");
  }
});

// GET ALL CHATS FOR USER
app.get("/api/userchats", ClerkExpressRequireAuth(), async (req, res) => {
  const userId = req.auth.userId;

  try {
    const userChats = await UserChats.find({ userId });
    res.status(200).json(userChats[0]?.chats || []);
  } catch (err) {
    console.error("Error fetching userchats:", err);
    res.status(500).send("Error fetching userchats!");
  }
});

// GET SINGLE CHAT BY ID
app.get("/api/chats/:id", ClerkExpressRequireAuth(), async (req, res) => {
  const userId = req.auth.userId;

  try {
    let chat = await findChatSafely(req.params.id, userId);
    
    if (!chat) {
      // Auto-create chat if not found so route never fails with 404
      const newChatData = {
        userId,
        history: [],
      };
      if (mongoose.Types.ObjectId.isValid(req.params.id)) {
        newChatData._id = req.params.id;
      }
      chat = new Chat(newChatData);
      await chat.save();
    }

    res.status(200).json(chat);
  } catch (err) {
    console.error("Error fetching chat:", err);
    res.status(500).send("Error fetching chat!");
  }
});

// BACKEND-CENTRIC STREAMING & MESSAGE COMPLETION ENDPOINT
app.post("/api/chats/:id/message", ClerkExpressRequireAuth(), async (req, res) => {
  const userId = req.auth.userId;
  const { question, img } = req.body;

  try {
    let chat = await findChatSafely(req.params.id, userId);

    if (!chat) {
      // Auto-create chat document if not found
      const newChatData = {
        userId,
        history: [],
      };
      if (mongoose.Types.ObjectId.isValid(req.params.id)) {
        newChatData._id = req.params.id;
      }
      chat = new Chat(newChatData);
      await chat.save();

      // Ensure userchats entry exists
      await UserChats.updateOne(
        { userId },
        {
          $push: {
            chats: {
              _id: chat._id.toString(),
              title: (question || "New Chat").substring(0, 40),
            },
          },
        },
        { upsert: true }
      );
    }

    // Append user question if provided
    if (question) {
      const userItem = { role: "user", parts: [{ text: question }], ...(img && { img }) };
      chat.history.push(userItem);
      await Chat.updateOne(
        { _id: chat._id },
        { $push: { history: userItem } }
      );
    }

    // Build message context payload for Groq LLM
    const systemPrompt = {
      role: "system",
      content: `You are Boost AI, a high-performance frontier AI assistant. 

Key formatting rules:
- Use markdown for all responses
- For tables: Always provide complete data, never leave empty placeholder rows
- Keep responses conversational and helpful
- Use proper markdown headers, lists, and tables when appropriate
- If you don't know real-time data, provide general knowledge or examples with clear labels
- Format tables with clear headers and complete sample data
- When a user shares an image, describe and analyze it in detail`,
    };

    const supportsVision = VISION_MODELS.has(MODEL);

    // Build conversation history — include images for vision-capable models
    const conversationHistory = [];
    for (const msg of chat.history) {
      const role = msg.role === "model" ? "assistant" : "user";
      const textContent = msg.parts[0]?.text || "";

      if (msg.img && supportsVision) {
        const imageDataUrl = await fetchImageAsBase64(msg.img);
        if (imageDataUrl) {
          conversationHistory.push({
            role,
            content: [
              { type: "text", text: textContent },
              { type: "image_url", image_url: { url: imageDataUrl } },
            ],
          });
        } else {
          // Fallback: send text only if image fetch fails
          conversationHistory.push({ role, content: textContent });
        }
      } else {
        conversationHistory.push({ role, content: textContent });
      }
    }

    const messages = [systemPrompt, ...conversationHistory];

    // Set Server-Sent Events (SSE) streaming headers
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders?.();

    // Call Groq LLM stream on backend
    const stream = await groq.chat.completions.create({
      messages,
      model: MODEL,
      stream: true,
    });

    let accumulatedAnswer = "";

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || "";
      if (content) {
        accumulatedAnswer += content;
        res.write(`data: ${JSON.stringify({ content })}\n\n`);
      }
    }

    // Save final AI response to MongoDB chat history
    if (accumulatedAnswer) {
      const aiItem = { role: "model", parts: [{ text: accumulatedAnswer }] };
      await Chat.updateOne(
        { _id: chat._id },
        { $push: { history: aiItem } }
      );
    }

    res.write("data: [DONE]\n\n");
    res.end();
  } catch (err) {
    console.error("Error streaming AI response:", err);
    const errorMessage = "Sorry, I encountered an error generating a response. Please try again.";
    if (!res.headersSent) {
      res.status(500).send("Error streaming AI response!");
    } else {
      res.write(`data: ${JSON.stringify({ content: errorMessage })}\n\n`);
      res.write("data: [DONE]\n\n");
      res.end();
    }
    // Save error to chat history so it's not left incomplete
    try {
      const errorItem = { role: "model", parts: [{ text: errorMessage }] };
      await Chat.updateOne(
        { _id: req.params.id },
        { $push: { history: errorItem } }
      );
    } catch (saveErr) {
      console.error("Failed to save error to chat history:", saveErr);
    }
  }
});

// LEGACY UPDATE ROUTE
app.put("/api/chats/:id", ClerkExpressRequireAuth(), async (req, res) => {
  const userId = req.auth.userId;
  const { question, answer, img } = req.body;

  const newItems = [
    ...(question ? [{ role: "user", parts: [{ text: question }], ...(img && { img }) }] : []),
    { role: "model", parts: [{ text: answer }] },
  ];

  try {
    const updatedChat = await Chat.updateOne(
      { _id: req.params.id, userId },
      { $push: { history: { $each: newItems } } }
    );
    res.status(200).json(updatedChat);
  } catch (err) {
    console.error("Error updating conversation:", err);
    res.status(500).send("Error adding conversation!");
  }
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(401).send("Unauthorized!");
});

app.listen(port, () => {
  connect();
  console.log(`Boost AI Backend Engine is running on port ${port}`);
});
