import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  ChatBubbleOvalLeftEllipsisIcon, 
  PaperAirplaneIcon, 
  XMarkIcon 
} from '@heroicons/react/24/solid';
import { AnimatePresence, motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

function App() {
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Hello, I'm your personal MadeWithNestle.ca AI assistant! Ask me anything, and I'll search the entire site to find the answers you need!" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const messageEndRef = useRef(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const userInput = input.trim();
    if (!userInput) return;
    setMessages((prev) => [...prev, { role: 'user', content: userInput }]);
    setInput('');
    setLoading(true);
    setMessages((prev) => [...prev, { role: 'bot', content: '...' }]);

    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/chat`, {
        message: userInput,
      });
      console.log(response.data);
      const backendResponse = response.data.response || 'Sorry, something went wrong.';
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: 'bot', content: backendResponse },
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: 'bot', content: 'There was an error processing your request.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="App min-h-screen bg-cover bg-center text-white relative"
      style={{ backgroundImage: "url('/madewithnestle.png')" }}
    >
      {/* Chatbot Toggle Button */}
      <button
        onClick={() => setShowChat(!showChat)}
        className="fixed bottom-6 right-6 bg-blue-600 p-3 rounded-full shadow-lg transition-transform hover:scale-125"
      >
        <AnimatePresence mode="wait">
          {showChat ? (
            <motion.div
              key="x-icon"
              initial={{ rotate: 0, opacity: 0 }}
              animate={{ rotate: 180, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <XMarkIcon className="h-8 w-8 text-white" />
            </motion.div>
          ) : (
            <motion.div
              key="chat-icon"
              initial={{ rotate: 180, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ChatBubbleOvalLeftEllipsisIcon className="h-8 w-8 text-white" />
            </motion.div>
          )}
        </AnimatePresence>
      </button>

      {/* Chatbox UI */}
      <AnimatePresence>
        {showChat && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.25 }}
            className="fixed bottom-24 right-6 w-96 h-[34rem] bg-white text-black rounded-2xl shadow-2xl flex flex-col z-40"
          >
          {/* Header */}
            <div className="bg-blue-700 text-white px-4 py-3 rounded-t-2xl font-semibold text-base">
              Nestlé Chatbot
            </div>

            {/* Message history */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 m-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'bot' ? 'justify-start' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-[80%] text-xs px-3 py-2 rounded-lg whitespace-pre-wrap break-words ${
                      msg.role === 'bot'
                        ? 'bg-blue-100 text-blue-900'
                        : 'bg-gray-100 text-black'
                    }`}
                  >
                    <ReactMarkdown>
                      {typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}
                    </ReactMarkdown>
                  </div>
                </div>
                
              ))}
              <div ref={messageEndRef} />
            </div>

            {/* Input */}
            <div className="mt-2 flex gap-2 p-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                className="flex-1 border rounded p-2 text-sm"
                placeholder="Ask me anything!"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                className="bg-blue-600 text-white px-3 py-2 rounded-full hover:bg-blue-700 text-sm"
              >
                <PaperAirplaneIcon className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
