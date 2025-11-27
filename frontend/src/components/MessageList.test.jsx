import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MessageList from './MessageList';

describe('MessageList', () => {

  const mockMessages = [
    {
      id: '1',
      content: 'Hello, how can I help you plan your vacation?',
      role: 'assistant',
      timestamp: Date.now(),
    },
    {
      id: '2',
      content: 'I want to go to Paris',
      role: 'user',
      timestamp: Date.now(),
    },
  ];

  it('renders messages correctly', () => {

    render(<MessageList messages={mockMessages} isLoading={false} />);
    
    expect(screen.getByText('Hello, how can I help you plan your vacation?')).toBeInTheDocument();
    expect(screen.getByText('I want to go to Paris')).toBeInTheDocument();
  });

  it('renders loading state when isLoading is true', () => {

    render(<MessageList messages={[]} isLoading={true} />);
    
    expect(screen.getByText('Planning your perfect vacation...')).toBeInTheDocument();
  });

  it('renders empty state when no messages', () => {

    render(<MessageList messages={[]} isLoading={false} />);
    
    const messageList = screen.getByTestId('message-list');
    expect(messageList.children).toHaveLength(0);
  });

  it('renders user and assistant messages with correct styling', () => {

    render(<MessageList messages={mockMessages} isLoading={false} />);
    
    const assistantMessage = screen.getByText('Hello, how can I help you plan your vacation?');
    const userMessage = screen.getByText('I want to go to Paris');
    


    const messageContainer = assistantMessage.closest('div').parentElement;
    expect(messageContainer).toHaveClass('bg-gray-100', 'text-gray-800');
    expect(userMessage.closest('div')).toHaveClass('bg-primary-600');
  });

  it('renders error messages with error styling', () => {

    const errorMessages = [
      {
        id: '1',
        content: 'An error occurred',
        role: 'assistant',
        isError: true,
        timestamp: Date.now(),
      },
    ];

    render(<MessageList messages={errorMessages} isLoading={false} />);
    
    expect(screen.getByText('An error occurred')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('renders messages with confidence scores', () => {

    const messagesWithConfidence = [
      {
        id: '1',
        content: 'I recommend Paris',
        role: 'assistant',
        metadata: { confidence_score: 0.85 },
        timestamp: Date.now(),
      },
    ];

    render(<MessageList messages={messagesWithConfidence} isLoading={false} />);
    
    expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
  });

  it('handles markdown content correctly', () => {

    const markdownMessage = [
      {
        id: '1',
        content: '**Bold text** and *italic text*',
        role: 'assistant',
        timestamp: Date.now(),
      },
    ];

    render(<MessageList messages={markdownMessage} isLoading={false} />);
    
    expect(screen.getByText('Bold text')).toBeInTheDocument();
    expect(screen.getByText('italic text')).toBeInTheDocument();
  });

  it('handles special characters in messages', () => {

    const specialCharMessage = [
      {
        id: '1',
        content: 'Test with <script>alert("xss")</script>',
        role: 'assistant',
        timestamp: Date.now(),
      },
    ];

    render(<MessageList messages={specialCharMessage} isLoading={false} />);
    
    expect(screen.getByText(/Test with/)).toBeInTheDocument();
  });

  it('handles very long messages', () => {

    const longMessage = [
      {
        id: '1',
        content: 'A'.repeat(1000),
        role: 'assistant',
        timestamp: Date.now(),
      },
    ];

    render(<MessageList messages={longMessage} isLoading={false} />);
    
    expect(screen.getByText('A'.repeat(1000))).toBeInTheDocument();
  });

  it('handles messages with missing properties gracefully', () => {

    const incompleteMessages = [
      {
        id: '1',
        content: 'Valid message',
        role: 'assistant',
        timestamp: Date.now(),
      },
      {
        id: '2',
        role: 'user',
        timestamp: Date.now(),
      },
      {
        content: 'No ID',
        role: 'assistant',
        timestamp: Date.now(),
      },
    ];

    render(<MessageList messages={incompleteMessages} isLoading={false} />);
    
    expect(screen.getByText('Valid message')).toBeInTheDocument();
  });

  it('renders user and assistant avatars correctly', () => {

    render(<MessageList messages={mockMessages} isLoading={false} />);
    
    const avatars = screen.getAllByText(/✈️|👤/);
    expect(avatars).toHaveLength(2);
  });

  it('applies dark mode classes correctly', () => {

    render(<MessageList messages={mockMessages} isLoading={false} />);
    
    const assistantMessage = screen.getByText('Hello, how can I help you plan your vacation?');
    const userMessage = screen.getByText('I want to go to Paris');
    


    const messageContainer = assistantMessage.closest('div').parentElement;
    expect(messageContainer).toHaveClass('dark:bg-gray-800', 'dark:text-gray-100');
    expect(userMessage.closest('div')).toHaveClass('dark:bg-primary-700', 'dark:text-white');
  });
}); 