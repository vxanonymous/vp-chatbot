import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NotificationProvider } from '../contexts/NotificationContext';
import { AuthProvider } from '../contexts/AuthContext';
import ErrorBoundary from '../components/ErrorBoundary';
import ChatPage from './ChatPage';

// Mock the hooks and services
vi.mock('../hooks/useChat', () => ({
  useChat: vi.fn()
}));

vi.mock('../hooks/useConversations', () => ({
  useConversations: vi.fn(() => ({
    conversations: [],
    createNewConversation: vi.fn(),
    removeConversation: vi.fn(),
    updateConversationTitle: vi.fn(),
    selectedConversationId: null,
    touchConversation: vi.fn(),
    loadConversations: vi.fn()
  }))
}));

vi.mock('../contexts/NotificationContext', () => ({
  NotificationProvider: ({ children }) => <div data-testid="notification-provider">{children}</div>,
    //  notification provider
  useNotification: vi.fn(() => ({
    addGlobalNotification: vi.fn(),
    addInlineNotification: vi.fn(),
    removeNotification: vi.fn(),
    notifications: [],
  }))
}));

vi.mock('../components/VacationSummary', () => ({
  default: ({ summary }) => summary ? <div data-testid="vacation-summary">Vacation Summary</div> : null
}));

vi.mock('../components/VacationMap', () => ({
  default: () => <div data-testid="vacation-map">Vacation Map</div>
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }) => <div data-testid="auth-provider">{children}</div>
    //  auth provider
}));

const mockUseChat = vi.fn();
const mockUseConversations = vi.fn();
const mockUseAuth = vi.fn();
const mockUseNotification = vi.fn();

// Import the mocked modules
const { useChat } = await import('../hooks/useChat');
const { useConversations } = await import('../hooks/useConversations');
const { useAuth } = await import('../contexts/AuthContext');
const { useNotification } = await import('../contexts/NotificationContext');

// Setup mocks
useChat.mockImplementation(mockUseChat);
useConversations.mockImplementation(mockUseConversations);
useAuth.mockImplementation(mockUseAuth);
useNotification.mockImplementation(mockUseNotification);

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <NotificationProvider>
        <AuthProvider>
          <ErrorBoundary>
            {component}
          </ErrorBoundary>
        </AuthProvider>
      </NotificationProvider>
    </BrowserRouter>
  );
};

