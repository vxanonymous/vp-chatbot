import React, { useState, useRef } from 'react';
import { Send } from 'lucide-react';

const MessageInput = ({ onSendMessage, disabled }) => {
  // Keep track of what they're typing
  const [message, setMessage] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Send their message if it's not empty and we're not disabled
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    // Send on Enter, but let them use Shift+Enter for new lines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 p-2 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
      <input
        type="text"
        className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400 dark:focus:ring-primary-700"
        placeholder="Tell me about your dream vacation..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={disabled}
      />
      <button
        type="submit"
        className="px-4 py-2 rounded-lg bg-primary-600 dark:bg-primary-700 text-white hover:bg-primary-700 dark:hover:bg-primary-800 transition disabled:opacity-50"
        disabled={disabled || !message.trim()}
      >
        <Send className="h-5 w-5" />
      </button>
    </form>
  );
};

export default MessageInput;