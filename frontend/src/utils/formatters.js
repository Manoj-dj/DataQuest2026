import { formatDistanceToNow, format } from 'date-fns';

export const formatEventTime = (eventTime) => {
  if (!eventTime) return 'Unknown';
  try {
    const date = new Date(eventTime);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return eventTime;
  }
};

export const formatFullDateTime = (eventTime) => {
  if (!eventTime) return 'Unknown';
  try {
    const date = new Date(eventTime);
    return format(date, 'PPpp');
  } catch {
    return eventTime;
  }
};

export const formatRiskScore = (score) => {
  if (!score) return 'N/A';
  return parseFloat(score).toFixed(1);
};

export const getSeverityColor = (severity) => {
  const colors = {
    Red: '#dc2626',
    Orange: '#f97316',
    Green: '#16a34a',
    Unknown: '#6b7280',
  };
  return colors[severity] || colors.Unknown;
};

export const getSeverityBadgeClass = (severity) => {
  const classes = {
    Red: 'bg-red-500/20 text-red-400 border-red-500/50',
    Orange: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    Green: 'bg-green-500/20 text-green-400 border-green-500/50',
    Unknown: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
  };
  return classes[severity] || classes.Unknown;
};

export const capitalizeFirst = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
};
