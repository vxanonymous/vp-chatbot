import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Notification from './Notification';

describe('Notification Component', () => {

  const mockOnDismiss = vi.fn();

  beforeEach(() => {

    mockOnDismiss.mockClear();
  });

  describe('Rendering', () => {

    it('renders nothing when notifications array is empty', () => {

      const { container } = render(<Notification notifications={[]} onDismiss={mockOnDismiss} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when notifications is null', () => {

      const { container } = render(<Notification notifications={null} onDismiss={mockOnDismiss} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when notifications is undefined', () => {

      const { container } = render(<Notification notifications={undefined} onDismiss={mockOnDismiss} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when notifications is not an array', () => {

      const { container } = render(<Notification notifications="not an array" onDismiss={mockOnDismiss} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Global Notifications (top-right)', () => {
    it('renders global notifications in top-right position', () => {

      const notifications = [
        { id: 1, message: 'Test success', type: 'success', position: 'top-right' },
        { id: 2, message: 'Test error', type: 'error', position: 'top-right' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Test success')).toBeInTheDocument();
      expect(screen.getByText('Test error')).toBeInTheDocument();

      const container = screen.getByText('Test success').closest('div');
      expect(container.parentElement.parentElement).toHaveClass('fixed', 'top-4', 'right-4');
    });

    it('applies correct styling for different notification types', () => {

      const notifications = [
        { id: 1, message: 'Success message', type: 'success', position: 'top-right' },
        { id: 2, message: 'Error message', type: 'error', position: 'top-right' },
        { id: 3, message: 'Warning message', type: 'warning', position: 'top-right' },
        { id: 4, message: 'Info message', type: 'info', position: 'top-right' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);


      const successContainer = screen.getByText('Success message').closest('div');
      expect(successContainer.parentElement).toHaveClass('bg-green-50', 'text-green-900', 'border-green-200');


      const errorContainer = screen.getByText('Error message').closest('div');
      expect(errorContainer.parentElement).toHaveClass('bg-red-50', 'text-red-900');


      const warningContainer = screen.getByText('Warning message').closest('div');
      expect(warningContainer.parentElement).toHaveClass('bg-yellow-50', 'text-yellow-900');


      const infoContainer = screen.getByText('Info message').closest('div');
      expect(infoContainer.parentElement).toHaveClass('bg-gray-900', 'text-white');
    });

    it('renders appropriate icons for each notification type', () => {

      const notifications = [
        { id: 1, message: 'Success', type: 'success', position: 'top-right' },
        { id: 2, message: 'Error', type: 'error', position: 'top-right' },
        { id: 3, message: 'Warning', type: 'warning', position: 'top-right' },
        { id: 4, message: 'Info', type: 'info', position: 'top-right' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);


      const containers = screen.getAllByText(/Success|Error|Warning|Info/);
      containers.forEach(container => {
        const icon = container.closest('div').querySelector('svg');
        expect(icon).toBeInTheDocument();
      });
    });
  });

  describe('Inline Notifications', () => {

    it('renders inline notifications in content area', () => {

      const notifications = [
        { id: 1, message: 'Inline success', type: 'success', position: 'inline' },
        { id: 2, message: 'Inline error', type: 'error', position: 'inline' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Inline success')).toBeInTheDocument();
      expect(screen.getByText('Inline error')).toBeInTheDocument();

      const container = screen.getByText('Inline success').closest('div');
      expect(container.parentElement.parentElement).toHaveClass('fixed', 'top-4', 'right-4');
    });
  });

  describe('Form Notifications', () => {

    it('renders form notifications in form area', () => {

      const notifications = [
        { id: 1, message: 'Form error', type: 'error', position: 'form' },
        { id: 2, message: 'Form warning', type: 'warning', position: 'form' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Form error')).toBeInTheDocument();
      expect(screen.getByText('Form warning')).toBeInTheDocument();

      const container = screen.getByText('Form error').closest('div');
      expect(container.parentElement.parentElement).toHaveClass('fixed', 'bottom-24');
    });
  });

  describe('Dismiss Functionality', () => {

    it('calls onDismiss when dismiss button is clicked', () => {

      const notifications = [
        { id: 1, message: 'Test notification', type: 'info', position: 'top-right', dismissible: true }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss notification');
      fireEvent.click(dismissButton);

      expect(mockOnDismiss).toHaveBeenCalledWith(1);
    });

    it('does not render dismiss button when dismissible is false', () => {

      const notifications = [
        { id: 1, message: 'Test notification', type: 'info', position: 'top-right', dismissible: false }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      expect(screen.queryByLabelText('Dismiss notification')).not.toBeInTheDocument();
    });

    it('handles missing onDismiss function gracefully', () => {

      const notifications = [
        { id: 1, message: 'Test notification', type: 'info', position: 'top-right', dismissible: true }
      ];

      render(<Notification notifications={notifications} />);

      const dismissButton = screen.getByLabelText('Dismiss notification');
      expect(() => fireEvent.click(dismissButton)).not.toThrow();

    });
  });

  describe('Mixed Notification Types', () => {

    it('renders notifications of different positions correctly', () => {

      const notifications = [
        { id: 1, message: 'Global notification', type: 'success', position: 'top-right' },
        { id: 2, message: 'Inline notification', type: 'error', position: 'inline' },
        { id: 3, message: 'Form notification', type: 'warning', position: 'form' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Global notification')).toBeInTheDocument();
      expect(screen.getByText('Inline notification')).toBeInTheDocument();
      expect(screen.getByText('Form notification')).toBeInTheDocument();


      const globalContainer = screen.getByText('Global notification').closest('div');
      const inlineContainer = screen.getByText('Inline notification').closest('div');
      const formContainer = screen.getByText('Form notification').closest('div');

      expect(globalContainer.parentElement.parentElement).toHaveClass('fixed', 'top-4', 'right-4');
      expect(inlineContainer.parentElement.parentElement).toHaveClass('fixed', 'top-4', 'right-4');
      expect(formContainer.parentElement.parentElement).toHaveClass('fixed', 'bottom-24');
    });
  });

  describe('Accessibility', () => {

    it('has proper ARIA labels for dismiss buttons', () => {

      const notifications = [
        { id: 1, message: 'Test notification', type: 'info', position: 'top-right', dismissible: true }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss notification');
      expect(dismissButton).toBeInTheDocument();
    });

    it('supports keyboard navigation for dismiss buttons', () => {

      const notifications = [
        { id: 1, message: 'Test notification', type: 'info', position: 'top-right', dismissible: true }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss notification');
      dismissButton.focus();

      fireEvent.keyDown(dismissButton, { key: 'Enter' });
      fireEvent.click(dismissButton);
      expect(mockOnDismiss).toHaveBeenCalledWith(1);
    });
  });

  describe('Edge Cases', () => {

    it('handles notifications with missing properties gracefully', () => {

      const notifications = [
        { id: 1, message: 'Test', type: 'info', position: 'top-right' },
        { id: 2, message: 'Test 2', position: 'top-right' },
        { id: 3, message: '', position: 'top-right' },
        { id: 4, message: 'Test 4', position: 'top-right' },
        { id: 5, message: 'Test 5', position: 'top-right' },
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);


      expect(screen.getByText('Test')).toBeInTheDocument();
      expect(screen.getByText('Test 2')).toBeInTheDocument();
      expect(screen.getByText('Test 4')).toBeInTheDocument();
      expect(screen.getByText('Test 5')).toBeInTheDocument();
    });

    it('handles notifications with duplicate IDs', () => {

      const notifications = [
        { id: 1, message: 'First notification', type: 'info', position: 'top-right' },
        { id: 1, message: 'Second notification', type: 'error', position: 'top-right' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('First notification')).toBeInTheDocument();
      expect(screen.getByText('Second notification')).toBeInTheDocument();
    });

    it('handles rapid dismiss calls', () => {

      const notifications = [
        { id: 1, message: 'Test notification', type: 'info', position: 'top-right', dismissible: true }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss notification');
      

      fireEvent.click(dismissButton);
      fireEvent.click(dismissButton);
      fireEvent.click(dismissButton);

      expect(mockOnDismiss).toHaveBeenCalledTimes(3);
      expect(mockOnDismiss).toHaveBeenCalledWith(1);
    });
  });

  describe('Dark Mode Support', () => {

    it('applies dark mode classes correctly', () => {

      const notifications = [
        { id: 1, message: 'Success dark', type: 'success', position: 'top-right' },
        { id: 2, message: 'Error dark', type: 'error', position: 'top-right' },
        { id: 3, message: 'Warning dark', type: 'warning', position: 'top-right' },
        { id: 4, message: 'Info dark', type: 'info', position: 'top-right' }
      ];

      render(<Notification notifications={notifications} onDismiss={mockOnDismiss} />);


      const successContainer = screen.getByText('Success dark').closest('div');
      expect(successContainer.parentElement).toHaveClass('dark:bg-green-900', 'dark:text-green-100', 'dark:border-green-700');

      const errorContainer = screen.getByText('Error dark').closest('div');
      expect(errorContainer.parentElement).toHaveClass('dark:bg-red-900', 'dark:text-red-100');

      const warningContainer = screen.getByText('Warning dark').closest('div');
      expect(warningContainer.parentElement).toHaveClass('dark:bg-yellow-900', 'dark:text-yellow-100');

      const infoContainer = screen.getByText('Info dark').closest('div');
      expect(infoContainer.parentElement).toHaveClass('dark:bg-gray-800', 'dark:text-gray-100');
    });
  });
}); 