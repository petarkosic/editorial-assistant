const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

export function relativeTime(iso: string, now: Date = new Date()): string {
  const deltaSec = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  const abs = Math.abs(deltaSec);

  if (abs < 45) return rtf.format(deltaSec, 'second');
  if (abs < 3600) return rtf.format(Math.round(deltaSec / 60), 'minute');
  if (abs < 86400) return rtf.format(Math.round(deltaSec / 3600), 'hour');
  
  return rtf.format(Math.round(deltaSec / 86400), 'day');
}
