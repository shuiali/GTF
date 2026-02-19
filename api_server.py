"""
FastAPI server that exposes the spread-finding engine to the frontend.
Run with: uvicorn api_server:app --reload --port 8080
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import List, Dict, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from exchanges.funding_rates import FundingRateManager
from utils.config_loader import ConfigLoader

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Shared state ─────────────────────────────────────────────────────
manager: FundingRateManager = None          # initialized on startup
config: ConfigLoader = None

cached_spreads: List[Dict] = []
last_fetch_time: float = 0
CACHE_TTL_SECONDS = 30                      # avoid hammering exchanges
is_fetching: bool = False                   # prevent concurrent fetches

# ── Lifespan ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager, config
    config = ConfigLoader()
    manager = FundingRateManager()
    logger.info("FundingRateManager ready – API server starting")
    # Kick off a background fetch immediately so data is ready soon
    asyncio.create_task(_background_fetch())
    yield
    logger.info("API server shutting down")


async def _background_fetch():
    """Fetch spread data in the background so the first API call has data."""
    global cached_spreads, last_fetch_time, is_fetching
    if is_fetching:
        return
    is_fetching = True
    try:
        logger.info("Background fetch started – querying all exchanges...")
        raw = await manager.get_cross_market_spreads(mode="futures-futures")
        cached_spreads = raw
        last_fetch_time = time.time()
        logger.info(f"Background fetch complete – {len(raw)} spreads cached")
    except Exception as e:
        logger.error(f"Background fetch failed: {e}", exc_info=True)
    finally:
        is_fetching = False

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(title="ArbitrageHub API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Response models ──────────────────────────────────────────────────
class SpreadItem(BaseModel):
    id: str
    token: str
    buyExchange: str
    sellExchange: str
    buyPrice: float
    sellPrice: float
    spread: float
    buyVolume: float
    sellVolume: float
    status: str
    funding: float
    timeActive: str

class SpreadsResponse(BaseModel):
    spreads: List[SpreadItem]
    exchanges: List[str]
    fetchedAt: float
    count: int

class ExchangeListResponse(BaseModel):
    exchanges: List[str]

# ── Helpers ──────────────────────────────────────────────────────────
def _format_spread(raw: Dict, idx: int) -> SpreadItem:
    """Convert a raw spread dict from FundingRateManager into a front-end friendly shape."""
    symbol = raw.get("symbol", "UNKNOWN")
    token = symbol.replace("USDT", "/USDT") if "USDT" in symbol else symbol

    # Determine buy/sell exchange names (field names differ across modes)
    buy_exchange = raw.get("lowest_exchange") or raw.get("buy_exchange", "?")
    sell_exchange = raw.get("highest_exchange") or raw.get("sell_exchange", "?")

    buy_price = raw.get("buy_ask") or raw.get("lowest_price", 0)
    sell_price = raw.get("sell_bid") or raw.get("highest_price", 0)

    buy_volume = raw.get("buy_volume", 0)
    sell_volume = raw.get("sell_volume", 0)
    # If volumes are inf (meaning unknown), send 0
    if buy_volume == float('inf'):
        buy_volume = 0
    if sell_volume == float('inf'):
        sell_volume = 0

    spread_pct = raw.get("spread_percentage", 0)

    return SpreadItem(
        id=str(idx),
        token=token,
        buyExchange=buy_exchange,
        sellExchange=sell_exchange,
        buyPrice=round(buy_price, 8),
        sellPrice=round(sell_price, 8),
        spread=round(spread_pct, 4),
        buyVolume=round(buy_volume, 2),
        sellVolume=round(sell_volume, 2),
        status="active",
        funding=0.0,
        timeActive="—",
    )

# ── Routes ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Quick health check — also reports whether data is ready."""
    return {
        "status": "ok",
        "spreads_cached": len(cached_spreads),
        "last_fetch": last_fetch_time,
        "is_fetching": is_fetching,
    }


@app.get("/api/exchanges", response_model=ExchangeListResponse)
async def get_exchanges():
    """Return the list of all exchange names the engine knows about."""
    names = sorted(manager.exchanges.keys())
    return ExchangeListResponse(exchanges=names)


@app.get("/api/spreads", response_model=SpreadsResponse)
async def get_spreads(
    mode: str = Query("futures-futures", description="Spread mode"),
    min_spread: Optional[float] = Query(None),
    max_spread: Optional[float] = Query(None),
):
    """
    Return current spread opportunities.
    If cache is stale, kick off a background refresh and return whatever we have.
    This ensures the endpoint NEVER blocks for 30+ seconds.
    """
    global cached_spreads, last_fetch_time

    now = time.time()
    need_refresh = (now - last_fetch_time) > CACHE_TTL_SECONDS

    if need_refresh and not is_fetching:
        # Start refresh in background — don't block the response
        asyncio.create_task(_background_fetch())

    # Format whatever we have cached right now
    items = [_format_spread(s, i) for i, s in enumerate(cached_spreads)]

    # Collect unique exchange names actually appearing in the data
    seen_exchanges: set = set()
    for s in cached_spreads:
        seen_exchanges.add(s.get("lowest_exchange") or s.get("buy_exchange", ""))
        seen_exchanges.add(s.get("highest_exchange") or s.get("sell_exchange", ""))
    seen_exchanges.discard("")

    return SpreadsResponse(
        spreads=items,
        exchanges=sorted(seen_exchanges),
        fetchedAt=last_fetch_time,
        count=len(items),
    )
