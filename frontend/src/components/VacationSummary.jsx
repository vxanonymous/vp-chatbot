import React from 'react';

const VacationSummary = ({ summary, showMap = false }) => {
  if (!summary) return null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Your Vacation Plan</h3>
      </div>
      
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
      
      {(summary.budget_amount || summary.budget_range) && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-700 dark:text-gray-300">Budget</h4>
          <p className="text-gray-900 dark:text-gray-100 font-semibold">
            {summary.budget_amount || (typeof summary.budget_range === 'string'
              ? summary.budget_range.charAt(0).toUpperCase() + summary.budget_range.slice(1)
              : summary.budget_range)}
          </p>
          {summary.budget_amount && summary.budget_range && (
            <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
              {summary.budget_range} range
            </p>
          )}
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