import React from 'react';

interface AzureLogoProps {
  className?: string;
  title?: string;
}

export function AzureLogo({ className, title = 'Microsoft Azure logo' }: AzureLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 96 96"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <defs>
        <linearGradient id="azure-gradient-1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#114A8B" />
          <stop offset="100%" stopColor="#0669BC" />
        </linearGradient>
        <linearGradient id="azure-gradient-2" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#3CCBF4" />
          <stop offset="100%" stopColor="#2892DF" />
        </linearGradient>
      </defs>
      <path
        d="M46.09 61.75h39.85a1.88 1.88 0 0 0 1.74-2.62L66.11 15.25a3.77 3.77 0 0 0-3.49-2.38H45.38a1.88 1.88 0 0 0-1.75 2.63l4.21 11.81z"
        fill="url(#azure-gradient-1)"
      />
      <path
        d="M75.45 73.13H37.91L56.4 28.21l-12.92 33.54h22.03L46.09 83.11z"
        fill="#0078D4"
      />
      <path
        d="M46.09 61.75a3.77 3.77 0 0 1-3.49 2.38H19.47a1.88 1.88 0 0 1-1.74-2.62L32.01 29.4z"
        fill="url(#azure-gradient-2)"
      />
    </svg>
  );
}
