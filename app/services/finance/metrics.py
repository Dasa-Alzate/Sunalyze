

def npv(rate, cashflows):
    total = 0.0
    for t, cf in enumerate(cashflows):
        total += cf / ((1.0 + rate) ** t)
    return total


def _npv_derivative(rate, cashflows):
    total = 0.0
    for t, cf in enumerate(cashflows):
        if t == 0:
            continue
        total += -t * cf / ((1.0 + rate) ** (t + 1))
    return total


def irr(cashflows, low=-0.9999, high=10.0, tol=1e-7, max_iter=200):
    if not cashflows or len(cashflows) < 2:
        return None

    f_low = npv(low, cashflows)
    f_high = npv(high, cashflows)
    if f_low == 0.0:
        return low
    if f_high == 0.0:
        return high
    if (f_low > 0) == (f_high > 0):
        return None

    a, b = low, high
    fa = f_low
    mid = (a + b) / 2.0
    for _ in range(max_iter):
        mid = (a + b) / 2.0
        fm = npv(mid, cashflows)
        if abs(fm) < tol or (b - a) / 2.0 < tol:
            break
        if (fm > 0) == (fa > 0):
            a, fa = mid, fm
        else:
            b = mid

    rate = mid
    for _ in range(50):
        f = npv(rate, cashflows)
        if abs(f) < tol:
            break
        d = _npv_derivative(rate, cashflows)
        if d == 0.0:
            break
        step = f / d
        candidate = rate - step
        if candidate <= low or candidate >= high:
            break
        rate = candidate

    if low < rate < high:
        return rate
    return mid


def payback_period(initial_investment, cashflows):
    pending = initial_investment
    if pending <= 0:
        return 0.0
    for t, cf in enumerate(cashflows, start=1):
        if cf <= 0:
            continue
        if cf >= pending:
            return (t - 1) + (pending / cf)
        pending -= cf
    return None
