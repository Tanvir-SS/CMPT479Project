# Synthetic source-validation fixtures

ESCAPE format: first line `n m`, then each distinct undirected edge exactly once;
vertex IDs are in `0..n-1`. These tiny graphs are authored for this project.
`expected_counts.json` uses the order in ESCAPE `getAllFour()[5:11]`:
3-star, 3-path, tailed triangle, 4-cycle, diamond, 4-clique.

Expectations were derived by hand from the identities in `docs/SOURCE_REVIEW.md`.
For example, a diamond has two degree-3 centers, six 3-edge paths, four triangle
tails, one 4-cycle, one diamond, and no clique. Adding isolated vertices to K4
must preserve all six connected counts. The edgeless graph has four vertices
(it is not a zero-vertex input). No randomness or private graph data is used.
