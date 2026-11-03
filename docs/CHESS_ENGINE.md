# Chess Engine & Move Classification Engine

This document describes the algorithms, mathematical models, and evaluation heuristics implemented in **ChessReview**.

---

## 1. Centipawn Loss Calculation

Chess engines evaluate board positions in **centipawns (cp)**, where $100\text{ cp} = 1\text{ pawn}$. 

For each ply (half-move):
1. The engine evaluates the position **before** the move is played from White's perspective: $S_{\text{before}}$.
2. The player makes a move $m$, and the engine evaluates the resulting position: $S_{\text{after}}$.
3. The raw centipawn delta is adjusted according to the side to move:

$$\Delta_{\text{raw}} = S_{\text{before}} - S_{\text{after}}$$

$$\text{cp\_loss} = \begin{cases} 
\max(0, \Delta_{\text{raw}}) & \text{if White to move} \\
\max(0, -\Delta_{\text{raw}}) & \text{if Black to move}
\end{cases}$$

To prevent extreme spikes from forced checkmate sequences, `cp_loss` is clamped to a configurable maximum (default $1000\text{ cp}$):

$$\text{cp\_loss}_{\text{capped}} = \min(\text{cp\_loss}, \text{CP\_LOSS\_CAP})$$

---

## 2. Accuracy Calculation

Player accuracy for each individual move is calculated using a linear centipawn decay model:

$$\text{Accuracy}_{\text{move}} = \max\left(0.0, \, \min\left(100.0, \, 100.0 - \frac{\text{cp\_loss}}{5}\right)\right)$$

* **0 Centipawns lost:** $100.0\%$ accuracy
* **50 Centipawns lost:** $90.0\%$ accuracy
* **100 Centipawns lost:** $80.0\%$ accuracy
* **500+ Centipawns lost:** $0.0\%$ accuracy

### Overall Game Accuracy
$$\text{Accuracy}_{\text{side}} = \frac{1}{N} \sum_{i=1}^{N} \text{Accuracy}_i$$
*(Book/Theory moves are excluded from accuracy averages so players are judged strictly on non-book decisions).*

---

## 3. Move Classification Matrix

ChessReview classifies moves into a discrete 11-tier taxonomy modeled after Chess.com's Game Review:

| Classification | Icon / Color | Criteria |
| :--- | :--- | :--- |
| **Brilliant** | :gem: Cyan | Either: (1) MultiPV CP gap between best move and 2nd best $\ge 300\text{ cp}$, OR (2) Material sacrifice ($\text{mat}_{\text{after}} < \text{mat}_{\text{before}}$) that maintains or significantly increases winning eval ($\ge +200\text{ cp}$). |
| **Great** | :star: Blue | The move matches the engine's best move in a critical position where the evaluation advantage is significant ($|S_{\text{before}}| > 200\text{ cp}$). |
| **Best** | :white_check_mark: Green | The move matches the engine's highest-scoring engine recommendation ($m = m_{\text{best}}$). |
| **Excellent** | :thumbsup: Lime | Suboptimal move, but with minimal evaluation loss: $\text{cp\_loss} \le 20\text{ cp}$. |
| **Good** | :ok_hand: Green-Yellow | Decent move maintaining the position: $20 < \text{cp\_loss} \le 50\text{ cp}$. |
| **Inaccuracy** | :warning: Yellow | Mild inaccuracy: $50 < \text{cp\_loss} \le 100\text{ cp}$. |
| **Mistake** | :orange_circle: Orange | Notable positional degradation: $100 < \text{cp\_loss} \le 300\text{ cp}$. |
| **Blunder** | :x: Red | Severe tactical failure: $\text{cp\_loss} > 300\text{ cp}$. |
| **Missed Win** | :broken_heart: Burgundy | Position was winning before the move ($S_{\text{before}} > 500\text{ cp}$), but dropped below winning threshold ($S_{\text{after}} < 200\text{ cp}$). |
| **Missed Mate** | :dart: Magenta | Forced mate was available before the move ($S_{\text{before}} = \text{Mate}(n)$), but lost after move ($S_{\text{after}} \neq \text{Mate}$). |
| **Theory** | :books: Brown | Move matches known master openings recorded in `openings.json` database. |

---

## 4. Evaluation Bar Normalization

To render an evaluation bar spanning $[-1.0, +1.0]$:
1. Forced mate scores: $+1.0$ for White mate, $-1.0$ for Black mate.
2. Centipawn scores: Clamped to $[-1000, +1000]$ and divided by $1000$:

$$\text{Eval}_{\text{bar}} = \frac{\max(-1000, \, \min(1000, \, \text{cp}))}{1000.0}$$

