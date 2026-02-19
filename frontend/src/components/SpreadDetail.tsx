import { useState } from 'react';
import { X, TrendingUp, ArrowRight, Calculator, Activity } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SpreadDetailProps {
  spreadId: string;
  onClose: () => void;
}

// Mock chart data
const generateChartData = () => {
  const data = [];
  const now = Date.now();
  for (let i = 20; i >= 0; i--) {
    data.push({
      time: new Date(now - i * 5 * 60 * 1000).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      spread: 1.2 + Math.random() * 0.6,
      buyPrice: 43200 + Math.random() * 100,
      sellPrice: 43800 + Math.random() * 100,
    });
  }
  return data;
};

const CHART_DATA = generateChartData();

export function SpreadDetail({ spreadId, onClose }: SpreadDetailProps) {
  const [investAmount, setInvestAmount] = useState(10000);
  const [leverage, setLeverage] = useState(1);
  const [buyExchange, setBuyExchange] = useState('Binance');
  const [sellExchange, setSellExchange] = useState('Coinbase');
  const [tokenSymbol, setTokenSymbol] = useState('BTC');

  // Mock spread data
  const spread = {
    token: 'BTC/USDT',
    buyExchange: buyExchange,
    sellExchange: sellExchange,
    buyPrice: 43250.50,
    sellPrice: 43890.25,
    spread: 1.48,
    exitSpread: 1.32,
    volume: 2450000,
    funding: 0.01,
  };

  const tokenName = tokenSymbol;
  const spreadValue = spread.sellPrice - spread.buyPrice;
  const profit = (investAmount / spread.buyPrice) * spreadValue * leverage;
  const profitPercent = ((spreadValue / spread.buyPrice) * 100 * leverage);
  const fees = investAmount * 0.002; // 0.2% fees
  const netProfit = profit - fees;

  const exchanges = ['Binance', 'Coinbase', 'Kraken', 'Bybit', 'OKX', 'KuCoin'];

  return (
    <div className="space-y-4">
      {/* Top Row: Spread History Chart (Left) + Realtime Info (Right) */}
      <div className="grid grid-cols-[1fr_135px] gap-4">
        {/* Spread History Chart - 90-95% width */}
        <div className="bg-[#252836] rounded-3xl p-6 backdrop-blur-sm bg-opacity-50 shadow-[0_8px_32px_rgba(0,0,0,0.5)] h-full flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-base">Spread History</h3>
            <div className="flex items-center gap-2">
              <button className="px-3 py-1.5 text-xs bg-gradient-to-r from-green-400 to-emerald-500 text-black rounded-lg font-medium shadow-lg shadow-green-500/30">
                1H
              </button>
              <button className="px-3 py-1.5 text-xs bg-[#1a1d2e] text-gray-300 rounded-lg hover:bg-[#2a2d3e] shadow-md">
                4H
              </button>
              <button className="px-3 py-1.5 text-xs bg-[#1a1d2e] text-gray-300 rounded-lg hover:bg-[#2a2d3e] shadow-md">
                1D
              </button>
              <button className="px-3 py-1.5 text-xs bg-[#1a1d2e] text-gray-300 rounded-lg hover:bg-[#2a2d3e] shadow-md">
                1W
              </button>
            </div>
          </div>
          
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CHART_DATA}>
                <defs>
                  <linearGradient id="colorSpread" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="time" 
                  stroke="#9ca3af" 
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#9ca3af" 
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  domain={[0.8, 2.0]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1d2e',
                    border: '1px solid #374151',
                    borderRadius: '12px',
                    color: '#fff'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="spread" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  fill="url(#colorSpread)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Realtime Spread Info - Apple Minimalist Design */}
        <div className="bg-[rgb(37,40,54)] rounded-3xl p-4 backdrop-blur-xl bg-opacity-95 shadow-2xl border border-white/5 flex flex-col h-full">
          {/* Token Name - Editable Input */}
          <div className="mb-4 text-center">
            <input
              type="text"
              value={tokenSymbol}
              onChange={(e) => setTokenSymbol(e.target.value.toUpperCase())}
              className="w-full text-xl font-semibold tracking-tight text-white/95 bg-transparent border-0 focus:outline-none text-center"
              maxLength={6}
            />
          </div>

          {/* Positions Stack */}
          <div className="space-y-2.5 mb-4">
            {/* LONG Position */}
            <div className="space-y-2 text-center">
              <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider">Long</div>
              <select
                value={buyExchange}
                onChange={(e) => setBuyExchange(e.target.value)}
                className="w-full bg-white/5 border-0 rounded-xl px-3 py-2 text-xs text-white font-medium focus:outline-none focus:bg-white/10 transition-all appearance-none cursor-pointer text-center"
              >
                {exchanges.map(ex => (
                  <option key={ex} value={ex} className="bg-[#2c2c2e] text-white">{ex}</option>
                ))}
              </select>
              <div className="text-base font-semibold text-green-400 tracking-tight">
                ${(spread.buyPrice / 1000).toFixed(2)}K
              </div>
            </div>

            {/* Minimal Divider */}
            <div className="flex items-center justify-center py-1">
              <div className="w-8 h-px bg-white/10"></div>
            </div>

            {/* SHORT Position */}
            <div className="space-y-2 text-center">
              <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider">Short</div>
              <select
                value={sellExchange}
                onChange={(e) => setSellExchange(e.target.value)}
                className="w-full bg-white/5 border-0 rounded-xl px-3 py-2 text-xs text-white font-medium focus:outline-none focus:bg-white/10 transition-all appearance-none cursor-pointer text-center"
              >
                {exchanges.map(ex => (
                  <option key={ex} value={ex} className="bg-[#2c2c2e] text-white">{ex}</option>
                ))}
              </select>
              <div className="text-base font-semibold text-red-400 tracking-tight">
                ${(spread.sellPrice / 1000).toFixed(2)}K
              </div>
            </div>
          </div>

          {/* Spreads - Centered and Organized */}
          <div className="space-y-2.5 mt-auto">
            {/* Entry Spread */}
            <div className="bg-green-500/10 backdrop-blur-sm rounded-xl p-4 border border-green-500/20">
              <div className="flex flex-col items-center justify-center gap-1.5">
                <span className="text-[10px] font-medium text-green-400/80 uppercase tracking-wide">Entry</span>
                <span className="text-2xl font-bold text-green-400 text-[22px]">+{spread.spread}%</span>
              </div>
            </div>
            
            {/* Exit Spread */}
            <div className="bg-red-500/10 backdrop-blur-sm rounded-xl p-4 border border-red-500/20">
              <div className="flex flex-col items-center justify-center gap-1.5">
                <span className="text-[10px] font-medium text-red-400/80 uppercase tracking-wide">Exit</span>
                <span className="text-2xl font-bold text-red-400 text-[22px]">+{spread.exitSpread}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Calculator (50%) + Position Details (50%) */}
      <div className="grid grid-cols-2 gap-4">
        {/* Spread Calculator */}
        <div className="bg-[#252836] rounded-3xl p-4 backdrop-blur-sm bg-opacity-50 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <h3 className="font-semibold text-base mb-4 flex items-center gap-2">
            <Calculator className="w-5 h-5" />
            Spread Calculator
          </h3>
          
          <div className="space-y-4 mb-5">
            {/* Row 1: Investment Amount & Leverage */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Investment Amount ($)</label>
                <input
                  type="number"
                  value={investAmount}
                  onChange={(e) => setInvestAmount(parseFloat(e.target.value) || 0)}
                  className="w-full bg-[#1a1d2e] border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-green-400 transition shadow-lg"
                  placeholder="10000"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Leverage</label>
                <select
                  value={leverage}
                  onChange={(e) => setLeverage(parseFloat(e.target.value))}
                  className="w-full bg-[#1a1d2e] border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-green-400 transition appearance-none cursor-pointer"
                >
                  <option value={1}>1x</option>
                  <option value={2}>2x</option>
                  <option value={3}>3x</option>
                  <option value={5}>5x</option>
                  <option value={10}>10x</option>
                </select>
              </div>
            </div>

            {/* Row 2: Desired Spread & Funding Rate */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Desired Spread (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={spread.spread}
                  onChange={(e) => {
                    const newSpread = parseFloat(e.target.value) || 0;
                    // This will update the local state - note: spread is from props/mock data
                  }}
                  className="w-full bg-[#1a1d2e] border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-green-400 transition shadow-lg"
                  placeholder="1.48"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Funding Rate (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={(spread.funding * 100).toFixed(2)}
                  onChange={(e) => {
                    const newFunding = parseFloat(e.target.value) || 0;
                    // This will update the local state
                  }}
                  className="w-full bg-[#1a1d2e] border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-green-400 transition shadow-lg"
                  placeholder="0.01"
                />
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="bg-[#1a1d2e] rounded-2xl p-4 space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Gross Profit</span>
              <span className="text-green-400 font-semibold">${profit.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Trading Fees (0.2%)</span>
              <span className="text-red-400 font-semibold">-${fees.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Funding Rate Impact</span>
              <span className="text-yellow-400 font-semibold">{spread.funding > 0 ? '+' : ''}${(investAmount * spread.funding).toFixed(2)}</span>
            </div>
            <div className="border-t border-gray-700 pt-3 flex justify-between items-center">
              <span className="font-semibold text-base">Net Profit</span>
              <div className="text-right">
                <div className="text-green-400 font-bold text-base">${netProfit.toFixed(2)}</div>
                <div className="text-green-400/70 text-xs">({profitPercent.toFixed(2)}%)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Position Details */}
        <div className="bg-[#252836] rounded-3xl p-4 backdrop-blur-sm bg-opacity-50 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Position Details
          </h3>
          
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-[#1a1d2e] rounded-xl p-3 shadow-lg">
              <div className="text-xs text-gray-400 mb-1">Buy Position ({spread.buyExchange})</div>
              <div className="text-sm font-bold mb-1">{(investAmount / spread.buyPrice).toFixed(6)} {tokenName}</div>
              <div className="text-xs text-gray-400">@ ${spread.buyPrice.toLocaleString()}</div>
            </div>
            
            <div className="bg-[#1a1d2e] rounded-xl p-3 shadow-lg">
              <div className="text-xs text-gray-400 mb-1">Sell Position ({spread.sellExchange})</div>
              <div className="text-sm font-bold mb-1">{(investAmount / spread.buyPrice).toFixed(6)} {tokenName}</div>
              <div className="text-xs text-gray-400">@ ${spread.sellPrice.toLocaleString()}</div>
            </div>
            
            <div className="bg-[#1a1d2e] rounded-xl p-3 shadow-lg">
              <div className="text-xs text-gray-400 mb-1">Total Capital Required</div>
              <div className="text-sm font-bold">${(investAmount * 2).toLocaleString()}</div>
              <div className="text-xs text-gray-400">Including both positions</div>
            </div>
            
            <div className="bg-[#1a1d2e] rounded-xl p-3 shadow-lg">
              <div className="text-xs text-gray-400 mb-1">Risk Level</div>
              <div className="text-sm font-bold text-yellow-400">Medium</div>
              <div className="text-xs text-gray-400">Based on volatility</div>
            </div>
          </div>

          <button className="w-full bg-gradient-to-r from-green-400 to-emerald-500 text-black font-semibold py-3 rounded-xl hover:opacity-90 transition text-sm">
            Execute Arbitrage
          </button>
        </div>
      </div>
    </div>
  );
}