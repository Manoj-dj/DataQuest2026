import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getEvents, getEventDetails } from '../services/api';

export const useDisasterEvents = (limit = 50, disasterType = null) => {
  return useQuery({
    queryKey: ['events', limit, disasterType],
    queryFn: () => getEvents(limit, disasterType),
    refetchInterval: 120000, // Refetch every 2 minutes
    staleTime: 60000, // Consider data fresh for 1 minute
  });
};

export const useEventDetails = (eventId) => {
  return useQuery({
    queryKey: ['event', eventId],
    queryFn: () => getEventDetails(eventId),
    enabled: !!eventId,
  });
};

export const useRefreshEvents = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ limit, disasterType }) => {
      return getEvents(limit, disasterType);
    },
    onSuccess: (data, variables) => {
      queryClient.setQueryData(['events', variables.limit, variables.disasterType], data);
    },
  });
};
