import { useEffect, useState } from 'react';

const buildUrls = () => {
  const base = import.meta.env.BASE_URL;
  return {
    index: `${base}market/securities-ai/index.json`,
    month: (month) => `${base}market/securities-ai/${month}.json`
  };
};

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${url}`);
  }
  return response.json();
};

const useMarketAdminData = () => {
  const [index, setIndex] = useState(null);
  const [events, setEvents] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const urls = buildUrls();

    const loadIndex = async () => {
      try {
        setLoading(true);
        const indexData = await fetchJson(urls.index);
        if (!isMounted) return;
        setIndex(indexData);
        if (!selectedMonth && indexData.months?.length) {
          setSelectedMonth(indexData.months[0]);
        }
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

    loadIndex();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    const urls = buildUrls();

    if (!selectedMonth) {
      setEvents([]);
      return undefined;
    }

    const loadMonth = async () => {
      try {
        setLoading(true);
        const payload = await fetchJson(urls.month(selectedMonth));
        if (!isMounted) return;
        setEvents(payload.events || []);
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

    loadMonth();

    return () => {
      isMounted = false;
    };
  }, [selectedMonth]);

  return {
    index,
    events,
    selectedMonth,
    setSelectedMonth,
    loading,
    error
  };
};

export default useMarketAdminData;
