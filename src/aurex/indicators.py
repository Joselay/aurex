def ema(values, window):
    output = [float("nan")] * len(values)
    if len(values) < window:
        return output

    alpha = 2 / (window + 1)
    current = values[0]
    for index in range(1, len(values)):
        current = values[index] * alpha + current * (1 - alpha)
        if index >= window - 1:
            output[index] = current
    return output


def rsi(values, window):
    output = [float("nan")] * len(values)
    if len(values) <= window:
        return output

    average_gain = 0
    average_loss = 0
    for index in range(1, window + 1):
        change = values[index] - values[index - 1]
        average_gain += max(change, 0)
        average_loss += max(-change, 0)

    average_gain /= window
    average_loss /= window
    output[window] = _rsi_from_averages(average_gain, average_loss)

    for index in range(window + 1, len(values)):
        change = values[index] - values[index - 1]
        average_gain = (average_gain * (window - 1) + max(change, 0)) / window
        average_loss = (average_loss * (window - 1) + max(-change, 0)) / window
        output[index] = _rsi_from_averages(average_gain, average_loss)

    return output


def atr(highs, lows, closes, window):
    output = [float("nan")] * len(closes)
    if len(closes) < window:
        return output

    true_ranges = []
    for index, _close in enumerate(closes):
        if index == 0:
            true_ranges.append(highs[index] - lows[index])
            continue
        true_ranges.append(
            max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
        )

    current = sum(true_ranges[:window]) / window
    output[window - 1] = current
    for index in range(window, len(true_ranges)):
        current = (current * (window - 1) + true_ranges[index]) / window
        output[index] = current
    return output


def _rsi_from_averages(average_gain, average_loss):
    if average_loss == 0:
        return 100
    relative_strength = average_gain / average_loss
    return 100 - 100 / (1 + relative_strength)
