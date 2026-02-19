import { X, ChevronDown } from 'lucide-react';
import { useState } from 'react';

interface FilterControlsProps {
  filters: {
    exchanges: string[];
    minSpread: number;
    blockedTokens: string[];
    minVolume: number;
  };
  onFiltersChange: (filters: any) => void;
  availableExchanges: string[];
}

const POPULAR_TOKENS = [
  'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP'
];

export function FilterControls({ filters, onFiltersChange, availableExchanges }: FilterControlsProps) {
  const [showBlockedDropdown, setShowBlockedDropdown] = useState(false);
  const [blockedTokenInput, setBlockedTokenInput] = useState('');

  const toggleExchange = (exchange: string) => {
    const newExchanges = filters.exchanges.includes(exchange)
      ? filters.exchanges.filter(e => e !== exchange)
      : [...filters.exchanges, exchange];
    onFiltersChange({ ...filters, exchanges: newExchanges });
  };

  const toggleToken = (token: string) => {
    const newTokens = filters.blockedTokens.includes(token)
      ? filters.blockedTokens.filter(t => t !== token)
      : [...filters.blockedTokens, token];
    onFiltersChange({ ...filters, blockedTokens: newTokens });
  };

  const addBlockedToken = () => {
    if (blockedTokenInput.trim() && !filters.blockedTokens.includes(blockedTokenInput.trim().toUpperCase())) {
      onFiltersChange({ 
        ...filters, 
        blockedTokens: [...filters.blockedTokens, blockedTokenInput.trim().toUpperCase()] 
      });
      setBlockedTokenInput('');
    }
  };

  const removeBlockedToken = (token: string) => {
    onFiltersChange({ 
      ...filters, 
      blockedTokens: filters.blockedTokens.filter(t => t !== token) 
    });
  };

  return (
    <div className="bg-[#252836] rounded-3xl p-6 backdrop-blur-sm bg-opacity-50 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
      {/* Exchanges */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm text-gray-400">Exchanges</label>
          <div className="flex gap-1.5">
            <button
              onClick={() => onFiltersChange({ ...filters, exchanges: [...availableExchanges] })}
              className="text-[11px] px-2 py-0.5 rounded bg-[#1a1d2e] text-gray-400 hover:text-green-400 transition"
            >
              All
            </button>
            <button
              onClick={() => onFiltersChange({ ...filters, exchanges: [] })}
              className="text-[11px] px-2 py-0.5 rounded bg-[#1a1d2e] text-gray-400 hover:text-red-400 transition"
            >
              None
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {availableExchanges.map(exchange => (
            <button
              key={exchange}
              onClick={() => toggleExchange(exchange)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                filters.exchanges.includes(exchange)
                  ? 'bg-gradient-to-r from-green-400 to-emerald-500 text-black shadow-lg shadow-green-500/30'
                  : 'bg-[#1a1d2e] text-gray-300 hover:bg-[#2a2d3e] shadow-md'
              }`}
            >
              {exchange}
            </button>
          ))}
        </div>
      </div>

      {/* Other Filters - Stacked Vertically */}
      <div className="space-y-4">
        {/* Minimal Spread */}
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Minimal Spread (%)</label>
          <input
            type="number"
            value={filters.minSpread}
            onChange={(e) => onFiltersChange({ ...filters, minSpread: parseFloat(e.target.value) || 0 })}
            className="w-full bg-[#1a1d2e] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-400 transition"
            placeholder="0.0"
            step="0.1"
            min="0"
          />
        </div>

        {/* Blocked Tokens - Input with Dropdown */}
        <div className="relative">
          <label className="text-sm text-gray-400 mb-2 block">Blocked Tokens</label>
          <div className="relative">
            <input
              type="text"
              value={blockedTokenInput}
              onChange={(e) => setBlockedTokenInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addBlockedToken()}
              onFocus={() => setShowBlockedDropdown(true)}
              onBlur={() => setTimeout(() => setShowBlockedDropdown(false), 200)}
              className="w-full bg-[#1a1d2e] border border-gray-700 rounded-lg px-3 py-2 pr-9 text-sm text-white focus:outline-none focus:border-green-400 transition"
              placeholder="Add token..."
            />
            <button
              onClick={() => setShowBlockedDropdown(!showBlockedDropdown)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {/* Dropdown showing blocked tokens */}
            {showBlockedDropdown && filters.blockedTokens.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1d2e] border border-gray-700 rounded-lg shadow-xl z-10 max-h-40 overflow-y-auto">
                {filters.blockedTokens.map(token => (
                  <div 
                    key={token}
                    className="flex items-center justify-between px-4 py-2 hover:bg-[#2a2d3e]"
                  >
                    <span className="text-red-400 text-sm">{token}</span>
                    <button
                      onClick={() => removeBlockedToken(token)}
                      className="text-gray-400 hover:text-red-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Popular tokens suggestions */}
            {showBlockedDropdown && blockedTokenInput.length === 0 && filters.blockedTokens.length === 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1d2e] border border-gray-700 rounded-lg shadow-xl z-10">
                <div className="px-4 py-2 text-xs text-gray-500 border-b border-gray-700">Popular tokens:</div>
                {POPULAR_TOKENS.map(token => (
                  <button
                    key={token}
                    onClick={() => {
                      onFiltersChange({ ...filters, blockedTokens: [...filters.blockedTokens, token] });
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-[#2a2d3e] text-sm text-gray-300"
                  >
                    {token}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Volume Filter */}
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Min Volume ($)</label>
          <input
            type="number"
            value={filters.minVolume}
            onChange={(e) => onFiltersChange({ ...filters, minVolume: parseFloat(e.target.value) || 0 })}
            className="w-full bg-[#1a1d2e] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-400 transition shadow-lg"
            placeholder="0"
            step="1000"
            min="0"
          />
        </div>
      </div>
    </div>
  );
}