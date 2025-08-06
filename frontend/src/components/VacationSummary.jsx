import React from 'react';

const VacationSummary = ({ summary }) => {
  // Don't show anything if we don't have a summary to show
  if (!summary) return null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Your Vacation Plan</h3>
      
      {summary.destination && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-700 dark:text-gray-300">Destination</h4>
          <p className="text-xl font-semibold text-primary-600">📍 {summary.destination}</p>
        </div>
      )}
      
      {summary.travel_dates && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-700 dark:text-gray-300">Travel Dates</h4>
          <p className="text-gray-900 dark:text-gray-100">{summary.travel_dates.start} to {summary.travel_dates.end}</p>
        </div>
      )}
      
      {summary.budget_range && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-700 dark:text-gray-300">Budget</h4>
          <p className="capitalize text-gray-900 dark:text-gray-100">{summary.budget_range}</p>
        </div>
      )}
      
      {summary.travel_style && summary.travel_style.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-700 dark:text-gray-300">Travel Style</h4>
          <div className="flex flex-wrap gap-2 mt-1">
            {summary.travel_style.map((style, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm capitalize"
              >
                {style}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {summary.status && (
        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-300">{summary.status}</p>
        </div>
      )}
    </div>
  );
};

export default VacationSummary;