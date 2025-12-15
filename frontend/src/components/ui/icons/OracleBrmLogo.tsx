import React from 'react';

interface OracleBrmLogoProps {
  className?: string;
  title?: string;
}

export function OracleBrmLogo({ className, title = 'Oracle BRM logo' }: OracleBrmLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <rect x="4" y="10" width="56" height="44" rx="10" fill="#F80000" />
      <path
        d="M16 24h32v4H16v-4zm4 12h24c2.2 0 4 1.8 4 4v6H16v-6c0-2.2 1.8-4 4-4zm8-6h8v4h-8v-4z"
        fill="#FFFFFF"
      />
    </svg>
  );
}
