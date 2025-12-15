import React from 'react';

interface AmdoxLogoProps {
  className?: string;
  title?: string;
}

export function AmdoxLogo({ className, title = 'Amdox logo' }: AmdoxLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <rect x="6" y="8" width="52" height="48" rx="12" fill="#6C2DC7" />
      <path
        d="M22 22h20l6 6v14c0 3.3-2.7 6-6 6H22c-3.3 0-6-2.7-6-6V28c0-3.3 2.7-6 6-6zm4 8c-2.2 0-4 1.8-4 4v2c0 2.2 1.8 4 4 4s4-1.8 4-4v-2c0-2.2-1.8-4-4-4zm12 0c-2.2 0-4 1.8-4 4v6h4v-2h4v-4c0-2.2-1.8-4-4-4z"
        fill="#FFFFFF"
      />
    </svg>
  );
}
