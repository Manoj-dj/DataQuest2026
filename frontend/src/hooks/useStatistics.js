import { useQuery } from '@tanstack/react-query';
import { getStatistics } from '../services/api';

export const useStatistics = () => {
  return useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
    refetchInterval: 120000, // Refetch every 2 minutes
    staleTime: 60000, // Consider data fresh for 1 minute
  });
};
