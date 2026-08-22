import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/clerk-react";

const API_URL = import.meta.env.VITE_API_URL;

async function fetchWithToken(getToken, path) {
  const token = await getToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

/** Boolean map of all feature flags, e.g. { enable_chat_sharing: true } */
export function useFlags() {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["featureFlags"],
    queryFn: () => fetchWithToken(getToken, "/api/flags"),
    staleTime: 60_000,
  });
}

/** if/else helper for components:
 *  if (useFeatureFlag("enable_chat_sharing")) { ... } else { ... }
 */
export function useFeatureFlag(name) {
  const { data, isLoading } = useFlags();
  return { enabled: !!data?.[name], isLoading };
}

/** Whether the signed-in user is an admin (drives /admin nav visibility). */
export function useIsAdmin() {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["adminSession"],
    queryFn: () => fetchWithToken(getToken, "/api/admin/session"),
    staleTime: 5 * 60_000,
  });
}
