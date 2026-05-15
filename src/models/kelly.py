def kelly(probability, odds):

    b = odds - 1

    q = 1 - probability

    return ((b * probability) - q) / b