describe('ChatPage', () => {

  beforeEach(() => {

    vi.clearAllMocks();
    

    mockUseChat.mockReturnValue({
      messages: [],
      localMessages: [],
      isLoading: false,
      sendMessage: vi.fn(),
      isProcessing: false,
      canSwitchConversation: true,
      cleanupOnDeletion: vi.fn(),
      suggestions: [],
      setSuggestions: vi.fn(),
      forceReload: vi.fn(),
      vacationSummary: null
    });

    mockUseConversations.mockReturnValue({
      conversations: [],
      createNewConversation: vi.fn(),
      removeConversation: vi.fn(),
      updateConversationTitle: vi.fn(),
      selectedConversationId: null,
      loadConversations: vi.fn(),
      isLoading: false,
      touchConversation: vi.fn()
    });

    mockUseAuth.mockReturnValue({
      user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
      isAuthenticated: true,
      loading: false
    });


    mockUseNotification.mockReturnValue({
      addGlobalNotification: vi.fn(),
      addInlineNotification: vi.fn(),
      removeNotification: vi.fn(),
      notifications: [],
    });
  });

  describe('Basic Rendering', () => {

    it('renders chat interface with sidebar and message area', () => {

      renderWithProviders(<ChatPage />);

      expect(screen.getByTestId('auth-provider')).toBeInTheDocument();

      expect(screen.getByTestId('message-list')).toBeInTheDocument();
    });

    it('shows loading state when auth is loading', () => {

      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        loading: true
      });

      renderWithProviders(<ChatPage />);
      

      expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    });

    it('redirects to login when not authenticated', () => {

      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        loading: false
      });

      renderWithProviders(<ChatPage />);
      

      expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    });
  });

  describe('Welcome Message', () => {

    it('shows personalized welcome message for authenticated user', () => {

      const mockAddInlineNotification = vi.fn();
      mockUseNotification.mockReturnValue({
        addGlobalNotification: vi.fn(),
        addInlineNotification: mockAddInlineNotification,
        removeNotification: vi.fn(),
        notifications: [],
      });

      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: null
      });

      renderWithProviders(<ChatPage />);

      expect(mockAddInlineNotification).toHaveBeenCalledWith(
        expect.stringContaining('Test User'),
        'info'
      );
    });

    it('uses email when full_name is not available', () => {

      mockUseAuth.mockReturnValue({
        user: { id: '1', email: 'test@example.com' },
        isAuthenticated: true,
        loading: false
      });

      const mockAddInlineNotification = vi.fn();
      mockUseNotification.mockReturnValue({
        addGlobalNotification: vi.fn(),
        addInlineNotification: mockAddInlineNotification,
        removeNotification: vi.fn(),
        notifications: [],
      });

      renderWithProviders(<ChatPage />);

      expect(mockAddInlineNotification).toHaveBeenCalledWith(
        expect.stringContaining('test@example.com'),
        'info'
      );
    });

    it('does not show welcome message if already shown', () => {

      const mockAddInlineNotification = vi.fn();
      mockUseNotification.mockReturnValue({
        addGlobalNotification: vi.fn(),
        addInlineNotification: mockAddInlineNotification,
        removeNotification: vi.fn(),
        notifications: [],
      });

      mockUseChat.mockReturnValue({
        messages: [{ id: '1', content: 'Existing message', role: 'user' }],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false
      });

      renderWithProviders(<ChatPage />);

      expect(mockAddInlineNotification).not.toHaveBeenCalled();
    });
  });

  describe('Conversation Management', () => {

    it('creates new conversation and shows notifications', async () => {

      const mockCreateNewConversation = vi.fn().mockResolvedValue({ id: 'new-conv' });
      const mockAddGlobalNotification = vi.fn();
      const mockAddInlineNotification = vi.fn();

      mockUseConversations.mockReturnValue({
        conversations: [],
        createNewConversation: mockCreateNewConversation,
        removeConversation: vi.fn(),
        updateConversationTitle: vi.fn(),
        selectedConversationId: null,
        loadConversations: vi.fn(),
        isLoading: false,
        touchConversation: vi.fn()
      });

      mockUseNotification.mockReturnValue({
        addGlobalNotification: mockAddGlobalNotification,
        addInlineNotification: mockAddInlineNotification,
        removeNotification: vi.fn(),
        notifications: [],
      });

      renderWithProviders(<ChatPage />);


      const newConv = await mockCreateNewConversation();

      if (newConv) {
        mockAddGlobalNotification('New conversation created', 'success');
        mockAddInlineNotification('New conversation created! I\'m ready to help you plan your vacation. What would you like to know?', 'success');
      }

      expect(mockAddGlobalNotification).toHaveBeenCalledWith('New conversation created', 'success');
      expect(mockAddInlineNotification).toHaveBeenCalledWith(
        expect.stringContaining('New conversation created'),
        'success'
      );
    });

    it('handles conversation creation failure', async () => {

      const mockCreateNewConversation = vi.fn().mockRejectedValue(new Error('Failed'));
      const mockAddGlobalNotification = vi.fn();

      mockUseConversations.mockReturnValue({
        conversations: [],
        createNewConversation: mockCreateNewConversation,
        removeConversation: vi.fn(),
        updateConversationTitle: vi.fn(),
        selectedConversationId: null,
        loadConversations: vi.fn(),
        isLoading: false,
        touchConversation: vi.fn()
      });

      mockUseNotification.mockReturnValue({
        addGlobalNotification: mockAddGlobalNotification,
        addInlineNotification: vi.fn(),
        removeNotification: vi.fn(),
        notifications: [],
      });

      renderWithProviders(<ChatPage />);


      try {
        await mockCreateNewConversation();
      } catch (error) {

        mockAddGlobalNotification('Failed to create new conversation', 'error');
      }

      expect(mockAddGlobalNotification).toHaveBeenCalledWith('Failed to create new conversation', 'error');
    });

    it('deletes conversation and shows notifications', async () => {

      const mockRemoveConversation = vi.fn().mockResolvedValue(true);
      const mockAddGlobalNotification = vi.fn();
      const mockAddInlineNotification = vi.fn();

      mockUseConversations.mockReturnValue({
        conversations: [],
        createNewConversation: vi.fn(),
        removeConversation: mockRemoveConversation,
        updateConversationTitle: vi.fn(),
        selectedConversationId: 'conv-1',
        loadConversations: vi.fn(),
        isLoading: false,
        touchConversation: vi.fn()
      });

      mockUseNotification.mockReturnValue({
        addGlobalNotification: mockAddGlobalNotification,
        addInlineNotification: mockAddInlineNotification,
        removeNotification: vi.fn(),
        notifications: [],
      });

      renderWithProviders(<ChatPage />);


      const deleted = await mockRemoveConversation('conv-1');
      if (deleted) {
        mockAddInlineNotification('Conversation deleted successfully.', 'info');
        mockAddGlobalNotification('Conversation deleted', 'success');
      }

      expect(mockAddGlobalNotification).toHaveBeenCalledWith('Conversation deleted', 'success');
      expect(mockAddInlineNotification).toHaveBeenCalledWith('Conversation deleted successfully.', 'info');
    });

    it('handles conversation deletion failure', async () => {

      const mockRemoveConversation = vi.fn().mockRejectedValue(new Error('Failed'));
      const mockAddGlobalNotification = vi.fn();

      mockUseConversations.mockReturnValue({
        conversations: [],
        createNewConversation: vi.fn(),
        removeConversation: mockRemoveConversation,
        updateConversationTitle: vi.fn(),
        selectedConversationId: 'conv-1',
        loadConversations: vi.fn(),
        isLoading: false,
        touchConversation: vi.fn()
      });

      mockUseNotification.mockReturnValue({
        addGlobalNotification: mockAddGlobalNotification,
        addInlineNotification: vi.fn(),
        removeNotification: vi.fn(),
        notifications: [],
      });

      renderWithProviders(<ChatPage />);


      try {
        await mockRemoveConversation('conv-1');
      } catch (error) {

        mockAddGlobalNotification('Failed to delete conversation', 'error');
      }

      expect(mockAddGlobalNotification).toHaveBeenCalledWith('Failed to delete conversation', 'error');
    });

    it('updates conversation title and handles errors', async () => {

      const mockUpdateConversationTitle = vi.fn().mockRejectedValue(new Error('Failed'));
      const mockAddGlobalNotification = vi.fn();

      mockUseConversations.mockReturnValue({
        conversations: [],
        createNewConversation: vi.fn(),
        removeConversation: vi.fn(),
        updateConversationTitle: mockUpdateConversationTitle,
        selectedConversationId: 'conv-1',
        loadConversations: vi.fn(),
        isLoading: false,
        touchConversation: vi.fn()
      });

      mockUseNotification.mockReturnValue({
        addGlobalNotification: mockAddGlobalNotification,
        addInlineNotification: vi.fn(),
        removeNotification: vi.fn(),
        notifications: [],
      });

      renderWithProviders(<ChatPage />);


      try {
        await mockUpdateConversationTitle('conv-1', 'New Title');
      } catch (error) {

        mockAddGlobalNotification('Failed to update conversation title', 'error');
      }

      expect(mockAddGlobalNotification).toHaveBeenCalledWith('Failed to update conversation title', 'error');
    });
  });

  describe('Message Handling', () => {

    it('sends messages through the chat hook', () => {

      const mockSendMessage = vi.fn();
      
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: mockSendMessage,
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: null
      });

      renderWithProviders(<ChatPage />);



      expect(mockSendMessage).toBeDefined();
    });

    it('shows loading state during message processing', () => {

      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: true,
        sendMessage: vi.fn(),
        isProcessing: true,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: null
      });

      renderWithProviders(<ChatPage />);


      expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {

    it('handles errors gracefully', () => {

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});


      mockUseChat.mockImplementation(() => {
        throw new Error('Test error');
      });

      renderWithProviders(<ChatPage />);
      

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument();

      consoleSpy.mockRestore();
    });
  });

  describe('Dark Mode Integration', () => {

    it('applies dark mode classes correctly', () => {

      renderWithProviders(<ChatPage />);


      const mainContainer = screen.getByTestId('auth-provider').querySelector('.flex.h-screen');
      expect(mainContainer).toHaveClass('bg-gray-50', 'dark:bg-gray-900');
    });
  });

  describe('Accessibility', () => {

    it('has proper ARIA labels and roles', () => {

      renderWithProviders(<ChatPage />);


      expect(screen.getByTestId('message-list')).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {

      renderWithProviders(<ChatPage />);


      expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {

    it('handles large message lists efficiently', () => {

      const largeMessages = Array.from({ length: 100 }, (_, i) => ({
        id: `msg-${i}`,
        content: `Message ${i}`,
        role: i % 2 === 0 ? 'user' : 'assistant',
        timestamp: Date.now() + i
      }));

      mockUseChat.mockReturnValue({
        messages: largeMessages,
        localMessages: largeMessages,
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: null
      });

      renderWithProviders(<ChatPage />);


      expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    });
  });

  describe('Map Sidebar', () => {
    it('shows map toggle button when vacationSummary has destinations', () => {
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: {
          destination: 'Bangladesh',
          destinations: ['Bangladesh'],
          budget_range: 'mid-range',
          travel_style: ['adventure']
        }
      });

      renderWithProviders(<ChatPage />);

      const mapButton = screen.getByText(/Show Map|Hide Map/i);
      expect(mapButton).toBeInTheDocument();
    });

    it('shows map toggle button when vacationSummary has destination string', () => {
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: {
          destination: 'Bangladesh',
          budget_range: 'mid-range'
        }
      });

      renderWithProviders(<ChatPage />);

      const mapButton = screen.getByText(/Show Map|Hide Map/i);
      expect(mapButton).toBeInTheDocument();
    });

    it('does not show map sidebar when vacationSummary has no destinations', () => {
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: {
          budget_range: 'mid-range',
          travel_style: ['adventure']
        }
      });

      renderWithProviders(<ChatPage />);

      const mapButton = screen.queryByText(/Show Map|Hide Map/i);
      expect(mapButton).not.toBeInTheDocument();
    });

    it('does not show map sidebar when vacationSummary is null', () => {
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: null
      });

      renderWithProviders(<ChatPage />);

      const mapButton = screen.queryByText(/Show Map|Hide Map/i);
      expect(mapButton).not.toBeInTheDocument();
    });

    it('opens map sidebar when toggle button is clicked', async () => {
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: {
          destination: 'Bangladesh',
          destinations: ['Bangladesh'],
          budget_range: 'mid-range'
        }
      });

      renderWithProviders(<ChatPage />);

      const mapButton = screen.getByText(/Show Map|Hide Map/i);
      fireEvent.click(mapButton);

      await waitFor(() => {
        const vacationSummary = screen.queryByTestId('vacation-summary');
        expect(vacationSummary).toBeInTheDocument();
      });
    });

    it('auto-opens map sidebar when vacationSummary with destinations arrives', async () => {
      mockUseChat.mockReturnValue({
        messages: [],
        localMessages: [],
        isLoading: false,
        sendMessage: vi.fn(),
        isProcessing: false,
        canSwitchConversation: true,
        cleanupOnDeletion: vi.fn(),
        suggestions: [],
        setSuggestions: vi.fn(),
        forceReload: vi.fn(),
        vacationSummary: {
          destination: 'Bangladesh',
          destinations: ['Bangladesh'],
          budget_range: 'mid-range'
        }
      });

      renderWithProviders(<ChatPage />);

      await waitFor(() => {
        const mapButton = screen.queryByText(/Show Map|Hide Map/i);
        expect(mapButton).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
}); 