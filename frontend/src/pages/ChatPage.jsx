import React, { useState, useEffect, useCallback, memo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Menu } from 'lucide-react';
import ConversationSidebar from '../components/ConversationSidebar';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import VacationSummary from '../components/VacationSummary';
import { useConversations } from '../hooks/useConversations';
import { useChat } from '../hooks/useChat';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import ErrorBoundary from '../components/ErrorBoundary';

// Memoized components for better performance
const MobileHeader = memo(({ onMenuClick }) => (
  <div className="md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center">
    <button
      onClick={onMenuClick}
      className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
      aria-label="Open menu"
    >
      <Menu className="h-6 w-6" />
    </button>
    <h1 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">Vacation Planner</h1>
  </div>
));

const SuggestionsList = memo(({ suggestions = [], onSuggestionClick }) => {
  if (!suggestions || suggestions.length === 0) return null;
  
  return (
    <div className="px-4 pb-4">
      <div className="max-w-3xl mx-auto">
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion, index) => (
            <button
              key={`${suggestion}-${index}`}
              className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-800 dark:text-gray-200"
              onClick={() => onSuggestionClick(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
});

const ChatPage = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  
  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // System message dismiss logic
  const [localMessages, setLocalMessages] = useState([]);
  const [hasShownWelcome, setHasShownWelcome] = useState(false);

  // Custom hooks
  const { user } = useAuth();
  const {
    conversations,
    isLoading: isConversationsLoading,
    createNewConversation,
    updateConversationTitle,
    removeConversation,
    touchConversation,
    loadConversations
  } = useConversations();
  
  const { addGlobalNotification, addInlineNotification } = useNotification();
  
  const handleConversationUpdate = useCallback((newConversationId) => {
    navigate(`/chat/${newConversationId}`, { replace: true });
    // Add a small delay to ensure the conversation is fully created before loading
    setTimeout(() => {
      loadConversations();
    }, 500);
  }, [navigate, loadConversations]);
  
  const {
    messages,
    isLoading: isChatLoading,
    isProcessing,
    vacationSummary,
    suggestions,
    setSuggestions,
    sendMessage,
    forceReload,
    canSwitchConversation,
    cleanupOnDeletion
  } = useChat(conversationId, handleConversationUpdate);

  // Merge messages from chat and local system messages
  const allMessages = [...localMessages, ...messages];

  // Handler to dismiss system messages
  const handleDismissSystemMessage = useCallback((index) => {
    // Since system messages are only in localMessages, we can filter directly
    setLocalMessages((msgs) => msgs.filter((msg, i) => i !== index));
  }, []);

  // Add welcome message for new conversations
  useEffect(() => {
    if (messages.length === 0 && localMessages.length === 0 && !hasShownWelcome && user) {
      const name = user.full_name || user.email;
      // Add inline notification instead of system message
      addInlineNotification(`Welcome back, ${name}! I'm here to help you plan your perfect trip. Ask me about destinations, itineraries, budgets, or anything travel-related!`, 'info');
      setHasShownWelcome(true);
    }
  }, [messages.length, localMessages.length, hasShownWelcome, user, addInlineNotification]);



  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Event handlers
  const handleNewConversation = useCallback(async () => {
    try {
      const newConv = await createNewConversation();
      if (newConv) {
        navigate(`/chat/${newConv.id}`);
        // Add inline notification instead of system message
        addInlineNotification('New conversation created! I\'m ready to help you plan your vacation. What would you like to know?', 'success');
        addGlobalNotification('New conversation created', 'success');
      }
    } catch (error) {
      addGlobalNotification('Failed to create new conversation', 'error');
    }
  }, [createNewConversation, navigate, addGlobalNotification, addInlineNotification]);

  const handleDeleteConversation = useCallback(async (id) => {
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
      const deleted = await removeConversation(id);
      if (deleted && conversationId === id) {
        // Add inline notification instead of system message
        addInlineNotification('Conversation deleted successfully.', 'info');
        // Cleanup if we're deleting the current conversation
        cleanupOnDeletion();
        navigate('/chat');
        addGlobalNotification('Conversation deleted', 'success');
      }
    } catch (error) {
      addGlobalNotification('Failed to delete conversation', 'error');
    }
  }, [removeConversation, conversationId, navigate, cleanupOnDeletion, addGlobalNotification, addInlineNotification]);

  const handleUpdateConversationTitle = useCallback(async (id, newTitle) => {
    try {
      await updateConversationTitle(id, newTitle);
    } catch (error) {
      addGlobalNotification('Failed to update conversation title', 'error');
    }
  }, [updateConversationTitle, addGlobalNotification]);

  const handleSendMessage = useCallback((content) => {
    sendMessage(content);
    // Update conversation timestamp after sending
    if (conversationId) {
      setTimeout(() => touchConversation(conversationId), 100);
    }
    // Add a system message for the first message in a conversation
    if (messages.length === 0 && localMessages.length === 1) {
      setLocalMessages(prev => [...prev, { 
        role: 'system', 
        content: 'Great! I\'m processing your request. Feel free to ask me anything about vacation planning!', 
        timestamp: Date.now() 
      }]);
    }
  }, [sendMessage, conversationId, touchConversation, messages.length, localMessages.length]);

  const handleSuggestionClick = useCallback((suggestion) => {
    handleSendMessage(suggestion);
    setSuggestions([]);
  }, [handleSendMessage, setSuggestions]);

  const handleSidebarToggle = useCallback(() => {
    setSidebarOpen(prev => !prev);
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const scrollToBottom = () => {
      const element = document.getElementById('messages-end');
      element?.scrollIntoView({ behavior: 'smooth' });
    };
    
    const timer = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timer);
  }, [messages]);

  return (
    <ErrorBoundary>
      <div className="flex h-screen min-h-screen w-full bg-gray-50 dark:bg-gray-900">
        {/* Processing overlay */}
        {isProcessing && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 shadow-lg">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                <span className="text-lg font-medium">Processing your request...</span>
              </div>
              <p className="text-gray-600 mt-2 text-center">Please wait while I think about your question.</p>
            </div>
          </div>
        )}
        
        <ConversationSidebar
          isOpen={sidebarOpen}
          onToggle={handleSidebarToggle}
          conversations={conversations}
          isLoading={isConversationsLoading}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onUpdateConversation={handleUpdateConversationTitle}
          selectedConversationId={conversationId}
          disabled={isProcessing} // Disable during processing
        />
        
        <div className="flex-1 flex flex-col">
          <MobileHeader onMenuClick={handleSidebarToggle} />
          
          <div className="flex-1 flex overflow-hidden">
            <div className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="max-w-3xl mx-auto">
                  <MessageList messages={allMessages} isLoading={isChatLoading} onDismissSystemMessage={handleDismissSystemMessage} />
                  <div id="messages-end" />
                </div>
              </div>
              
              <SuggestionsList 
                suggestions={suggestions} 
                onSuggestionClick={handleSuggestionClick} 
              />
              
              <div className="border-t bg-white dark:bg-gray-900 px-4 py-4">
                <div className="max-w-3xl mx-auto">
                  <MessageInput 
                    onSendMessage={handleSendMessage} 
                    disabled={isChatLoading} 
                  />
                </div>
              </div>
            </div>
            
            {vacationSummary && (
              <div className="hidden lg:block w-80 border-l bg-white dark:bg-gray-900 p-6 overflow-y-auto">
                <VacationSummary summary={vacationSummary} />
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default memo(ChatPage);