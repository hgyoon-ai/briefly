import { useEffect, useMemo, useState } from 'react';

const buildUrls = (dataset) => {
  const base = import.meta.env.BASE_URL;
  return {
    index: `${base}market/${dataset}/index.json`,
    month: (month) => `${base}market/${dataset}/${month}.json`
  };
};

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${url}`);
  }
  return response.json();
};

const sortEvents = (events) =>
  events
    .slice()
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

const useSecuritiesAIMarket = (dataset = 'securities-ai') => {
  const [index, setIndex] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const urls = buildUrls(dataset);

    const load = async () => {
      try {
        if (isMounted) {
          setLoading(true);
        }
        const indexData = await fetchJson(urls.index);
        const months = Array.isArray(indexData.months) ? indexData.months : [];
        const monthsToLoad = months.slice(0, 2);
        const monthPayloads = await Promise.all(
          monthsToLoad.map((month) => fetchJson(urls.month(month)))
        );
        const nextEvents = sortEvents(
          monthPayloads.flatMap((payload) => payload.events || [])
        );

        if (isMounted) {
          setIndex(indexData);
          setEvents(nextEvents);
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
  }, [dataset]);

  const lastUpdated = useMemo(() => {
    if (index?.lastUpdated) {
      return new Date(index.lastUpdated);
    }
    if (events.length > 0) {
      return new Date(events[0].date);
    }
    return null;
  }, [index, events]);

  return {
    index,
    events,
    loading,
    error,
    lastUpdated
  };
};

export default useSecuritiesAIMarket;
