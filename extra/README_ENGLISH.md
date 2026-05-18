# Short Relation - Revenge

## Challenge Design

The service runs on the $j = 0$ curve:

$$
E / \mathbb{F}_p: y^2 = x^3 - 17,\quad p = 2^{255} - 19
$$

The record relation is:

$$
x = m \cdot \texttt{window} + k
$$

and it must satisfy:

$$
0 \le m < \texttt{item\\_limit},\quad 0 \le k < \texttt{window}
$$

$$
y \equiv z^2 \pmod p,\quad (x, y) \in E(\mathbb{F}_p)
$$




In this challenge, $\texttt{window} = 2^{64}$ and $\texttt{item\\_limit} = 2^{127}$. According to the density calculation from Short Relation 1,
$$
\frac{\texttt{tiem\\_limit}\cdot\texttt{window}}{p} = \frac{2^{191}}{2^{255}-19}\approx2^{-64}
$$

it is actually hard to brute-force the target account's $k_2$. Therefore, we first need to solve a bounded modular short relation satisfying

$$
a \cdot (m_1 \cdot \texttt{window} + k_1)
\equiv
\texttt{account\\_id} \cdot \texttt{window} + k_2
\pmod p
$$

where

$$
0 \le m_1 < \texttt{item\\_limit},\quad 0 \le k_1, k_2 < \texttt{window}
$$

Here are two approaches:

## Solution 1: Simple LLL/CVP

[solve-simple.py](/extra/solve-simple.py) uses lattice reduction to find a usable bounded modular short relation. The goal of this solver is to use a short LLL/CVP model to find a $(m_1, k_1, k_2)$ that is usually sufficient.

First, we have

$$
x_1 \equiv a^{-1} \cdot (\texttt{account\\_id} \cdot \texttt{window} + k_2) \pmod p
$$

where

$$
x_1 = m_1 \cdot \texttt{window} + k_1
$$

If we can find some $k_2$ such that the corresponding $x_1$ lies in

$$
0 \le x_1 < \texttt{item\\_limit} \cdot \texttt{window}
$$

then we can split it into

$$
m_1 = \lfloor x_1 / \texttt{window} \rfloor,\quad
k_1 = x_1 \bmod \texttt{window}
$$

Let

$$
\texttt{base} = a^{-1} \cdot \texttt{account\\_id} \cdot \texttt{window} \bmod p
$$

then search for

$$
x_1 = \texttt{base} + a^{-1} k_2 \pmod p
$$

Build the lattice as

$$
\begin{pmatrix}
a^{-1} & \texttt{item\\_limit} \\
-p & 0
\end{pmatrix}
$$

Together with LLL and CVP, set the target vector near the centers of different $k_2$ intervals, and try to find a lattice vector whose second coordinate corresponds to a valid $k_2$ and whose first coordinate corresponds to a short $x_1$.

Exploit flow:

1. Call $\texttt{params}$ to get $p$, $b$, $\texttt{window}$, $\texttt{item\\_limit}$, and $\texttt{account\\_id}$.
2. Compute the order-3 automorphism coefficient $a$ from $p$.
3. Build the congruence $a \cdot (m_1 \cdot \texttt{window} + k_1) \equiv \texttt{account\\_id} \cdot \texttt{window} + k_2 \pmod p$.
4. Rewrite the problem as $x_1 = \texttt{base} + a^{-1} \cdot k_2 \pmod p$, where $x_1$ must be smaller than $\texttt{item\\_limit} \cdot \texttt{window}$.
5. Build a 2-dimensional lattice, run LLL reduction first, then use CVP around multiple $k_2$ interval centers to find the closest vector.
6. Recover $k_2$ from the closest vector, compute $x_1$, and check whether $x_1$ lies within the valid bound.


This version depends on `fpylll`, and only takes the first candidate it finds. If that candidate happens not to satisfy the record witness condition, the solver will not fully search the remaining possible solutions.

## Solution 2: Fast floor-sum Solver

[solve-floor-sum.py](/extra/solve-floor-sum.py) does not use LLL. Instead, it turns the short relation search into a counting problem: finding which $k_2$ values make a modular linear expression fall into a short interval.

We have

$$
x_1 \equiv a^{-1} \cdot (\texttt{account\\_id} \cdot \texttt{window} + k_2) \pmod p
$$

Let

$$
d = a^{-1},\quad
\texttt{base} = d \cdot \texttt{account\\_id} \cdot \texttt{window} \bmod p
$$

The problem becomes searching for

$$
0 \le k_2 < \texttt{window}
$$

such that

$$
\big((\texttt{base} + d k_2) \bmod p\big)
<
\texttt{item\\_limit} \cdot \texttt{window}
$$

That is, $x_1$ falls within the range representable by a non-reserved record.

Here, floor sum is used to count how many $k_2$ values in an interval satisfy:

$$
\big((\texttt{base} + d k_2) \bmod p \big)< \texttt{x\\_bound}
$$

where

$$
\texttt{x\\_bound} = \texttt{item\\_limit} \cdot \texttt{window}
$$

The counting trick is to write the condition that a modular value is less than some limit as the difference of two floor sums. This lets us count the hits in an interval in $O(\log p)$ time. Then we recursively bisect the range of $k_2$: if an interval has 0 hits, prune it; otherwise, split it in half again until the actual $k_2$ values are located.

Exploit flow:

1. Call $\texttt{params}$ to get $p$, $b$, $\texttt{window}$, $\texttt{item\\_limit}$, and $\texttt{account\\_id}$.
2. Compute the two non-trivial cube roots of unity $a$ from $\sqrt{-3}$, which are the two possible automorphism coefficients.
3. For each $a$, set $d = a^{-1}$ and $\texttt{base} = d \cdot \texttt{account\\_id} \cdot \texttt{window} \bmod p$.
4. Use floor sum to count how many $k_2$ values in an interval satisfy $(\texttt{base} + d \cdot k_2) \bmod p < \texttt{item\\_limit} \cdot \texttt{window}$.
5. Use recursive bisection to locate the hit $k_2$ values, so we do not need to enumerate the entire $\texttt{window}$ of size $2^{64}$.
6. For each hit $k_2$, compute $x_2=\texttt{account\\_id} \cdot \texttt{window} + k_2$ and $x_1 = dx_2 \bmod p$.

The advantage is that it does not need a lattice library and does not rely on a single candidate.

## FLAG

`CCCTF{f100R_5Um_g0TT4_b3_usefaahhh}`
