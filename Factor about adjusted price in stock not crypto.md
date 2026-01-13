# Factor and Adjusted Price

## Basic Idea

This document explains why:

- price uses `× factor`
- amount uses `÷ factor`

---

## Example

| Time | Raw Price | Adjusted Price |
|----|----|----|
| Before | 10 | 20 |
| After | 5 | 5 |

---

## Code Example

```python
adjusted_price = raw_price * factor
