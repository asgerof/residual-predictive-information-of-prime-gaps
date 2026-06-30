# Formal B1 Wheel-First-Hit Baseline Algorithm

This note gives a manuscript-ready replacement for Section 3.2, "Wheel-first-hit baseline \(B_1(y)\)." It is written to match the implementation in `experiments/rpi_b1_u1.py`, especially the `WheelFirstHit` class.

## Replacement text for Section 3.2

### 3.2 Wheel-first-hit baseline \(B_1(y)\)

The wheel-corrected baseline \(B_1(y)\) incorporates congruence constraints modulo the product of all primes up to a declared cutoff \(y\):
\[
W_y=\prod_{q\leq y}q,
\qquad
\varphi_y=\varphi(W_y).
\]
Let
\[
\mathcal U_y=\{u\in\{0,1,\ldots,W_y-1\}:\gcd(u,W_y)=1\}
\]
be the reduced residue classes modulo \(W_y\). For a current prime \(p\), write
\[
r=p\bmod W_y.
\]
The one-period wheel-admissible offsets are the sorted values
\[
D_y(r)=\operatorname{sort}\{d(u,r):u\in\mathcal U_y\},
\]
where
\[
d(u,r)=
\begin{cases}
(u-r)\bmod W_y, & (u-r)\bmod W_y\neq 0,\\
W_y, & (u-r)\bmod W_y=0.
\end{cases}
\]
Thus \(D_y(r)\subseteq\{1,\ldots,W_y\}\) and \(|D_y(r)|=\varphi_y\). An offset \(m>0\) is admissible at \(p\) if and only if
\[
\gcd(p+m,W_y)=1.
\]
Offsets failing this condition receive probability zero under \(B_1(y)\).

For \(m>0\), define the number of wheel-admissible offsets up to \(m\) by
\[
C_y(p,m)=
\left\lfloor\frac{m}{W_y}\right\rfloor\varphi_y
+
\#\{d\in D_y(p\bmod W_y):d\leq m\bmod W_y\},
\]
with the convention that \(C_y(p,m)=0\) for \(m\leq 0\). This is the implementation's admissible-rank counter. Equivalently, the \(k\)-th admissible offset is
\[
a_y(p,k)=
\left\lfloor\frac{k-1}{\varphi_y}\right\rfloor W_y
+d_{((k-1)\bmod \varphi_y)+1},
\]
where \(d_1<\cdots<d_{\varphi_y}\) are the elements of \(D_y(p\bmod W_y)\).

The baseline assumes a geometric first-hit law on this ordered admissible sequence. The conditional success probability among admissible positions is
\[
\theta_y(p)=
\operatorname{clip}\left(
\frac{W_y}{\varphi_y\log p},\,10^{-12},\,1-10^{-12}
\right),
\]
where `clip` truncates the value into the displayed interval. This calibration uses only the current scale \(p\), the declared wheel modulus \(W_y\), and \(\varphi(W_y)\); it does not use future gaps, primality tests of candidate offsets, or target-window fitting.

For an admissible offset \(m\), let
\[
k_y(p,m)=C_y(p,m).
\]
The wheel-first-hit probability assigned to the exact next gap \(g=m\) is
\[
B_{1,y}(g=m\mid p)=
(1-\theta_y(p))^{k_y(p,m)-1}\theta_y(p),
\qquad \gcd(p+m,W_y)=1.
\]
For non-admissible offsets,
\[
B_{1,y}(g=m\mid p)=0,
\qquad \gcd(p+m,W_y)>1.
\]
The normalization follows from the geometric series over the ordered admissible offsets:
\[
\sum_{k=1}^{\infty}(1-\theta_y(p))^{k-1}\theta_y(p)=1.
\]
Thus \(B_1(y)\) is a proper online distribution over positive offsets once the finite wheel and current prime \(p\) have been declared.

The headline experiments use \(B_1(11)\). In that case,
\[
W=2\cdot3\cdot5\cdot7\cdot11=2310,
\qquad
\varphi(W)=480.
\]
Therefore the model treats the next prime as the first success in the ordered sequence of offsets that are coprime to \(2310\), using the local hit probability
\[
\theta_{11}(p)=
\operatorname{clip}\left(
\frac{2310}{480\log p},\,10^{-12},\,1-10^{-12}
\right).
\]

For the bucket-residual experiment, the baseline exact-gap distribution also induces a bucket distribution. Let bucket edges be
\[
0=e_0<e_1<\cdots<e_J=\infty,
\]
and assign gap \(g\) at prime \(p\) to bucket \(b\) when
\[
e_b\leq \frac{g}{\log p}<e_{b+1}.
\]
The corresponding baseline bucket mass is
\[
B_{1,y}^{\mathrm{bucket}}(b\mid p)
=
\sum_{m:\,e_b\leq m/\log p<e_{b+1}} B_{1,y}(g=m\mid p).
\]
In the implementation this sum is evaluated by admissible-rank counts. If
\[
\ell_b(p)=\max\{1,\lceil e_b\log p\rceil\},
\qquad
u_b(p)=\lceil e_{b+1}\log p\rceil-1,
\]
then, for a finite upper edge,
\[
B_{1,y}^{\mathrm{bucket}}(b\mid p)
=(1-\theta_y(p))^{C_y(p,\ell_b(p)-1)}
\left[1-(1-\theta_y(p))^{C_y(p,\nu_b(p))-C_y(p,\ell_b(p)-1)}\right],
\]
with mass zero if \(\nu_b(p)<\ell_b(p)\). For the final infinite bucket, the mass is
\[
(1-\theta_y(p))^{C_y(p,\ell_b(p)-1)}.
\]
These bucket masses partition unity and define the baseline expert used in the bucket-residual mixture.

The role of \(B_1(y)\) is deliberately limited. It removes the elementary finite-wheel congruence obstruction before a residual learner is credited with predictive gain. It is not a full Hardy--Littlewood model, not a tuple-corrected baseline, and not a global analytic model of prime intensity. The empirical claim beyond \(B_1(11)\) should therefore be read as a claim beyond this explicit wheel-first-hit baseline, not beyond all possible arithmetic null models.

## Implementation traceability

The corresponding implementation is:

- `WheelFirstHit.__init__`: builds \(W_y\), the reduced residue classes, and \(\varphi(W_y)\).
- `WheelFirstHit.theta`: computes \(\theta_y(p)=W_y/(\varphi(W_y)\log p)\), clipped into \([10^{-12},1-10^{-12}]\).
- `WheelFirstHit.offsets_for_residue`: builds the sorted one-period admissible offsets \(D_y(r)\).
- `WheelFirstHit.admissible_count_leq`: computes \(C_y(p,m)\).
- `WheelFirstHit.kth_admissible_offset`: computes \(a_y(p,k)\).
- `WheelFirstHit.sample_gap`: samples the geometric first-hit rank and maps it to an admissible offset.
- `WheelFirstHit.log2_prob_gap`: evaluates the exact-gap log probability for admissible gaps.
- `WheelFirstHit.bucket_mass`: evaluates the induced bucket probability mass used by the residual bucket model.
