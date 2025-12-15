import React from 'react';

interface OciLogoProps {
  className?: string;
  title?: string;
}

export function OciLogo({ className, title = 'Oracle Cloud Infrastructure logo' }: OciLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 512 512"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <rect width="512" height="512" fill="#C74634" rx="64" />
      <path
        d="M256 96c-88.366 0-160 71.634-160 160s71.634 160 160 160 160-71.634 160-160S344.366 96 256 96zm0 272c-61.856 0-112-50.144-112-112s50.144-112 112-112 112 50.144 112 112-50.144 112-112 112z"
        fill="#FFFFFF"
      />
    </svg>
  );
}
