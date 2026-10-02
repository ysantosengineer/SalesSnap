import Link from "next/link";

type BrandProps = {
  compact?: boolean;
  href?: string;
};

export function BrandMark({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      viewBox="0 0 48 48"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="sales-snap-brand" x1="8" x2="40" y1="40" y2="8">
          <stop stopColor="#2dd4bf" />
          <stop offset="1" stopColor="#818cf8" />
        </linearGradient>
      </defs>
      <rect fill="#10182a" height="46" rx="14" stroke="#263451" width="46" x="1" y="1" />
      <path
        d="M12 31.5 19.5 24l6 4.5L36 17"
        stroke="url(#sales-snap-brand)"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="3.5"
      />
      <circle cx="12" cy="31.5" fill="#2dd4bf" r="2.5" />
      <circle cx="19.5" cy="24" fill="#50e3cb" r="2.5" />
      <circle cx="25.5" cy="28.5" fill="#6dd4d8" r="2.5" />
      <circle cx="36" cy="17" fill="#818cf8" r="3" />
    </svg>
  );
}

export function Brand({ compact = false, href = "/" }: BrandProps) {
  return (
    <Link
      aria-label="SalesSnap home"
      className="inline-flex items-center gap-3 rounded-lg text-white no-underline"
      href={href}
    >
      <BrandMark className={compact ? "h-9 w-9" : "h-11 w-11"} />
      <span className={compact ? "text-lg font-semibold tracking-tight" : "text-xl font-semibold"}>
        Sales<span className="text-teal-300">Snap</span>
      </span>
    </Link>
  );
}
