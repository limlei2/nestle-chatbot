import React, { useState } from 'react';
import { ChatBubbleOvalLeftEllipsisIcon } from '@heroicons/react/24/solid';

function App() {
  const [showChat, setShowChat] = useState(false);
  return (
    <div
      className="App min-h-screen bg-cover bg-center text-white relative"
      style={{ backgroundImage: "url('/madewithnestle.png')" }}
    >
      {/* Chatbot Toggle Button */}
      <button
        onClick={() => setShowChat(!showChat)}
        className="fixed bottom-6 right-6 bg-blue-600 p-4 rounded-full shadow-lg hover:bg-blue-700 transition"
      >
        <ChatBubbleOvalLeftEllipsisIcon className="text-white h-6 w-6" />
      </button>

      {/* Chatbox UI */}
      {showChat && (
        <div className="fixed bottom-20 right-6 w-80 h-96 bg-white text-black rounded-xl shadow-xl p-4 flex flex-col">
          <div className="font-semibold text-lg mb-2">Nestlé Chatbot</div>
          <div className="flex-1 overflow-y-auto border p-2 rounded mb-2 text-sm">
            <p>Hello! How can I help you today?</p>
          </div>
          <input
            type="text"
            className="border rounded p-2 text-sm"
            placeholder="Type your message..."
          />
        </div>
      )}
    </div>
  );
}

export default App;
