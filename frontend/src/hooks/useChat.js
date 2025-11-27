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
  
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [vacationSummary, setVacationSummary] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const loadedConversationRef = useRef(null);
  const abortControllerRef = useRef(null);
  const processingConversationRef = useRef(null);

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

  const clearState = useCallback((clearVacationSummary = true) => {
    setMessages([]);
    if (clearVacationSummary) {
      setVacationSummary(null);
    }
    setSuggestions([]);
    setIsLoading(false);
    setIsProcessing(false);
    processingConversationRef.current = null;
  }, []);

  const cleanupOnDeletion = useCallback(() => {
    if (isProcessing) {
      setIsProcessing(false);
      processingConversationRef.current = null;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    }
  }, [isProcessing]);

  const loadConversation = useCallback(async (id) => {
    if (isProcessing && processingConversationRef.current !== id) {
      return;
    }

    if (loadedConversationRef.current === id && id) {
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setMessages([]);
    setSuggestions([]);
    setIsLoading(false);
    setIsProcessing(false);
    processingConversationRef.current = null;

    if (!id || id === 'undefined' || id === 'null') {
      setMessages([getWelcomeMessage()]);
      setVacationSummary(null);
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

      if (loadedConversationRef.current !== id) {
        return;
      }

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

      // Update vacation summary from conversation preferences if available
      if (conversation.vacation_preferences && 
          Object.keys(conversation.vacation_preferences).length > 0) {
        const prefs = conversation.vacation_preferences;
        const destinations = prefs.destinations || (prefs.destination ? [prefs.destination] : []);
        
        if (destinations.length > 0 || prefs.destination) {
          setVacationSummary({
            destination: prefs.destination || destinations[0],
            destinations: destinations,
            budget_range: prefs.budget_range,
            budget_amount: prefs.budget_amount,
            travel_style: prefs.travel_style,
            travel_dates: prefs.travel_dates,
            group_size: prefs.group_size,
            interests: prefs.interests
          });
        } else {
          // If preferences exist but no destinations, don't clear existing summary
          // It might have been set from a recent message
        }
      }
      // If conversation doesn't have preferences yet, preserve existing vacationSummary
      // It might have been set from a recent message response

    } catch (error) {
      if (error.name === 'AbortError') {
        return;
      }

      if (error.message && !error.message.includes('404')) {
        console.error('Failed to load conversation:', error);
      }
      
      if (loadedConversationRef.current === id) {
        if (error.response?.status === 404 || (error.message && error.message.includes('404'))) {
          setMessages([getWelcomeMessage()]);
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

  const sendChatMessage = useCallback(async (content) => {
    // Prevent concurrent message sending
    if (isProcessing) {
      console.warn('Message already processing, ignoring new message');
      return;
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
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

    abortControllerRef.current = new AbortController();

    try {
      const response = await sendMessage(content, requestConversationId, {
        signal: abortControllerRef.current.signal
      });
      
      if (requestConversationId !== conversationId) {
        return;
      }
      
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (!requestConversationId && response.conversation_id) {
        loadedConversationRef.current = response.conversation_id;
        onConversationUpdate?.(response.conversation_id);
        setTimeout(() => {

          window.dispatchEvent(new CustomEvent('conversation-created', { 
            detail: { conversationId: response.conversation_id } 
          }));
        }, 100);
      }

      console.log('Full response received:', response);
      if (response.vacation_summary) {
        console.log('Received vacation_summary:', response.vacation_summary);
        console.log('Setting vacationSummary state with:', response.vacation_summary);
        setVacationSummary(response.vacation_summary);
      } else {
        console.warn('No vacation_summary in response. Response keys:', Object.keys(response || {}));
        console.log('Full response object:', JSON.stringify(response, null, 2));
      }
      if (response.suggestions) {
        setSuggestions(response.suggestions);
      }
    } catch (error) {
      if (error.name === 'AbortError' || error.message.includes('canceled') || requestConversationId !== conversationId) {
        return;
      }
      
      console.error('Error sending message:', error);
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
      if (requestConversationId === conversationId) {
        setIsLoading(false);
      }
      setIsProcessing(false);
      processingConversationRef.current = null;
      abortControllerRef.current = null;
    }
  }, [conversationId, onConversationUpdate]);

  const forceReload = useCallback(() => {
    loadedConversationRef.current = null;
    if (conversationId) {
      loadConversation(conversationId);
    }
  }, [conversationId, loadConversation]);

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
