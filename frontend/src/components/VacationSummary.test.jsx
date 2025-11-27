import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import VacationSummary from './VacationSummary';


describe('VacationSummary', () => {
  const mockSummary = {
    destination: 'Paris',
    destinations: ['Paris'],
    travel_dates: {
      start: '2024-06-01',
      end: '2024-06-07'
    },
    budget_range: 'moderate',
    travel_style: ['cultural', 'adventure'],
    status: 'Great! You\'re almost ready to go!'
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns null when summary is not provided', () => {
    const { container } = render(<VacationSummary summary={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders destination when provided', () => {
    render(<VacationSummary summary={mockSummary} />);
    expect(screen.getByText(/Paris/i)).toBeInTheDocument();
  });


  it('renders travel dates when provided', () => {
    render(<VacationSummary summary={mockSummary} />);
    expect(screen.getByText(/2024-06-01.*2024-06-07/i)).toBeInTheDocument();
  });

  it('renders budget range when provided', () => {
    render(<VacationSummary summary={mockSummary} />);
    expect(screen.getByText(/moderate/i)).toBeInTheDocument();
  });

  it('renders budget amount when provided', () => {
    const summaryWithAmount = {
      ...mockSummary,
      budget_amount: '$3,000',
    };
    render(<VacationSummary summary={summaryWithAmount} />);
    expect(screen.getByText(/\$3,000/i)).toBeInTheDocument();
    expect(screen.getByText(/moderate range/i)).toBeInTheDocument();
  });

  it('renders travel style tags when provided', () => {
    render(<VacationSummary summary={mockSummary} />);
    expect(screen.getByText(/cultural/i)).toBeInTheDocument();
    expect(screen.getByText(/adventure/i)).toBeInTheDocument();
  });

  it('renders status message when provided', () => {
    render(<VacationSummary summary={mockSummary} />);
    expect(screen.getByText(/Great! You're almost ready/i)).toBeInTheDocument();
  });


  it('handles missing optional fields gracefully', () => {
    const minimalSummary = {
      destination: 'Paris',
      destinations: ['Paris']
    };
    render(<VacationSummary summary={minimalSummary} />);
    expect(screen.getByText(/Paris/i)).toBeInTheDocument();
  });
});
