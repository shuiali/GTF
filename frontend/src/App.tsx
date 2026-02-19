import { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, Bell, TrendingUp, Settings } from 'lucide-react';
import { FilterControls } from './components/FilterControls';
import { SpreadsTable, Spread } from './components/SpreadsTable';
import { SpreadDetail } from './components/SpreadDetail';

// All exchanges the engine supports
const ALL_EXCHANGES = [
  'Binance', 'MEXC', 'OKX', 'Bybit', 'Gate.io', 'KuCoin', 'BitGet',
  'BingX', 'CoinEx', 'XT', 'BitMart', 'LBank', 'OurBit', 'BloFin',
];

export default function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'analytics'>('dashboard');
  const [selectedSpread, setSelectedSpread] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(true);
  const [filters, setFilters] = useState({
    exchanges: [...ALL_EXCHANGES],    // all selected by default
    minSpread: 0,
    blockedTokens: [] as string[],
    minVolume: 0,
  });

  // Data state
  const [rawSpreads, setRawSpreads] = useState<Spread[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastFetched, setLastFetched] = useState(0);
  const [availableExchanges, setAvailableExchanges] = useState<string[]>(ALL_EXCHANGES);

  // ── Fetch spreads from API ────────────────────────────────────────
  const fetchSpreads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/spreads?mode=futures-futures');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRawSpreads(data.spreads ?? []);
      setLastFetched(data.fetchedAt ?? Date.now() / 1000);
      // Merge any exchanges we see in data into the available list
      if (data.exchanges?.length) {
        setAvailableExchanges(prev => {
          const merged = new Set([...prev, ...data.exchanges]);
          return Array.from(merged).sort();
        });
      }
      return data.spreads?.length ?? 0;
    } catch (err) {
      console.error('Failed to fetch spreads:', err);
      return -1; // signal error
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-fetch on mount, then poll every 5s until data arrives
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      const count = await fetchSpreads();
      // If no data yet (backend is still fetching from exchanges), retry in 5s
      if (!cancelled && count === 0) {
        timer = setTimeout(poll, 5000);
      }
    };

    poll();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [fetchSpreads]);

  // ── Client-side filtering ─────────────────────────────────────────
  const filteredSpreads = useMemo(() => {
    return rawSpreads.filter(s => {
      // Exchange filter: both exchanges must be selected
      if (!filters.exchanges.includes(s.buyExchange) || !filters.exchanges.includes(s.sellExchange)) {
        return false;
      }
      // Min spread
      if (filters.minSpread > 0 && s.spread < filters.minSpread) return false;
      // Min volume (use the higher of buy/sell volume)
      if (filters.minVolume > 0) {
        const vol = Math.max(s.buyVolume, s.sellVolume);
        if (vol > 0 && vol < filters.minVolume) return false;
      }
      // Blocked tokens
      if (filters.blockedTokens.length > 0) {
        const baseToken = s.token.split('/')[0].toUpperCase();
        if (filters.blockedTokens.some(bt => baseToken.includes(bt))) return false;
      }
      return true;
    });
  }, [rawSpreads, filters]);

  const handleSpreadClick = (spreadId: string) => {
    setSelectedSpread(spreadId);
    setCurrentPage('analytics');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d1e] via-[#0f1419] to-[#0d1b2f] text-white">
      {/* Top Navigation */}
      <nav className="flex items-center justify-between px-8 py-6">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-[#1a1d2e]" />
            </div>
            <span className="text-xl font-semibold font-[Hanken_Grotesk] text-[24px] not-italic font-bold">ArbitrageHub</span>
          </div>
          
          <div className="flex items-center gap-2 bg-[#2a2d3e] rounded-full p-1 shadow-xl">
            <button 
              onClick={() => setCurrentPage('dashboard')}
              className={`px-6 py-2 rounded-full text-sm font-medium shadow-lg ${
                currentPage === 'dashboard' 
                  ? 'bg-white text-[#1a1d2e]' 
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => setCurrentPage('analytics')}
              className={`px-6 py-2 rounded-full text-sm font-medium ${
                currentPage === 'analytics' 
                  ? 'bg-white text-[#1a1d2e] shadow-lg' 
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Analytics
            </button>
            <button className="px-6 py-2 text-gray-300 hover:text-white rounded-full text-sm font-medium">
              History
            </button>
            <button className="px-6 py-2 text-gray-300 hover:text-white rounded-full text-sm font-medium">
              Settings
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Settings Button for Filter Toggle */}
          <button 
            onClick={() => setShowFilters(!showFilters)}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition shadow-lg ${
              showFilters 
                ? 'bg-gradient-to-r from-green-400 to-emerald-500 text-black' 
                : 'bg-[#2a2d3e] hover:bg-[#353849]'
            }`}
          >
            <Settings className="w-5 h-5" />
          </button>
          <button className="w-10 h-10 bg-[#2a2d3e] rounded-full flex items-center justify-center hover:bg-[#353849] transition shadow-lg">
            <Search className="w-5 h-5" />
          </button>
          <button className="w-10 h-10 bg-[#2a2d3e] rounded-full flex items-center justify-center hover:bg-[#353849] transition shadow-lg">
            <Bell className="w-5 h-5" />
          </button>
          <div className="w-10 h-10 bg-gradient-to-br from-pink-400 to-purple-500 rounded-full flex items-center justify-center font-semibold shadow-xl">
            <span className="text-sm">JD</span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="px-8 pb-8">
        {currentPage === 'dashboard' ? (
          <>
            {/* Settings Container + Spreads Table Layout */}
            <div className="flex items-start gap-4">
              {/* Filter Controls - Left Side */}
              {showFilters && (
                <div className="w-80 flex-shrink-0">
                  <FilterControls
                    filters={filters}
                    onFiltersChange={setFilters}
                    availableExchanges={availableExchanges}
                  />
                </div>
              )}

              {/* Spreads Table - Right Side */}
              <div className="flex-1">
                <SpreadsTable 
                  selectedSpread={selectedSpread} 
                  onSelectSpread={handleSpreadClick}
                  isMinimized={false}
                  spreads={filteredSpreads}
                  loading={loading}
                  onRefresh={fetchSpreads}
                  lastFetched={lastFetched}
                />
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Analytics Page - Full Width Detail View */}
            {selectedSpread ? (
              <SpreadDetail 
                spreadId={selectedSpread} 
                onClose={() => setSelectedSpread(null)}
              />
            ) : (
              <div className="text-center text-gray-500 py-20">
                <p>Select a spread from the Dashboard to view analytics.</p>
                <button
                  onClick={() => setCurrentPage('dashboard')}
                  className="mt-4 px-6 py-2 rounded-xl bg-[#2a2d3e] hover:bg-[#353849] text-sm transition"
                >
                  Go to Dashboard
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}