import tron
import numpy as np
from datetime import datetime

# ============================================================================
# TRON FINTECH DEMO: Distributed Portfolio Risk Analysis
# The Magic: 1 decorator. That's it. Everything else is automatic.
# ============================================================================

# STEP 1: Define a remote function (mark it with @tron.remote)
@tron.remote
def analyze_portfolio_position(position_id, stock_price, volatility, weight, num_simulations=10000):
    '''
    Simulate a single position's Value at Risk (VaR).
    In real system: runs DISTRIBUTED across cluster. No config.
    '''
    np.random.seed(position_id)
    
    # Monte Carlo: simulate 10k daily returns
    daily_returns = np.random.normal(0, volatility / np.sqrt(252), num_simulations)
    future_prices = stock_price * (1 + daily_returns)
    position_pnl = (future_prices - stock_price) * weight
    
    # Calculate risk metrics
    var_95 = np.percentile(position_pnl, 5)
    var_99 = np.percentile(position_pnl, 1)
    expected_shortfall = position_pnl[position_pnl <= var_99].mean()
    
    return {
        'position_id': position_id,
        'var_95': float(var_95),
        'var_99': float(var_99),
        'es_99': float(expected_shortfall),
        'avg_price': float(future_prices.mean()),
        'worst_case': float(future_prices.min()),
        'best_case': float(future_prices.max()),
    }

# STEP 2: Create a portfolio
print('=' * 80)
print('TRON FINTECH DEMO: Institutional Portfolio Risk Analysis')
print('=' * 80)
print()
print('Portfolio: 1000 equity positions')
print('Simulation: 10,000 Monte Carlo paths per position')
print('Total operations: 10 MILLION simulations')
print()
print('WITHOUT TRON:  Spark config, map/reduce, serialization debugging...')
print('WITH TRON:     Add @tron.remote decorator. Done.')
print()
print('Creating portfolio...')

portfolio = []
np.random.seed(42)
for i in range(1000):
    portfolio.append({
        'id': i,
        'price': np.random.uniform(50, 500),
        'volatility': np.random.uniform(0.15, 0.40),
        'weight': 1000000 / 1000,
    })

print('Created {} positions'.format(len(portfolio)))
print()

# STEP 3: THE MAGIC - distributed execution
print('Submitting to TRON for DISTRIBUTED execution...')
print()

futures = []
for pos in portfolio:
    # This looks like a normal call but executes REMOTELY across cluster
    future = analyze_portfolio_position(
        position_id=pos['id'],
        stock_price=pos['price'],
        volatility=pos['volatility'],
        weight=pos['weight']
    )
    futures.append(future)

print('Submitted {} distributed tasks'.format(len(futures)))
print()

# STEP 4: Collect results
print('Collecting results from distributed cluster...')
print()

results = []
for i, future in enumerate(futures):
    result = future  # MagicFuture: just use it
    results.append(result)
    
    if (i + 1) % 200 == 0:
        print('  {}/1000 results collected...'.format(i+1))

print()
print('Received all {} results'.format(len(results)))
print()

# STEP 5: Aggregate portfolio-level risk
print('=' * 80)
print('PORTFOLIO RISK SUMMARY')
print('=' * 80)
print()

var_95_total = sum(r['var_95'] for r in results)
var_99_total = sum(r['var_99'] for r in results)
es_99_total = sum(r['es_99'] for r in results)

print('Portfolio VaR (95% confidence): ${:,.2f}'.format(var_95_total))
print('Portfolio VaR (99% confidence): ${:,.2f}'.format(var_99_total))
print('Portfolio Expected Shortfall:   ${:,.2f}'.format(es_99_total))
print()

# Show top 5 riskiest positions
print('Top 5 Riskiest Positions:')
sorted_by_risk = sorted(results, key=lambda x: x['var_99'])
for i, pos in enumerate(sorted_by_risk[:5], 1):
    print('  {}. Position {:04d}: VaR99 = ${:.2f}'.format(i, pos['position_id'], pos['var_99']))

print()
print('=' * 80)
print('THE MAGIC')
print('=' * 80)
print()
print('What you wrote:      @tron.remote + function call')
print('What happened:       10 MILLION simulations distributed')
print('Configuration:       ZERO (no Spark, no Kubernetes, no YAML)')
print('Boilerplate:         NONE')
print('Async/Parallelism:   AUTOMATIC (MagicFuture)')
print('Scaling:             UNLIMITED')
print()
print('No infrastructure. No DevOps. No deployment.')
print('Just write Python with @tron.remote')
print()
print('This is computing WITHOUT LIMITS + SIMPLICITY')
print('This is TRON.')
print()
