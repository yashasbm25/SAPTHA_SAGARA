import React, { useRef, useEffect } from 'react';
import { Send, Loader } from 'lucide-react';

interface Message {
  type: 'user' | 'assistant' | 'error';
  content: string;
}

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  loading: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, loading }) => {
  const [input, setInput] = React.useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3 className="text-lg font-bold mb-2">Welcome to SAPTHA SAGARA</h3>
            <p className="text-sm text-gray-600 mb-4">Ask about marine conditions, fishing zones, weather, and safety</p>
            <div className="quick-prompts space-y-2">
              <button 
                onClick={() => setInput('Is it safe to go fishing tomorrow?')}
                className="w-full text-left p-2 hover:bg-gray-100 rounded text-sm"
              >
                • Is it safe to go fishing tomorrow?
              </button>
              <button 
                onClick={() => setInput('Where is the nearest productive fishing zone?')}
                className="w-full text-left p-2 hover:bg-gray-100 rounded text-sm"
              >
                • Where is the nearest productive fishing zone?
              </button>
              <button 
                onClick={() => setInput('Show me current sea conditions')}
                className="w-full text-left p-2 hover:bg-gray-100 rounded text-sm"
              >
                • Show me current sea conditions
              </button>
              <button 
                onClick={() => setInput('Are there any alerts?')}
                className="w-full text-left p-2 hover:bg-gray-100 rounded text-sm"
              >
                • Are there any alerts?
              </button>
            </div>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.type}`}>
            <div className={`message-content ${msg.type === 'user' ? 'user-message' : msg.type === 'error' ? 'error-message' : 'assistant-message'}`}>
              <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message message-loading">
            <div className="message-content assistant-message flex items-center gap-2">
              <Loader className="w-4 h-4 animate-spin" />
              <span className="text-sm">Processing...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about fishing conditions, safety, zones..."
          className="input-field"
          rows={2}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="send-button"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;