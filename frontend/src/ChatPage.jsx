import React, { useState } from 'react';
import MessageList from './components/MessageList';

const ChatPage = () => {

  const [messages, setMessages] = useState([


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