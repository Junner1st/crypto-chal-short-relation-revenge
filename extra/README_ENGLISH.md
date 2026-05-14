# Short Relation - 2

## Challenge Design

Compared with [Φ2Sin](https://github.com/Junner1st/crypto-chal-phi-2-sin), this
challenge keeps the same curve family but changes the record parameters.

The service still works over the $j = 0$ curve:

$$
E / \mathbb{F}_p: y^2 = x^3 - 17,\quad p = 2^{255} - 19
$$

The record relation is:

$$
x = m \cdot \texttt{window} + k
$$

with:

$$
0 \le m < \texttt{item\_limit},\quad 0 \le k < \texttt{window}
$$

$$
y \equiv z^2 \pmod p,\quad (x, y) \in E(\mathbb{F}_p)
$$

The curve has a public order-3 automorphism:

$$
\phi(x, y) = (a x, y),\quad a^3 = 1,\quad a \ne 1
$$

Since scalar multiplication commutes with $\phi$, a signature on a non-reserved
account can still be transported to the reserved account.

This challenge uses `window = 2^64`, so directly enumerating the target
account's `k2` is infeasible. The intended approach is to first solve a bounded
modular short relation:

$$
a \cdot (m_1 \cdot \texttt{window} + k_1)
\equiv
\texttt{account\_id} \cdot \texttt{window} + k_2
\pmod p
$$

where:

$$
0 \le m_1 < \texttt{item\_limit},\quad 0 \le k_1, k_2 < \texttt{window}
$$

After this short relation is found, the rest of the exploit is the same
automorphism-based signature transport as in Φ2Sin.

## Exploit Process

1. Request `params` to get `p`, `b`, `window`, `item_limit`, and `account_id`.
2. Compute the automorphism coefficient `a` from $p$.
3. Build the congruence `a * (m1 * window + k1) == account_id * window + k2 (mod p)`.
4. Use LLL/CVP or equivalent lattice reduction to recover a bounded short-vector candidate `(m1, k1, k2)`.
5. Check that `x1 = m1 * window + k1` and `x2 = account_id * window + k2` satisfy `a*x1 == x2 (mod p)`.
6. Check that the corresponding curve point exists and that witness `z` satisfies `y = z^2 mod p`.
7. Ask the oracle to sign the non-reserved relation point `(x1, y)`.
8. Push the returned token forward with the automorphism, giving `(a*sx, sy)`.
9. Submit the transported token for the reserved account point `(x2, y)` to get the flag.

[solver script is here](/extra/solve.py)

## FLAG

`CCCTF{f100R_5Um_g0TT4_b3_usefaahhh}`
