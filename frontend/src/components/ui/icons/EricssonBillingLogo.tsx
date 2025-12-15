import React from 'react';

interface EricssonBillingLogoProps {
  className?: string;
  title?: string;
}

export function EricssonBillingLogo({ className, title = 'Ericsson Billing logo' }: EricssonBillingLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <rect x="6" y="8" width="52" height="48" rx="10" fill="#002561" />
      <path
        d="M20 20h24l-3 4H20v-4zm0 10h24l-3 4H20v-4zm0 10h24l-3 4H20v-4z"
        fill="#FFFFFF"
      />
    </svg>
  );
}
