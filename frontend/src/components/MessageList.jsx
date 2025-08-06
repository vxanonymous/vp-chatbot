import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Calendar, DollarSign, MapPin, Users, Clock, AlertCircle } from 'lucide-react';

// Component that makes messages look nice with formatting and icons
const RichMessage = memo(({ content }) => {
  // Make sure we got a string to work with
  if (typeof content !== 'string') {
    console.error('RichMessage received non-string content:', content);
    return (
      <div className="text-red-600">
        Error: Invalid message format. Please try again.
      </div>
    );
  }

  // Set up how we want different parts of the message to look
  const renderers = {
    // Make headers stand out
    h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
    h2: ({ children }) => <h2 className="text-lg font-semibold mt-3 mb-2">{children}</h2>,
    h3: ({ children }) => <h3 className="text-md font-semibold mt-2 mb-1">{children}</h3>,
    
    // Make lists look nice
    ul: ({ children }) => <ul className="list-disc list-inside ml-4 my-2">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-inside ml-4 my-2">{children}</ol>,
    li: ({ children }) => <li className="mb-1">{children}</li>,
    
    // Add icons to paragraphs based on what they're talking about
    p: ({ children }) => {
      // Turn the children into a string so we can check what it says
      const text = Array.isArray(children) 
        ? children.join('') 
        : String(children || '');
      
      // Add icons based on what the message is talking about
      if (text.includes('$') && /\$\d+/.test(text)) {
        // If they're talking about money, add a dollar sign icon
        return (
          <p className="mb-2">
            <DollarSign className="inline w-4 h-4 text-green-600 mr-1" />
            {children}
          </p>
        );
      }
      
      if (text.includes('📍') || text.toLowerCase().includes('location')) {
        // If they're talking about places, add a map pin icon
        return (
          <p className="mb-2">
            <MapPin className="inline w-4 h-4 text-blue-600 mr-1" />
            {children}
          </p>
        );
      }
      
      if (text.includes('📅') || text.toLowerCase().includes('date')) {
        // If they're talking about dates, add a calendar icon
        return (
          <p className="mb-2">
            <Calendar className="inline w-4 h-4 text-purple-600 mr-1" />
            {children}
          </p>
        );
      }
      
      return <p className="mb-2">{children}</p>;
    },
    
    // Make code blocks look nice
    code: ({ inline, children }) => {
      if (inline) {
        return <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">{children}</code>;
      }
      return (
        <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto my-2">
          <code className="text-sm">{children}</code>
        </pre>
      );
    },
    
    // Make links look clickable
    a: ({ href, children }) => (
      <a 
        href={href} 
        target="_blank" 
        rel="noopener noreferrer"
        className="text-primary-600 hover:text-primary-700 underline"
      >
        {children}
      </a>
    ),
    
    // Make quotes stand out
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-primary-400 pl-4 italic my-2 text-gray-700">
        {children}
      </blockquote>
    )
  };

  return (
    <ReactMarkdown 
      className="prose prose-sm max-w-none dark:prose-invert"
      components={renderers}
    >
      {content}
    </ReactMarkdown>
  );
});

RichMessage.displayName = 'RichMessage';

const MessageList = ({ messages, isLoading }) => {
  return (
    <div className="message-list" data-testid="message-list">
      {messages.map((message, index) => (
        <div
          key={`${message.timestamp}-${index}`}
          className={`flex gap-3 mb-4 ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.role === 'assistant' && (
            <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-sm">✈️</span>
            </div>
          )}
          
          <div
            className={`max-w-[70%] rounded-lg px-4 py-2 transition-colors ${
              message.role === 'user'
                ? 'bg-primary-600 text-white dark:bg-primary-700 dark:text-white'
                : message.isError
                ? 'bg-red-100 text-red-800 border border-red-200 dark:bg-red-900 dark:text-red-100 dark:border-red-700'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
            }`}
          >
            {message.isError && (
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4" />
                <span className="font-semibold">Error</span>
              </div>
            )}
            
            {message.role === 'user' ? (
              <p className="whitespace-pre-wrap">{String(message.content || '')}</p>
            ) : (
              <RichMessage content={message.content} />
            )}
            
            {message.metadata?.confidence_score !== undefined && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    Confidence: {Math.round(message.metadata.confidence_score * 100)}%
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {message.role === 'user' && (
            <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-sm">👤</span>
            </div>
          )}
        </div>
      ))}
      
      {isLoading && (
        <div className="flex gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
            <span className="text-white text-sm">✈️</span>
          </div>
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              <span className="text-sm text-gray-600 dark:text-gray-300 ml-2">Planning your perfect vacation...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(MessageList);