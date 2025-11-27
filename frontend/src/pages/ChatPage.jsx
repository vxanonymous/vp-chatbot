import React, { useState, useEffect, useCallback, memo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Menu, X, Map } from 'lucide-react';
import ConversationSidebar from '../components/ConversationSidebar';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import VacationSummary from '../components/VacationSummary';
import VacationMap from '../components/VacationMap';
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
  

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mapSidebarOpen, setMapSidebarOpen] = useState(false);

  const [localMessages, setLocalMessages] = useState([]);
  const [hasShownWelcome, setHasShownWelcome] = useState(false);


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


  useEffect(() => {

      if (messages.length === 0 && localMessages.length === 0 && !hasShownWelcome && user) {
      const name = user.full_name || user.email;

      addInlineNotification(`Welcome back, ${name}! I'm here to help you plan your perfect trip. Ask me about destinations, itineraries, budgets, or anything travel-related!`, 'info');
      setHasShownWelcome(true);
    }
  }, [messages.length, localMessages.length, hasShownWelcome, user, addInlineNotification]);




  useEffect(() => {

    loadConversations();
  }, [loadConversations]);


  const handleNewConversation = useCallback(async () => {
    try {
      const newConv = await createNewConversation();
      if (newConv) {
        navigate(`/chat/${newConv.id}`);

        addGlobalNotification('New conversation created! I\'m ready to help you plan your vacation.', 'success');
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

        addInlineNotification('Conversation deleted successfully.', 'info');

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

    if (conversationId) {
      setTimeout(() => touchConversation(conversationId), 100);

    }

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

  const handleMapSidebarToggle = useCallback(() => {
    setMapSidebarOpen(prev => !prev);
  }, []);

  // Open map sidebar automatically when a new summary with destinations arrives
  useEffect(() => {
    console.log('Vacation summary useEffect triggered. vacationSummary:', vacationSummary);
    if (vacationSummary) {
      const hasDestinations = vacationSummary.destinations?.length > 0 || vacationSummary.destination;
      console.log('Vacation summary check:', {
        vacationSummary,
        hasDestinations,
        destinations: vacationSummary.destinations,
        destination: vacationSummary.destination,
        destinationsLength: vacationSummary.destinations?.length,
        hasDestination: !!vacationSummary.destination
      });
      if (hasDestinations) {
        console.log('Opening map sidebar with vacation summary:', vacationSummary);
        setMapSidebarOpen(true);
      } else {
        console.warn('Vacation summary exists but has no destinations');
      }
    } else {
      console.log('No vacation summary available');
    }
  }, [vacationSummary]);

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
            <div className={`flex-1 flex flex-col transition-all duration-300 ${mapSidebarOpen ? 'lg:mr-96' : ''}`}>
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
          </div>
          
          {/* Map Sidebar - Outside the flex container */}
          {vacationSummary && (vacationSummary.destinations?.length > 0 || vacationSummary.destination) && (
            <>
              {/* Toggle button - always visible when map is available */}
              <button
                onClick={handleMapSidebarToggle}
                className={`fixed bottom-24 right-6 z-40 px-4 py-3 rounded-full shadow-xl bg-primary-600 text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-400 flex items-center gap-2 transition-all ${mapSidebarOpen ? 'lg:right-[400px]' : ''}`}
              >
                <Map className="h-5 w-5" />
                <span className="hidden sm:inline">{mapSidebarOpen ? 'Hide' : 'Show'} Map</span>
              </button>

              {/* Desktop: Right sidebar */}
              <div className={`hidden lg:block fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 shadow-xl transition-transform duration-300 z-30 ${mapSidebarOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                <div className="h-full flex flex-col">
                  <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4 py-3">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      <Map className="h-5 w-5" />
                      Trip Map
                    </h2>
                    <button
                      onClick={handleMapSidebarToggle}
                      className="text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 p-1"
                      aria-label="Close map"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto">
                    <div className="p-4">
                      <VacationSummary summary={vacationSummary} />
                    </div>
                    
                    <div className="px-4 pb-4">
                      <VacationMap
                        destinations={vacationSummary.destinations || (vacationSummary.destination ? [vacationSummary.destination] : [])}
                        itinerary={vacationSummary.itinerary || []}
                        route={vacationSummary.route || []}
                        height="500px"
                        className="rounded-lg overflow-hidden"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Mobile: Full screen drawer */}
              {mapSidebarOpen && (
                <div className="lg:hidden fixed inset-0 z-50 bg-white dark:bg-gray-900">
                  <div className="h-full flex flex-col">
                    <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4 py-3">
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        <Map className="h-5 w-5" />
                        Trip Map
                      </h2>
                      <button
                        onClick={handleMapSidebarToggle}
                        className="text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 p-1"
                        aria-label="Close map"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto">
                      <div className="p-4">
                        <VacationSummary summary={vacationSummary} />
                      </div>
                      
                      <div className="px-4 pb-4">
                        <VacationMap
                          destinations={vacationSummary.destinations || (vacationSummary.destination ? [vacationSummary.destination] : [])}
                          itinerary={vacationSummary.itinerary || []}
                          route={vacationSummary.route || []}
                          height="400px"
                          className="rounded-lg overflow-hidden"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

    </ErrorBoundary>
  );
};

export default memo(ChatPage);