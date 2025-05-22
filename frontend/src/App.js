import React, { useState } from 'react';
import { 
  ChatBubbleOvalLeftEllipsisIcon, 
  PaperAirplaneIcon, 
  ChevronDownIcon,
  XMarkIcon 
} from '@heroicons/react/24/solid';

function App() {
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Hello, I'm your personal MadeWithNestle.ca AI assistant! Ask me anything, and I'll search the entire site to find the answers you need!" }
  ]);
  const [input, setInput] = useState('');

  const sendMessage = () => {
    if (!input.trim()) return;
    setMessages([...messages, { role: 'user', content: input }]);
    setInput('');
  };

  const handleClose = () => {
    setShowChat(false);
    setMessages([
      {
        role: 'bot',
        content:
          "Hello, I'm your personal MadeWithNestle.ca AI assistant! Ask me anything, and I'll search the entire site to find the answers you need!"
      }
    ]);
  };

  return (
    <div
      className="App min-h-screen bg-cover bg-center text-white relative"
      style={{ backgroundImage: "url('/madewithnestle.png')" }}
    >
      {/* Chatbot Toggle Button */}
      <button
        onClick={() => setShowChat(!showChat)}
        className="fixed bottom-6 right-6 bg-blue-600 p-4 rounded-full shadow-lg transition-transform hover:scale-110"
      >
        <ChatBubbleOvalLeftEllipsisIcon className="text-white h-6 w-6" />
      </button>

      {/* Chatbox UI */}
      {showChat && (
        <div className="fixed bottom-20 right-6 w-96 h-[34rem] bg-white text-black rounded-xl shadow-xl flex flex-col transition-all duration-300">
          <div className="flex justify-between items-center font-semibold text-lg bg-blue-800 p-4 text-white">
            <span className="font-semibold text-lg">Nestlé Chatbot</span>
            <div className="flex gap-2">
              <button onClick={() => setShowChat(false)}>
                <ChevronDownIcon className="h-5 w-5 text-white hover:text-gray-200" />
              </button>
              <button onClick={handleClose}>
                <XMarkIcon className="h-5 w-5 text-white hover:text-gray-200" />
              </button>
            </div>
          </div>

          {/* Message history */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 m-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'bot' ? 'justify-start' : 'justify-end'}`}
            >
              <div
                className={`max-w-[80%] text-sm px-3 py-2 rounded-lg ${
                  msg.role === 'bot'
                    ? 'bg-blue-100 text-blue-900'
                    : 'bg-gray-100 text-black'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
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
            />
            <button
              onClick={sendMessage}
              className="bg-blue-600 text-white px-3 py-2 rounded-full hover:bg-blue-700 text-sm"
            >
              <PaperAirplaneIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
