import { useEffect, useState } from 'react';

const buildEndpoint = () => `${import.meta.env.BASE_URL}developer/daily.json`;

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${url}`);
  }
  return response.json();
};

const useDeveloperRadar = () => {
  const [daily, setDaily] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const url = buildEndpoint();

    const load = async () => {
      try {
        if (isMounted) {
          setLoading(true);
        }
        const data = await fetchJson(url);
        if (isMounted) {
          setDaily(data);
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

  return { daily, loading, error };
};

export default useDeveloperRadar;
