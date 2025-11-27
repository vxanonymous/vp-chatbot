import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import VacationSummary from './VacationSummary';
import { sendMessage } from '../services/api';

/**

 * Chat Interface Component

 * 

 * This is the main chat interface - it handles all the conversation stuff,

 * message sending, and user interactions for planning vacations.

 */


const ChatInterface = () => {

  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [vacationSummary, setVacationSummary] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  
  const messagesEndRef = useRef(null);
  const currentRequestRef = useRef(null);

  const scrollToBottom = () => {

    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {

    scrollToBottom();
  }, [messages]);

  useEffect(() => {

    setMessages([
      {
        role: 'assistant',
        content: "Hello! I'm your vacation planning assistant. I'm here to help you plan your perfect getaway. Tell me about your dream vacation - where would you like to go, when, and what kind of experience are you looking for?",
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  const handleSendMessage = async (message) => {

    if (currentRequestRef.current) {
      currentRequestRef.current.cancel();
    }

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    const requestConversationId = conversationId;

    try {
      console.log('Sending message:', message, 'Conversation ID:', requestConversationId);
      
      const controller = new AbortController();
      currentRequestRef.current = controller;
      
      const response = await sendMessage(message, requestConversationId, {
        signal: controller.signal
      });
      
      console.log('Received response:', response);
      
      if (requestConversationId !== conversationId) {
        console.log('Conversation changed during request, ignoring response');
        return;
      }
      
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (response.vacation_summary) {
        setVacationSummary(response.vacation_summary);
      }
      if (response.suggestions) {
        setSuggestions(response.suggestions);
      }
    } catch (error) {
      if (error.name === 'AbortError' || error.message.includes('canceled')) {
        console.log('Request was cancelled');
        return;
      }
      
      console.error('Error sending message:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data
      });
      
      if (requestConversationId === conversationId) {
        const errorMessage = {
          role: 'assistant',
          content: `I'm sorry, I encountered an error: ${error.message}. Please try again.`,
          timestamp: new Date().toISOString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      if (requestConversationId === conversationId) {
        setIsLoading(false);
      }
      currentRequestRef.current = null;
    }
  };

  const handleSuggestionClick = (suggestion) => {

    handleSendMessage(suggestion);
  };

  useEffect(() => {
    return () => {

      if (currentRequestRef.current) {
        currentRequestRef.current.cancel();
      }
    };
  }, []);

  return (
    <div className="chat-interface min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900 dark:text-gray-100">
      <div className="chat-container flex-1 flex flex-col md:flex-row">
        <div className="messages-section flex-1">
          <MessageList messages={messages} isLoading={isLoading} />
          <div ref={messagesEndRef} />
        </div>
        {vacationSummary && (
          <div className="summary-section bg-gray-100 dark:bg-gray-800 p-4 rounded-lg shadow-md">
            <VacationSummary summary={vacationSummary} />
          </div>
        )}
      </div>
      
      {suggestions.length > 0 && (
        <div className="suggestions bg-gray-100 dark:bg-gray-800 p-2 rounded-lg mt-2">
          <p>Suggestions:</p>
          <div className="suggestion-chips flex flex-wrap gap-2 mt-1">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-chip bg-primary-100 dark:bg-primary-800 text-primary-800 dark:text-primary-100 px-3 py-1 rounded-full hover:bg-primary-200 dark:hover:bg-primary-700 transition"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  );
};

export default ChatInterface;
