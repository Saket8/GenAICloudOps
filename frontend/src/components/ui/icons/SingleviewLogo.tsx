import React from 'react';

interface SingleviewLogoProps {
  className?: string;
  title?: string;
}

export function SingleviewLogo({ className, title = 'Singleview logo' }: SingleviewLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <rect x="6" y="8" width="52" height="48" rx="12" fill="#003B71" />
      <circle cx="24" cy="32" r="10" fill="#00B5E2" />
      <path d="M34 22h14v4H34zM34 30h12v4H34zM34 38h10v4H34z" fill="#FFFFFF" />
    </svg>
  );
}
