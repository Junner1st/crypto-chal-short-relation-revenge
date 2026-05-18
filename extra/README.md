# Short Relation - Revenge

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




這題的 $\texttt{window} = 2^{64}$，$\texttt{item\\_limit} = 2^{127}$，按照 Short Relation 1 密度的算法，
$$
\frac{\texttt{tiem\\_limit}\cdot\texttt{window}}{p} = \frac{2^{191}}{2^{255}-19}\approx2^{-64}
$$

其實難以爆破目標 account 的 $k_2$。所以要先解出一組 bounded modular short relation，滿足

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

這裡介紹兩種作法：

## 〈法一〉　Simple LLL/CVP

[solve-simple.py](/extra/solve-simple.py) 使用 lattice reduction 找出一組可用的 bounded modular short relation。這份 solver 的目標是用簡短的 LLL/CVP 建模找到一組通常足夠使用的 $(m_1, k_1, k_2)$。

首先我們有

$$
x_1 \equiv a^{-1} \cdot (\texttt{account\\_id} \cdot \texttt{window} + k_2) \pmod p
$$

where

$$
x_1 = m_1 \cdot \texttt{window} + k_1
$$

要找到某個 $k_2$ 使得對應的 $x_1$ 落在

$$
0 \le x_1 < \texttt{item\\_limit} \cdot \texttt{window}
$$

就能拆出

$$
m_1 = \lfloor x_1 / \texttt{window} \rfloor,\quad
k_1 = x_1 \bmod \texttt{window}
$$

令

$$
\texttt{base} = a^{-1} \cdot \texttt{account\\_id} \cdot \texttt{window} \bmod p
$$

然後找

$$
x_1 = \texttt{base} + a^{-1} k_2 \pmod p
$$

這樣建構 lattice

$$
\begin{pmatrix}
a^{-1} & \texttt{item\\_limit} \\
-p & 0
\end{pmatrix}
$$

配合 LLL 和 CVP，把目標向量設在不同的 $k_2$ 區間中心附近，嘗試找出讓第二個座標對應到合法 $k_2$、第一個座標對應到短 $x_1$ 的 lattice vector。

主要攻擊流程：

1. 呼叫 $\texttt{params}$ 取得 $p$、$b$、$\texttt{window}$、$\texttt{item\\_limit}$ 和 $\texttt{account\\_id}$。
2. 由 $p$ 算出三階自同態係數 $a$。
3. 建立 congruence $a \cdot (m_1 \cdot \texttt{window} + k_1) \equiv \texttt{account\\_id} \cdot \texttt{window} + k_2 \pmod p$。
4. 將問題改寫成 $x_1 = \texttt{base} + a^{-1} \cdot k_2 \pmod p$，其中 $x_1$ 必須小於 $\texttt{item\\_limit} \cdot \texttt{window}$。
5. 建立 2 維 lattice，先做 LLL reduction，再用 CVP 對多個 $k_2$ 區間中心找 closest vector。
6. 從 closest vector 還原 $k_2$，計算 $x_1$，並檢查 $x_1$ 是否落在合法 bound 內。


這個版本依賴 `fpylll`，而且只取第一個找到的候選。如果候選剛好沒有滿足 record witness 條件，solver 不會完整搜尋其他可能解。

## 〈法二〉　floor-sum 高速解

[solve-floor-sum.py](/extra/solve-floor-sum.py) 不使用 LLL，而是把 short relation 搜索轉成「找出哪些 $k_2$ 會讓 modular linear expression 落在短區間內」的計數問題。

我們有

$$
x_1 \equiv a^{-1} \cdot (\texttt{account\\_id} \cdot \texttt{window} + k_2) \pmod p
$$

令

$$
d = a^{-1},\quad
\texttt{base} = d \cdot \texttt{account\\_id} \cdot \texttt{window} \bmod p
$$

問題變成搜尋

$$
0 \le k_2 < \texttt{window}
$$

使得

$$
\big((\texttt{base} + d k_2) \bmod p\big)
<
\texttt{item\\_limit} \cdot \texttt{window}
$$

也就是 $x_1$ 會落在非 reserved record 可以表示的範圍內。

這裡使用 floor sum 來計算一段區間中有多少個 $k_2$ 滿足：

$$
\big((\texttt{base} + d k_2) \bmod p \big)< \texttt{x\\_bound}
$$

其中

$$
\texttt{x\\_bound} = \texttt{item\\_limit} \cdot \texttt{window}
$$

計數時的技巧是把 modular 小於某個 limit 的條件寫成兩個 floor sum 的差，這樣就可以在 $O(\log p)$ 時間內計算一個區間的命中數量。接著對 $k_2$ 的範圍做二分遞迴，如果某段區間的命中數是 0 就剪枝，不是 0 就繼續切一半，直到定位出實際的 $k_2$。

主要攻擊流程：

1. 呼叫 $\texttt{params}$ 取得 $p$、$b$、$\texttt{window}$、$\texttt{item\\_limit}$ 和 $\texttt{account\\_id}$。
2. 由 $\sqrt{-3}$ 算出兩個非平凡三次單位根 $a$，也就是兩個可能的自同態係數。
3. 對每個 $a$ 設定 $d = a^{-1}$ 和 $\texttt{base} = d \cdot \texttt{account\\_id} \cdot \texttt{window} \bmod p$。
4. 用 floor sum 計算區間內有多少 $k_2$ 滿足 $(\texttt{base} + d \cdot k_2) \bmod p < \texttt{item\\_limit} \cdot \texttt{window}$。
5. 用二分遞迴定位命中的 $k_2$，就不用枚舉整個 $2^{64}$ 大小的 $\texttt{window}$。
6. 對每個命中的 $k_2$ 計算 $x_2=\texttt{account\\_id} \cdot \texttt{window} + k_2$ 和 $x_1 = dx_2 \bmod p$。

優點是不用 lattice library，也不依賴單一候選。

## FLAG

`CCCTF{f100R_5Um_g0TT4_b3_usefaahhh}`