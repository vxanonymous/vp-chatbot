// Helper functions for the application

export const formatDate = (date) => {
  return new Date(date).toLocaleDateString();
};

export const truncateText = (text, maxLength) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};