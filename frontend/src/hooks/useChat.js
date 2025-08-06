import { useState, useCallback, useRef, useEffect } from 'react';
import { sendMessage, getConversation } from '../services/api';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Custom hook for managing chat functionality and conversation state.
 * 
 * This hook handles all the chat stuff - sending messages, loading conversations,
 * and keeping track of what's happening in the chat.
 * 
 * @param {string} conversationId - Current conversation ID
 * @param {Function} onConversationUpdate - Callback when conversation updates
 * @returns {Object} Chat state and functions
 */
export const useChat = (conversationId, onConversationUpdate) => {
  const { addNotification } = useNotification();
  
  // Keep track of what's happening in the chat
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [vacationSummary, setVacationSummary] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Use refs to keep track of things and prevent weird race conditions
  const loadedConversationRef = useRef(null);
  const abortControllerRef = useRef(null);
  const processingConversationRef = useRef(null);

  // The messages we show when someone starts a new chat or comes back
  const getWelcomeMessage = useCallback(() => ({
    role: 'assistant',
    content: "Hello! I'm your vacation planning assistant. Where would you like to go for your next adventure?",
    timestamp: new Date().toISOString()
  }), []);

  const getContinueMessage = useCallback(() => ({
    role: 'assistant',
    content: "Welcome back! Let's continue planning your trip.",
    timestamp: new Date().toISOString()
  }), []);

  // Clear everything and start fresh
  const clearState = useCallback(() => {
    setMessages([]);
    setVacationSummary(null);
    setSuggestions([]);
    setIsLoading(false);
    setIsProcessing(false);
    processingConversationRef.current = null;
  }, []);

  // Clean up when someone deletes a conversation
  const cleanupOnDeletion = useCallback(() => {
    if (isProcessing) {
      setIsProcessing(false);
      processingConversationRef.current = null;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    }
  }, [isProcessing]);

  // Load a conversation by its ID
  const loadConversation = useCallback(async (id) => {
    // Don't load if we're busy processing something else
    if (isProcessing && processingConversationRef.current !== id) {
      return;
    }

    // Don't load the same conversation twice
    if (loadedConversationRef.current === id && id) {
      return;
    }

    // Stop any request that's still running
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear everything and start fresh
    clearState();

    // If there's no ID or it's invalid, show the welcome message
    if (!id || id === 'undefined' || id === 'null') {
      setMessages([getWelcomeMessage()]);
      loadedConversationRef.current = null;
      return;
    }

    abortControllerRef.current = new AbortController();
    setIsLoading(true);
    loadedConversationRef.current = id;

    try {
      const conversation = await getConversation(id, {
        signal: abortControllerRef.current.signal
      });

      // Double-check we're still loading the same conversation
      if (loadedConversationRef.current !== id) {
        return;
      }

      // Set messages
      if (!conversation.messages || conversation.messages.length === 0) {
        setMessages([getContinueMessage()]);
      } else {
        const formattedMessages = conversation.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp || new Date().toISOString()
        }));
        setMessages(formattedMessages);
      }

      // Set vacation preferences
      if (conversation.vacation_preferences && 
          Object.keys(conversation.vacation_preferences).length > 0 &&
          conversation.vacation_preferences.destinations?.length > 0) {
        setVacationSummary({
          destination: conversation.vacation_preferences.destinations[0],
          budget_range: conversation.vacation_preferences.budget_range,
          travel_style: conversation.vacation_preferences.travel_style,
          travel_dates: conversation.vacation_preferences.travel_dates
        });
      }

    } catch (error) {
      if (error.name === 'AbortError') {
        return;
      }

      console.error('Failed to load conversation:', error);
      
      // Only update if we're still trying to load this conversation
      if (loadedConversationRef.current === id) {
        if (error.response?.status === 404) {
          addNotification('Conversation not found. Starting a new chat.', 'info');
          window.location.href = '/chat';
        } else {
          addNotification('Failed to load conversation', 'error');
          setMessages([getWelcomeMessage()]);
        }
      }
    } finally {
      if (loadedConversationRef.current === id) {
        setIsLoading(false);
      }
    }
  }, [clearState, getWelcomeMessage, getContinueMessage, isProcessing]);

  // Send message
  const sendChatMessage = useCallback(async (content) => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Store the conversation ID at the time of sending
    const requestConversationId = conversationId;
    
    const userMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsProcessing(true);
    processingConversationRef.current = requestConversationId;

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await sendMessage(content, requestConversationId, {
        signal: abortControllerRef.current.signal
      });
      
      // Check if conversation has changed since we sent the request
      if (requestConversationId !== conversationId) {
        return;
      }
      
      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Handle new conversation
      if (!requestConversationId && response.conversation_id) {
        loadedConversationRef.current = response.conversation_id;
        onConversationUpdate?.(response.conversation_id);
        // Trigger a refresh of conversations list to show the new conversation
        setTimeout(() => {
          // This will trigger a refresh of the conversations list
          window.dispatchEvent(new CustomEvent('conversation-created', { 
            detail: { conversationId: response.conversation_id } 
          }));
        }, 100);
      }

      // Update vacation summary and suggestions
      if (response.vacation_summary) {
        setVacationSummary(response.vacation_summary);
      }
      if (response.suggestions) {
        setSuggestions(response.suggestions);
      }
    } catch (error) {
      // Don't show error if request was cancelled or conversation changed
      if (error.name === 'AbortError' || error.message.includes('canceled') || requestConversationId !== conversationId) {
        return;
      }
      
      console.error('Error sending message:', error);
      // Ensure error message is a string
      let errorContent = "I'm sorry, I encountered an error. Please try again.";
      if (error.message && typeof error.message === 'string') {
        errorContent = error.message;
      } else if (error.response?.data?.detail) {
        errorContent = String(error.response.data.detail);
      }
      
      const errorMessage = {
        role: 'assistant',
        content: errorContent,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
      addNotification('Failed to send message', 'error');
    } finally {
      // Only clear loading if conversation hasn't changed
      if (requestConversationId === conversationId) {
        setIsLoading(false);
      }
      setIsProcessing(false);
      processingConversationRef.current = null;
      abortControllerRef.current = null;
    }
  }, [conversationId, onConversationUpdate]);

  // Force reload conversation
  const forceReload = useCallback(() => {
    loadedConversationRef.current = null;
    if (conversationId) {
      loadConversation(conversationId);
    }
  }, [conversationId, loadConversation]);

  // Effect to load conversation when ID changes
  useEffect(() => {
    loadedConversationRef.current = null;
    loadConversation(conversationId);

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [conversationId]);

  return {
    messages,
    isLoading,
    isProcessing,
    vacationSummary,
    suggestions,
    setSuggestions,
    sendMessage: sendChatMessage,
    forceReload,
    canSwitchConversation: !isProcessing,
    cleanupOnDeletion
  };
};