from heuristic_functions import find_moments_without_stockfish, stockfish_moments
from util import merge_intervals, transform_format

pgn_file_path = "lichess_pgn.pgn"
pgn_string = "1. d4 f5 2. h3 d6 3. g4 fxg4 4. hxg4 Bxg4 5. c4 Nf6 6. Nc3 h6 7. Qd3 Qd7 8. Qg6+ Kd8 9. Bh3 Bxh3 10. Nxh3 Qg4 11. Qd3 Nc6 12. Rg1 Qxd4 13. Qxd4 Nxd4 14. Kd1 e5 15. f4 Nc6 16. fxe5 Nxe5 17. Nf4 Ke7 18. Be3 Nxc4 19. Ng6+ Kf7 20. Nxh8+ Kg8 21. Bxh6 Kxh8 22. Bf4 Re8 23. Kc2 Kg8 24. b3 Ne3+ 25. Bxe3 Rxe3 26. Kd2 Re6 27. Raf1 Ne4+ 28. Nxe4 Rxe4 29. Kd3 Re6 30. Rc1 c6 31. e4 Be7 32. Rg4 Bf6 33. Rcg1 Kf7 34. R1g2 Re5 35. a4 Rc5 36. b4 Rc3+ 37. Kd2 Rc4 38. e5 Bxe5 39. Rxc4 d5 40. Rcg4 Bf6 41. Kd3 b6 42. Rf2 c5 43. bxc5 bxc5 44. Rf5 c4+ 45. Kc2 Ke6 46. Rgf4 g6 47. Rxf6+ Ke5 48. Rxg6 Kxf4 49. Rd6 Ke4 50. Rd8 Kd4 51. Rd7 Kc5 52. Rc7+ Kb6 53. Re7 a5 54. Re5 Kc5 55. Rh5 Kb4 56. Rh4 Kxa4 57. Kc3 Kb5 58. Rd4 a4 59. Rd1 Kc5 60. Ra1 Kb5 61. Rd1 Kc5 62. Rh1 Kb5 63. Rh5 Kc5 64. Rg5 Kd6 65. Rg2 Kc5 66. Ra2 Kb5 67. Rb2+ Kc5 68. Rd2 Kb5 69. Ra2 Ka5 70. Ra1 Kb5 71. Rd1 1/2-1/2"
engine_path = "C:/Users/Thinkpad/Desktop/Гоша/Friflex/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe"
heuristics_without_stockfish = find_moments_without_stockfish(pgn_string)
stockfish_moves = stockfish_moments(pgn_string, engine_path)
heuristics = heuristics_without_stockfish + stockfish_moves
heuristics = merge_intervals(heuristics)
print(heuristics)
print(transform_format(heuristics))
