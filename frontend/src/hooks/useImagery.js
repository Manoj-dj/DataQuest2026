import { useQuery } from '@tanstack/react-query';
import { getEventImagery, analyzeImagery } from '../services/api';

export const useEventImagery = (eventId) => {
  return useQuery({
    queryKey: ['imagery', eventId],
    queryFn: () => getEventImagery(eventId),
    enabled: !!eventId,
    staleTime: 300000, // 5 minutes
  });
};

export const useImageryAnalysis = (imageUrl, context = null, enabled = false) => {
  return useQuery({
    queryKey: ['imagery-analysis', imageUrl, context],
    queryFn: () => analyzeImagery(imageUrl, context),
    enabled: enabled && !!imageUrl,
    staleTime: 600000, // 10 minutes
  });
};
