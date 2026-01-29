import { useEffect, useState } from 'react';

const buildEndpoints = (tab) => ({
  today: `${import.meta.env.BASE_URL}briefing/${tab}/daily.json`,
  weekly: `${import.meta.env.BASE_URL}briefing/${tab}/weekly.json`,
  monthly: `${import.meta.env.BASE_URL}briefing/${tab}/monthly.json`
});

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${url}`);
  }
  return response.json();
};

const useMockData = (tab = 'ai') => {
  const [data, setData] = useState({ today: null, weekly: null, monthly: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const endpoints = buildEndpoints(tab);

    const load = async () => {
      try {
        if (isMounted) {
          setLoading(true);
        }
        const [today, weekly, monthly] = await Promise.all([
          fetchJson(endpoints.today),
          fetchJson(endpoints.weekly),
          fetchJson(endpoints.monthly)
        ]);

        if (isMounted) {
          setData({ today, weekly, monthly });
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [tab]);

  return { ...data, loading, error };
};

export default useMockData;
