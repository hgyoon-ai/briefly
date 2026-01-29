import { useEffect, useState } from 'react';

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${url}`);
  }
  return response.json();
};

const useRunHistory = (relativePath) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const base = import.meta.env.BASE_URL;
    const url = `${base}${relativePath}`;

    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchJson(url);
        if (!isMounted) return;
        setHistory(Array.isArray(data) ? data : []);
        setError(null);
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
  }, [relativePath]);

  return { history, loading, error };
};

export default useRunHistory;
