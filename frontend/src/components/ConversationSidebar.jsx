import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  LogOut,
  User
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';

const ConversationSidebar = ({ 

  isOpen, 
  onToggle, 
  conversations = [], 
  isLoading,
  onNewConversation,
  onDeleteConversation,
  onUpdateConversation,
  selectedConversationId,
  disabled = false
}) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { addNotification } = useNotification();
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const handleSelectConversation = (conv) => {

    if (disabled) {
      return;
    }
    const id = conv.id || conv._id;
    navigate(`/chat/${id}`);

    if (window.innerWidth < 768) {
      onToggle();
    }
  };

  const handleEditStart = (conv) => {

    const id = conv.id || conv._id;
    setEditingId(id);
    setEditTitle(conv.title);
  };

  const handleEditSave = async () => {

    if (!editTitle.trim()) {
      addNotification('Title cannot be empty', 'error');
      return;
    }
    
    try {
      await onUpdateConversation(editingId, editTitle);
      setEditingId(null);
      setEditTitle('');
    } catch (error) {

      setEditingId(null);
      setEditTitle('');
    }
  };

  const handleEditCancel = () => {

    setEditingId(null);
    setEditTitle('');
  };

  const handleDelete = async (e, conv) => {

    e.stopPropagation();
    const id = conv.id || conv._id;
    await onDeleteConversation(id);
  };

  const formatTime = (dateString) => {

    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Recently';
      }
      
      const now = new Date();
      const diffInHours = (now - date) / (1000 * 60 * 60);

      

      if (diffInHours < 1) {
        const diffInMinutes = Math.floor((now - date) / (1000 * 60));
        return diffInMinutes <= 1 ? 'Just now' : `${diffInMinutes}m ago`;
      } else if (diffInHours < 24) {
        return format(date, 'h:mm a');
      } else if (diffInHours < 48) {
        return 'Yesterday';
      } else {
        return format(date, 'MMM d');
      }
    } catch (error) {
      return 'Recently';
    }
  };

  return (
    <div className={`
      fixed inset-y-0 left-0 z-50 w-64 h-full bg-gray-900 dark:bg-gray-950 text-white dark:text-gray-100
      transform transition-transform duration-300 ease-in-out
      ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      md:relative md:translate-x-0
    `}>
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold">Vacation Planner</h1>
            <button
              onClick={onToggle}
              className="md:hidden text-gray-400 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <button
            onClick={onNewConversation}
            disabled={disabled}
            className={`mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              disabled 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-primary-600 hover:bg-primary-700 dark:bg-primary-700 dark:hover:bg-primary-800'
            }`}
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-400">Loading...</div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-400">
              No conversations yet
            </div>
          ) : (
            <div className="p-2">
              {conversations.map((conv) => {
                const convId = conv.id || conv._id;
                const isActive = selectedConversationId === convId;
                const isEditing = editingId === convId;
                
                return (
                  <div
                    key={convId}
                    className={`
                      group mb-1 rounded-lg transition-colors
                      ${isActive ? 'bg-gray-800 dark:bg-gray-900' : 'hover:bg-gray-800 dark:hover:bg-gray-900'}
                      ${disabled && !isActive ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    {isEditing ? (
                      <div className="flex items-center p-2 gap-2">
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          className="flex-1 px-2 py-1 text-sm bg-gray-700 rounded border border-gray-600 focus:border-primary-500 focus:outline-none"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleEditSave();
                            if (e.key === 'Escape') handleEditCancel();
                          }}
                        />
                        <button
                          onClick={handleEditSave}
                          className="text-green-500 hover:text-green-400"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                        <button
                          onClick={handleEditCancel}
                          className="text-gray-400 hover:text-white"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <div
                        onClick={() => !disabled && handleSelectConversation(conv)}
                        className="flex items-center p-2 gap-3"
                      >
                        <MessageSquare className={`h-4 w-4 flex-shrink-0 ${isActive ? 'text-primary-400' : 'text-gray-400'}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {conv.title || 'Untitled'}
                          </p>
                          <p className="text-xs text-gray-400">
                            {formatTime(conv.updated_at || conv.created_at)}
                          </p>
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!disabled) handleEditStart(conv);
                            }}
                            disabled={disabled}
                            className={`text-gray-400 hover:text-white p-1 ${disabled ? 'cursor-not-allowed' : ''}`}
                          >
                            <Edit2 className="h-3 w-3" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!disabled) handleDelete(e, conv);
                            }}
                            disabled={disabled}
                            className={`text-gray-400 hover:text-red-400 p-1 ${disabled ? 'cursor-not-allowed' : ''}`}
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="border-t border-gray-800 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <User className="h-4 w-4" />
              </div>
              <div className="text-sm">
                <p className="font-medium truncate">{user?.full_name}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="text-gray-400 hover:text-white"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationSidebar;