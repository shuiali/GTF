import { TrendingUp, Clock, Activity, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { useState, useMemo } from 'react';

export interface Spread {
  id: string;
  token: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  spread: number;
  buyVolume: number;
  sellVolume: number;
  status: 'active' | 'pending' | 'expired';
  funding: number;
  timeActive: string;
}

interface GroupedToken {
  token: string;
  best: Spread;
  others: Spread[];
}

interface SpreadsTableProps {
  selectedSpread: string | null;
  onSelectSpread: (id: string | null) => void;
  isMinimized: boolean;
  spreads: Spread[];
  loading: boolean;
  onRefresh: () => void;
  lastFetched: number;
}

// Format price with smart decimal handling
function formatPrice(price: number): string {
  if (price === 0) return '$0';
  if (price >= 1000) return '$' + price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price >= 1) return '$' + price.toFixed(4);
  if (price >= 0.01) return '$' + price.toFixed(6);
  return '$' + price.toFixed(8);
}

// Format volume as readable string
function formatVolume(vol: number): string {
  if (vol === 0) return '—';
  if (vol >= 1_000_000) return '$' + (vol / 1_000_000).toFixed(1) + 'M';
  if (vol >= 1_000) return '$' + (vol / 1_000).toFixed(0) + 'K';
  return '$' + vol.toFixed(0);
}

// Format seconds into human readable time
function formatTimeSince(ts: number): string {
  if (!ts) return '';
  const seconds = Math.round(Date.now() / 1000 - ts);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

function SpreadRow({ spread, onSelect }: { spread: Spread; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className="w-full grid grid-cols-[1.8fr_3fr_1.5fr_1.5fr_1.2fr_1fr_1fr_1fr] gap-4 px-8 py-3 hover:bg-white/5 transition-all items-center group"
    >
      {/* Token */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-yellow-500 flex-shrink-0 shadow-lg"></div>
        <span className="font-semibold text-lg text-white/95 tracking-tight">{spread.token.split('/')[0]}</span>
      </div>

      {/* Exchanges */}
      <div className="flex items-center justify-center gap-2 text-sm">
        <div className="flex items-center gap-1.5 justify-end flex-1">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex-shrink-0 shadow-md"></div>
          <span className="text-green-400 font-medium text-[15px]">{spread.buyExchange}</span>
        </div>
        <span className="text-white/30 px-2">→</span>
        <div className="flex items-center gap-1.5 justify-start flex-1">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex-shrink-0 shadow-md"></div>
          <span className="text-red-400 font-medium text-[15px]">{spread.sellExchange}</span>
        </div>
      </div>

      {/* Buy Price */}
      <div className="flex items-center justify-center">
        <span className="text-white/80 text-sm font-medium text-[14px]">{formatPrice(spread.buyPrice)}</span>
      </div>

      {/* Sell Price */}
      <div className="flex items-center justify-center">
        <span className="text-white/80 text-sm font-medium text-[14px]">{formatPrice(spread.sellPrice)}</span>
      </div>

      {/* Spread */}
      <div className="flex items-center justify-center">
        <div className="bg-green-500/10 px-3 py-1.5 rounded-full border border-green-500/20">
          <span className="text-green-400 font-semibold text-sm text-[14px] font-bold">
            +{spread.spread}%
          </span>
        </div>
      </div>

      {/* Volume */}
      <div className="flex items-center justify-center">
        <span className="text-white/70 text-sm font-medium text-[14px]">{formatVolume(Math.max(spread.buyVolume, spread.sellVolume))}</span>
      </div>

      {/* Funding */}
      <div className="flex items-center justify-center">
        <span className={`text-sm font-medium text-[14px] ${spread.funding >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {spread.funding >= 0 ? '+' : ''}{(spread.funding * 100).toFixed(2)}%
        </span>
      </div>

      {/* Time */}
      <div className="flex items-center justify-center">
        <span className="text-gray-500 flex items-center gap-1.5 text-xs font-medium">
          <Clock className="w-3.5 h-3.5" />
          {spread.timeActive}
        </span>
      </div>
    </button>
  );
}

function SubRow({ spread, onSelect }: { spread: Spread; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className="w-full grid grid-cols-[1.8fr_3fr_1.5fr_1.5fr_1.2fr_1fr_1fr_1fr] gap-4 px-8 py-2.5 hover:bg-white/5 transition-all items-center bg-white/[0.02]"
    >
      {/* Token - empty placeholder to keep alignment */}
      <div className="flex items-center gap-3 pl-6">
        <span className="text-sm text-gray-500">└</span>
      </div>

      {/* Exchanges */}
      <div className="flex items-center justify-center gap-2 text-sm">
        <div className="flex items-center gap-1.5 justify-end flex-1">
          <div className="w-4 h-4 rounded-full bg-gradient-to-br from-yellow-400/70 to-orange-500/70 flex-shrink-0 shadow-sm"></div>
          <span className="text-green-400/70 font-medium text-[13px]">{spread.buyExchange}</span>
        </div>
        <span className="text-white/20 px-2">→</span>
        <div className="flex items-center gap-1.5 justify-start flex-1">
          <div className="w-4 h-4 rounded-full bg-gradient-to-br from-blue-400/70 to-purple-500/70 flex-shrink-0 shadow-sm"></div>
          <span className="text-red-400/70 font-medium text-[13px]">{spread.sellExchange}</span>
        </div>
      </div>

      {/* Buy Price */}
      <div className="flex items-center justify-center">
        <span className="text-white/60 text-[13px]">{formatPrice(spread.buyPrice)}</span>
      </div>

      {/* Sell Price */}
      <div className="flex items-center justify-center">
        <span className="text-white/60 text-[13px]">{formatPrice(spread.sellPrice)}</span>
      </div>

      {/* Spread */}
      <div className="flex items-center justify-center">
        <span className="text-green-400/70 text-[13px] font-medium">
          +{spread.spread}%
        </span>
      </div>

      {/* Volume */}
      <div className="flex items-center justify-center">
        <span className="text-white/50 text-[13px]">{formatVolume(Math.max(spread.buyVolume, spread.sellVolume))}</span>
      </div>

      {/* Funding */}
      <div className="flex items-center justify-center">
        <span className={`text-[13px] ${spread.funding >= 0 ? 'text-green-400/60' : 'text-red-400/60'}`}>
          {spread.funding >= 0 ? '+' : ''}{(spread.funding * 100).toFixed(2)}%
        </span>
      </div>

      {/* Time */}
      <div className="flex items-center justify-center">
        <span className="text-gray-600 text-[11px]">{spread.timeActive}</span>
      </div>
    </button>
  );
}

export function SpreadsTable({ selectedSpread, onSelectSpread, isMinimized, spreads, loading, onRefresh, lastFetched }: SpreadsTableProps) {

  const [expandedTokens, setExpandedTokens] = useState<Set<string>>(new Set());

  // Group spreads by base token, best spread first
  const grouped: GroupedToken[] = useMemo(() => {
    const map = new Map<string, Spread[]>();
    for (const s of spreads) {
      const base = s.token.split('/')[0];
      if (!map.has(base)) map.set(base, []);
      map.get(base)!.push(s);
    }
    const result: GroupedToken[] = [];
    for (const [token, items] of map) {
      // Sort by spread descending
      items.sort((a, b) => b.spread - a.spread);
      result.push({ token, best: items[0], others: items.slice(1) });
    }
    // Sort groups by best spread descending
    result.sort((a, b) => b.best.spread - a.best.spread);
    return result;
  }, [spreads]);

  const toggleExpand = (token: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedTokens(prev => {
      const next = new Set(prev);
      if (next.has(token)) next.delete(token);
      else next.add(token);
      return next;
    });
  };

  return (
    <div className="bg-[#252836] rounded-3xl backdrop-blur-sm bg-opacity-50 overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.5)]">

      {/* Toolbar */}
      <div className="flex items-center justify-between px-8 py-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {grouped.length} token{grouped.length !== 1 ? 's' : ''} · {spreads.length} spread{spreads.length !== 1 ? 's' : ''}
          </span>
          {lastFetched > 0 && (
            <span className="text-xs text-gray-600">
              · {formatTimeSince(lastFetched)}
            </span>
          )}
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
            loading
              ? 'bg-[#1a1d2e] text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-green-400 to-emerald-500 text-black hover:opacity-90'
          }`}
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Fetching…' : 'Refresh'}
        </button>
      </div>

      {/* Table Header */}
      <div className="grid grid-cols-[1.8fr_3fr_1.5fr_1.5fr_1.2fr_1fr_1fr_1fr] gap-4 px-8 py-5 border-b border-white/10">
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Token</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Exchanges</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Buy Price</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Sell Price</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Spread</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Volume</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Funding</div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Time</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-white/5">
        {loading && spreads.length === 0 ? (
          <div className="px-8 py-16 text-center text-gray-500">
            <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-green-400" />
            <p className="text-sm">Fetching spreads from all exchanges…</p>
            <p className="text-xs text-gray-600 mt-1">The server is querying 14 exchanges — data will appear automatically</p>
          </div>
        ) : !loading && spreads.length === 0 ? (
          <div className="px-8 py-16 text-center text-gray-500">
            <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-green-400/50" />
            <p className="text-sm">Waiting for exchange data…</p>
            <p className="text-xs text-gray-600 mt-1">The backend is still collecting prices — will auto-refresh in a few seconds</p>
          </div>
        ) : (
          grouped.map(group => {
            const isExpanded = expandedTokens.has(group.token);
            const hasOthers = group.others.length > 0;
            return (
              <div key={group.token}>
                {/* Best spread row */}
                <div className="relative">
                  <SpreadRow spread={group.best} onSelect={() => onSelectSpread(group.best.id)} />
                  {/* Expand toggle chevron */}
                  {hasOthers && (
                    <button
                      onClick={(e) => toggleExpand(group.token, e)}
                      className="absolute left-2 top-1/2 -translate-y-1/2 w-5 h-5 rounded flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/10 transition"
                      title={`${group.others.length} more pair${group.others.length > 1 ? 's' : ''}`}
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  )}
                </div>
                {/* Expanded sub-rows */}
                {isExpanded && group.others.map(s => (
                  <SubRow key={s.id} spread={s} onSelect={() => onSelectSpread(s.id)} />
                ))}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}