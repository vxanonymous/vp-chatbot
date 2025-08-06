import React, { useState } from 'react';
import MessageList from './components/MessageList';

const ChatPage = () => {
  const [messages, setMessages] = useState([
    // Example system message
    // { role: 'system', content: 'New conversation created', timestamp: Date.now() }
  ]);

  const handleDismissSystemMessage = (index) => {
    setMessages((msgs) => msgs.filter((msg, i) => i !== index));
  };

  return (
    <MessageList
      messages={messages}
      isLoading={isLoading}
      onDismissSystemMessage={handleDismissSystemMessage}
    />
  );
}; 