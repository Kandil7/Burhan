'use client';

export function LoadingDots() {
  return (
    <div className="flex justify-center">
      <div className="flex gap-1">
        <div className="loading-dot" />
        <div className="loading-dot" />
        <div className="loading-dot" />
      </div>
    </div>
  );
}
