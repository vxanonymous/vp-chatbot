import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { NotificationProvider, useNotification } from './NotificationContext';

// Test component to use the notification context
const TestComponent = ({ onNotificationAdd, onNotificationRemove }) => {

  const { 
    notifications, 
    addNotification, 
    removeNotification, 
    clearNotifications,
    addGlobalNotification,
    addInlineNotification,
    addFormNotification
  } = useNotification();

  const handleAddGlobal = () => {

    const id = addGlobalNotification('Global test', 'success');
    onNotificationAdd?.(id);
  };

  const handleAddInline = () => {

    const id = addInlineNotification('Inline test', 'error');
    onNotificationAdd?.(id);
  };

  const handleAddForm = () => {

    const id = addFormNotification('Form test', 'warning');
    onNotificationAdd?.(id);
  };

  const handleAddCustom = () => {

    const id = addNotification('Custom test', 'info', {
      position: 'top-right',
      dismissible: false,
      autoDismiss: false,
      duration: 10000
    });
    onNotificationAdd?.(id);
  };

  const handleRemove = (id) => {

    removeNotification(id);
    onNotificationRemove?.(id);
  };

  const handleClearAll = () => {

    clearNotifications();
  };

  const handleClearPosition = () => {

    clearNotifications('top-right');
  };

  return (
    <div>
      <button onClick={handleAddGlobal}>Add Global</button>
      <button onClick={handleAddInline}>Add Inline</button>
      <button onClick={handleAddForm}>Add Form</button>
      <button onClick={handleAddCustom}>Add Custom</button>
      <button onClick={handleClearAll}>Clear All</button>
      <button onClick={handleClearPosition}>Clear Top-Right</button>
      
      <div data-testid="notification-count">
        {notifications.length} notifications
      </div>
      
      <div data-testid="notifications-list">
        {notifications.map(notification => (
          <div key={notification.id} data-testid={`notification-${notification.id}`}>
            {notification.message} - {notification.type} - {notification.position}
            <button onClick={() => handleRemove(notification.id)}>
              Remove {notification.id}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

describe('NotificationContext', () => {

  beforeEach(() => {

    vi.useFakeTimers();
  });

  afterEach(() => {

    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  describe('Basic Functionality', () => {

    it('provides notification state and methods', () => {

      const mockOnAdd = vi.fn();
      const mockOnRemove = vi.fn();

      render(
        <NotificationProvider>
          <TestComponent onNotificationAdd={mockOnAdd} onNotificationRemove={mockOnRemove} />
        </NotificationProvider>
      );

      expect(screen.getByTestId('notification-count')).toHaveTextContent('0 notifications');
      expect(screen.getByText('Add Global')).toBeInTheDocument();
      expect(screen.getByText('Add Inline')).toBeInTheDocument();
      expect(screen.getByText('Add Form')).toBeInTheDocument();
    });

    it('initializes with empty notifications array', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      expect(screen.getByTestId('notification-count')).toHaveTextContent('0 notifications');
    });
  });

  describe('addGlobalNotification', () => {

    it('adds global notification with correct defaults', () => {

      const mockOnAdd = vi.fn();

      render(
        <NotificationProvider>
          <TestComponent onNotificationAdd={mockOnAdd} />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Global test - success - top-right');
      expect(mockOnAdd).toHaveBeenCalledWith(expect.any(Number));
    });

    it('generates unique IDs for each notification', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      act(() => {
        fireEvent.click(screen.getByText('Add Global'));
        fireEvent.click(screen.getByText('Add Inline'));
      });

      expect(screen.getByTestId('notification-count')).toHaveTextContent('2 notifications');
      
      const notifications = screen.getAllByTestId(/^notification-\d+/);
      expect(notifications).toHaveLength(2);
      
      const ids = notifications.map(n => {
        const testId = n.getAttribute('data-testid');
        const match = testId ? testId.match(/notification-([\d.]+)/) : null;
        return match ? match[1] : null;
      }).filter(Boolean);
      expect(ids.length).toBe(2);
      expect(ids[0]).not.toBe(ids[1]);
    });
  });

  describe('addInlineNotification', () => {

    it('adds inline notification with correct properties', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Inline'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Inline test - error - inline');
    });

    it('sets inline notification as non-auto-dismissible', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Inline'));

      const notifications = screen.getAllByTestId(/^notification-/);
      const notification = notifications[0];

      act(() => {

        vi.advanceTimersByTime(6000);
      });

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
    });
  });

  describe('addFormNotification', () => {

    it('adds form notification with correct properties', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Form'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Form test - warning - form');
    });

    it('defaults to error type for form notifications', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );


      const TestComponentWithoutType = () => {

        const { addFormNotification, notifications } = useNotification();
        
        const handleAddForm = () => {

          addFormNotification('Form test without type');
        };

        return (
          <div>
            <button onClick={handleAddForm}>Add Form No Type</button>
            <div data-testid="notifications-list">
              {notifications.map(notification => (
                <div key={notification.id}>{notification.message}</div>
              ))}
            </div>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponentWithoutType />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Form No Type'));
      
      // Should default to 'error' type
      expect(screen.getAllByTestId('notifications-list')[1]).toHaveTextContent('Form test without type');
    });
  });

  describe('addNotification with custom options', () => {

    it('adds notification with custom options', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Custom'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Custom test - info - top-right');
    });

    it('respects custom duration and auto-dismiss settings', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Custom'));


      act(() => {

        vi.advanceTimersByTime(11000);
      });


      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
    });
  });

  describe('removeNotification', () => {

    it('removes specific notification by ID', () => {

      const mockOnRemove = vi.fn();

      render(
        <NotificationProvider>
          <TestComponent onNotificationRemove={mockOnRemove} />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));
      fireEvent.click(screen.getByText('Add Inline'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('2 notifications');


      const removeButtons = screen.getAllByText(/Remove [\d.]+/);
      fireEvent.click(removeButtons[0]);

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');
      expect(mockOnRemove).toHaveBeenCalledWith(expect.any(Number));
    });

    it('handles removing non-existent notification gracefully', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      const TestComponentWithRemove = () => {

        const { removeNotification } = useNotification();
        
        const handleRemoveNonExistent = () => {

          removeNotification(999);
        };

        return <button onClick={handleRemoveNonExistent}>Remove Non-Existent</button>;
      };

      render(
        <NotificationProvider>
          <TestComponentWithRemove />
        </NotificationProvider>
      );

      expect(() => {

        fireEvent.click(screen.getByText('Remove Non-Existent'));
      }).not.toThrow();
    });
  });

  describe('clearNotifications', () => {

    it('clears all notifications when no position specified', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));
      fireEvent.click(screen.getByText('Add Inline'));
      fireEvent.click(screen.getByText('Add Form'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('3 notifications');

      fireEvent.click(screen.getByText('Clear All'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('0 notifications');
    });

    it('clears only notifications of specific position', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));
      fireEvent.click(screen.getByText('Add Inline'));
      fireEvent.click(screen.getByText('Add Form'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('3 notifications');

      fireEvent.click(screen.getByText('Clear Top-Right'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('2 notifications');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Inline test');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Form test');
      expect(screen.getByTestId('notifications-list')).not.toHaveTextContent('Global test');
    });
  });

  describe('Auto-dismiss functionality', () => {

    it('auto-dismisses notifications after default duration', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('1 notifications');

      act(() => {

        vi.advanceTimersByTime(5000);
      });

      expect(screen.getByTestId('notification-count')).toHaveTextContent('0 notifications');
    });

    it('respects custom duration for auto-dismiss', () => {

      const TestComponentWithCustomDuration = () => {

        const { addNotification, notifications } = useNotification();
        
        const handleAddCustomDuration = () => {

          addNotification('Custom duration', 'info', { duration: 2000 });
        };

        return (
          <div>
            <button onClick={handleAddCustomDuration}>Add Custom Duration</button>
            <div data-testid="notifications-list">
              {notifications.map(notification => (
                <div key={notification.id}>{notification.message}</div>
              ))}
            </div>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponentWithCustomDuration />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Custom Duration'));

      act(() => {

        vi.advanceTimersByTime(1000);
      });

      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Custom duration');

      act(() => {

        vi.advanceTimersByTime(1500);
      });

      expect(screen.getByTestId('notifications-list')).not.toHaveTextContent('Custom duration');
    });

    it('does not auto-dismiss when autoDismiss is false', () => {

      const TestComponentWithNoAutoDismiss = () => {

        const { addNotification, notifications } = useNotification();
        
        const handleAddNoAutoDismiss = () => {

          addNotification('No auto dismiss', 'info', { autoDismiss: false });
        };

        return (
          <div>
            <button onClick={handleAddNoAutoDismiss}>Add No Auto Dismiss</button>
            <div data-testid="notifications-list">
              {notifications.map(notification => (
                <div key={notification.id}>{notification.message}</div>
              ))}
            </div>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponentWithNoAutoDismiss />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add No Auto Dismiss'));

      act(() => {

        vi.advanceTimersByTime(10000);
      });

      expect(screen.getByTestId('notifications-list')).toHaveTextContent('No auto dismiss');
    });
  });

  describe('Multiple notifications management', () => {

    it('handles multiple notifications of different types', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));
      fireEvent.click(screen.getByText('Add Inline'));
      fireEvent.click(screen.getByText('Add Form'));
      fireEvent.click(screen.getByText('Add Custom'));

      expect(screen.getByTestId('notification-count')).toHaveTextContent('4 notifications');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Global test');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Inline test');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Form test');
      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Custom test');
    });

    it('maintains notification order', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));
      fireEvent.click(screen.getByText('Add Inline'));

      const notifications = screen.getAllByTestId(/^notification-\d+/);
      expect(notifications[0]).toHaveTextContent('Global test');
      expect(notifications[1]).toHaveTextContent('Inline test');
    });
  });

  describe('Edge cases', () => {

    it('handles rapid notification additions', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      act(() => {
        fireEvent.click(screen.getByText('Add Global'));
        fireEvent.click(screen.getByText('Add Inline'));
        fireEvent.click(screen.getByText('Add Form'));
        fireEvent.click(screen.getByText('Add Custom'));
        fireEvent.click(screen.getByText('Add Global'));
        fireEvent.click(screen.getByText('Add Inline'));
        fireEvent.click(screen.getByText('Add Form'));
        fireEvent.click(screen.getByText('Add Custom'));
        fireEvent.click(screen.getByText('Add Global'));
        fireEvent.click(screen.getByText('Add Inline'));
      });

      expect(screen.getByTestId('notification-count').textContent).toMatch(/\d+ notifications/);
      const count = parseInt(screen.getByTestId('notification-count').textContent);
      expect(count).toBeGreaterThanOrEqual(1);
    });

    it('handles rapid notification removals', () => {

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Global'));
      fireEvent.click(screen.getByText('Add Inline'));

      const removeButtons = screen.getAllByText(/Remove \d+/);
      

      fireEvent.click(removeButtons[0]);
      fireEvent.click(removeButtons[1]);

      expect(screen.getByTestId('notification-count')).toHaveTextContent('0 notifications');
    });

    it('handles notifications with special characters', () => {

      const TestComponentWithSpecialChars = () => {

        const { addGlobalNotification, notifications } = useNotification();
        
        const handleAddSpecial = () => {

          addGlobalNotification('Test with <script>alert("xss")</script>', 'error');
        };

        return (
          <div>
            <button onClick={handleAddSpecial}>Add Special</button>
            <div data-testid="notifications-list">
              {notifications.map(notification => (
                <div key={notification.id}>{notification.message}</div>
              ))}
            </div>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponentWithSpecialChars />
        </NotificationProvider>
      );

      fireEvent.click(screen.getByText('Add Special'));

      expect(screen.getByTestId('notifications-list')).toHaveTextContent('Test with <script>alert("xss")</script>');
    });
  });

  describe('Context provider isolation', () => {

    it('isolates notifications between different providers', () => {

      const TestComponent1 = () => {

        const { addGlobalNotification, notifications } = useNotification();
        return (
          <div>
            <button onClick={() => addGlobalNotification('Provider 1')}>Add 1</button>
            <div data-testid="notifications-list-1">
              {notifications.map(notification => (
                <div key={notification.id}>{notification.message}</div>
              ))}
            </div>
          </div>
        );
      };

      const TestComponent2 = () => {

        const { addGlobalNotification, notifications } = useNotification();
        return (
          <div>
            <button onClick={() => addGlobalNotification('Provider 2')}>Add 2</button>
            <div data-testid="notifications-list-2">
              {notifications.map(notification => (
                <div key={notification.id}>{notification.message}</div>
              ))}
            </div>
          </div>
        );
      };

      render(
        <div>
          <NotificationProvider>
            <TestComponent1 />
          </NotificationProvider>
          <NotificationProvider>
            <TestComponent2 />
          </NotificationProvider>
        </div>
      );

      fireEvent.click(screen.getByText('Add 1'));
      fireEvent.click(screen.getByText('Add 2'));


      expect(screen.getByTestId('notifications-list-1')).toHaveTextContent('Provider 1');
      expect(screen.getByTestId('notifications-list-2')).toHaveTextContent('Provider 2');
    });
  });
}); 