import { useEffect, useState } from 'react';

const mockEndpoints = {
  today: `${import.meta.env.BASE_URL}mock/dummy_today.json`,
  weekly: `${import.meta.env.BASE_URL}mock/dummy_7d.json`,
  monthly: `${import.meta.env.BASE_URL}mock/dummy_30d.json`
};

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${url}`);
  }
  return response.json();
};

const useMockData = () => {
  const [data, setData] = useState({ today: null, weekly: null, monthly: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const [today, weekly, monthly] = await Promise.all([
          fetchJson(mockEndpoints.today),
          fetchJson(mockEndpoints.weekly),
          fetchJson(mockEndpoints.monthly)
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
  }, []);

  return { ...data, loading, error };
};

export default useMockData;
