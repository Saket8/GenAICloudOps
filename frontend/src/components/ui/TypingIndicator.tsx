import React from 'react';

interface TypingIndicatorProps {
  show: boolean;
  message?: string;
}

export function TypingIndicator({ show, message = "AI is thinking..." }: TypingIndicatorProps) {
  if (!show) return null;

  return (
    <div className="flex justify-start mb-4 animate-fadeIn">
      {/* AI Avatar */}
      <div className="flex-shrink-0 mr-3">
        <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
          <i className="fas fa-robot text-white text-sm animate-pulse" />
          {/* Thinking pulse */}
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-amber-400 rounded-full border-2 border-white dark:border-gray-900 animate-ping" />
        </div>
      </div>

      {/* Typing Bubble */}
      <div className="max-w-xs bg-white dark:bg-gray-800 rounded-2xl rounded-tl-md px-5 py-4 shadow-lg border border-gray-100 dark:border-gray-700">
        <div className="flex items-center space-x-4">
          {/* Animated dots */}
          <div className="flex items-center space-x-1.5">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-3 h-3 rounded-full bg-gradient-to-br from-blue-400 via-indigo-500 to-purple-500"
                style={{
                  animation: 'typingBounce 1.4s infinite ease-in-out',
                  animationDelay: `${i * 0.16}s`,
                }}
              />
            ))}
          </div>

          {/* Message */}
          <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">
            {message}
          </span>
        </div>

        {/* Shimmer effect */}
        <div className="mt-3 h-2.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-transparent via-blue-200 dark:via-blue-700 to-transparent rounded-full"
            style={{
              animation: 'shimmer 1.5s infinite',
              width: '50%',
            }}
          />
        </div>
      </div>

      {/* Custom Animations */}
      <style>{`
        @keyframes typingBounce {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.6;
          }
          30% {
            transform: translateY(-8px);
            opacity: 1;
          }
        }
        
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(300%);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}