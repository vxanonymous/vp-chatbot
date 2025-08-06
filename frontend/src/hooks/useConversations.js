import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  getConversations, 
  createConversation, 
  updateConversation, 
  deleteConversation 
} from '../services/api';
import { useNotification } from '../contexts/NotificationContext';

// Custom hook for managing conversations with optimistic updates
export const useConversations = () => {
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { addNotification } = useNotification();

  // Use ref to track pending operations for deduplication
  const pendingOps = useRef(new Set());
  
  // Normalize conversation object
  const normalizeConversation = useCallback((conv) => ({
    ...conv,
    id: conv.id || conv._id,
    _id: conv._id || conv.id,
    title: conv.title || 'Untitled Conversation',
    updated_at: conv.updated_at || conv.created_at || new Date().toISOString()
  }), []);

  // Load conversations with error handling and retry
  const loadConversations = useCallback(async (retries = 3) => {
    const opId = 'load-conversations';
    if (pendingOps.current.has(opId)) return;
    
    pendingOps.current.add(opId);
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await getConversations();
      if (Array.isArray(data)) {
        const normalized = data.map(normalizeConversation);
        setConversations(normalized.sort((a, b) => 
          new Date(b.updated_at) - new Date(a.updated_at)
        ));
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError(err);
      
      if (retries > 0) {
        setTimeout(() => loadConversations(retries - 1), 1000 * (4 - retries));
      } else {
        addNotification('Failed to load conversations', 'error');
      }
    } finally {
      setIsLoading(false);
      pendingOps.current.delete(opId);
    }
  }, [normalizeConversation, addNotification]);

  // Create conversation with optimistic update
  const createNewConversation = useCallback(async (title = 'New Conversation') => {
    const opId = 'create-conversation';
    if (pendingOps.current.has(opId)) return null;
    
    pendingOps.current.add(opId);
    
    // Create optimistic conversation
    const optimisticConv = {
      id: `temp-${Date.now()}`,
      _id: `temp-${Date.now()}`,
      title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [],
      vacation_preferences: {},
      is_active: true
    };
    
    // Add to state immediately
    setConversations(prev => [optimisticConv, ...prev]);
    
    try {
      const newConv = await createConversation(title);
      const normalized = normalizeConversation(newConv);
      
      // Replace optimistic with real conversation
      setConversations(prev => 
        prev.map(c => c.id === optimisticConv.id ? normalized : c)
      );
      
      addNotification('Conversation created', 'success');
      return normalized;
    } catch (error) {
      // Remove optimistic conversation on error
      setConversations(prev => prev.filter(c => c.id !== optimisticConv.id));
      addNotification('Failed to create conversation', 'error');
      throw error;
    } finally {
      pendingOps.current.delete(opId);
    }
  }, [normalizeConversation, addNotification]);

  // Update conversation title with optimistic update
  const updateConversationTitle = useCallback(async (id, title) => {
    const opId = `update-${id}`;
    if (pendingOps.current.has(opId)) return;
    
    pendingOps.current.add(opId);
    
    // Store original state for rollback
    const originalConversations = conversations;
    
    // Optimistic update
    setConversations(prev => 
      prev.map(c => 
        (c.id === id || c._id === id) 
          ? { ...c, title, updated_at: new Date().toISOString() }
          : c
      )
    );
    
    try {
      await updateConversation(id, { title });
      addNotification('Conversation updated', 'success');
    } catch (error) {
      // Rollback on error
      setConversations(originalConversations);
      addNotification('Failed to update conversation', 'error');
      throw error;
    } finally {
      pendingOps.current.delete(opId);
    }
  }, [conversations, addNotification]);

  // Delete conversation with optimistic update
  const removeConversation = useCallback(async (id) => {
    const opId = `delete-${id}`;
    if (pendingOps.current.has(opId)) return false;
    
    pendingOps.current.add(opId);
    
    // Store original state for rollback
    const originalConversations = conversations;
    
    // Optimistic update
    setConversations(prev => prev.filter(c => c.id !== id && c._id !== id));
    
    try {
      await deleteConversation(id);
      addNotification('Conversation deleted', 'success');
      return true;
    } catch (error) {
      // Rollback on error
      setConversations(originalConversations);
      addNotification('Failed to delete conversation', 'error');
      return false;
    } finally {
      pendingOps.current.delete(opId);
    }
  }, [conversations, addNotification]);

  // Update conversation timestamp (for message updates)
  const touchConversation = useCallback((id) => {
    setConversations(prev => {
      const updated = prev.map(c => 
        (c.id === id || c._id === id)
          ? { ...c, updated_at: new Date().toISOString() }
          : c
      );
      return updated.sort((a, b) => 
        new Date(b.updated_at) - new Date(a.updated_at)
      );
    });
  }, []);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Listen for new conversation events
  useEffect(() => {
    const handleNewConversation = () => {
      // Refresh conversations list when a new conversation is created
      setTimeout(() => {
        loadConversations();
      }, 200);
    };

    window.addEventListener('conversation-created', handleNewConversation);
    
    return () => {
      window.removeEventListener('conversation-created', handleNewConversation);
    };
  }, [loadConversations]);

  return {
    conversations,
    isLoading,
    error,
    loadConversations,
    createNewConversation,
    updateConversationTitle,
    removeConversation,
    touchConversation,
    refetch: loadConversations
  };
};