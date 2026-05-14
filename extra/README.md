# Short Relation - 2

## 題目設計

服務在 $j = 0$ 曲線上運作：

$$
E / \mathbb{F}_p: y^2 = x^3 - 17,\quad p = 2^{255} - 19
$$

record relation 為：

$$
x = m \cdot \texttt{window} + k
$$

並且需要滿足：

$$
0 \le m < \texttt{item\\_limit},\quad 0 \le k < \texttt{window}
$$

$$
y \equiv z^2 \pmod p,\quad (x, y) \in E(\mathbb{F}_p)
$$

曲線上有公開的三階自同態：

$$
\phi(x, y) = (a x, y),\quad a^3 = 1,\quad a \ne 1
$$

因為純量乘法會和 $\phi$ 交換，所以非 reserved account 上的簽章仍然可以被搬運到 reserved account 上。

這題的 `window = 2^64`，不能直接枚舉目標 account 的 `k2`。預期作法是先解出一組 bounded modular short relation：

$$
a \cdot (m_1 \cdot \texttt{window} + k_1)
\equiv
\texttt{account\\_id} \cdot \texttt{window} + k_2
\pmod p
$$

其中：

$$
0 \le m_1 < \texttt{item\\_limit},\quad 0 \le k_1, k_2 < \texttt{window}
$$

找到這組短關係後，後半段就和 Φ2Sin 一樣，利用自同態搬運簽章。

## 攻擊流程

1. 呼叫 `params` 取得 `p`、`b`、`window`、`item_limit` 和 `account_id`。
2. 由 $p$ 算出三階自同態係數 `a`。
3. 建立 congruence `a * (m1 * window + k1) == account_id * window + k2 (mod p)`。
4. 用 LLL/CVP 或等價的 lattice reduction 方法，找出滿足 bound 的短向量候選 `(m1, k1, k2)`。
5. 檢查 `x1 = m1 * window + k1` 和 `x2 = account_id * window + k2` 是否滿足 `a*x1 == x2 (mod p)`。
6. 檢查對應曲線點是否存在，並確認 witness `z` 讓 `y = z^2 mod p`。
7. 請 oracle 對非 reserved 的 relation point `(x1, y)` 簽章。
8. 對回傳 token 套用自同態，得到 `(a*sx, sy)`。
9. 把搬運後的 token 送去驗證 reserved account 的點 `(x2, y)`，取得 flag。

[簡單 solver script](/extra/solve-simple.py) 以及 [faster solve script](/extra/solve-floor-sum.py).


## FLAG

`CCCTF{f100R_5Um_g0TT4_b3_usefaahhh}`