from scryptos.math.FiniteField import FiniteField
from scryptos.math.arithmetic import *
import sys
sys.setrecursionlimit(65537)

class EllipticCurve:
  def __init__(s, a, b, p, ring=FiniteField):
    s.ring = ring
    s.p = p
    s.a = ring(a, p)
    s.b = ring(b, p)
    if s.determinant() == 0:
      raise Exception("Invalid params of a, b(not smooth!)")

  def isoncurve(s, x, y):
    return s.ring(x**3 + s.a * x + s.b, s.p) == s.ring(y**2, s.p)

  def determinant(s):
    return s.ring(-16*(4 * s.a**3 + 27 * s.b**2), s.p)

  def __repr__(s):
    return "Elliptic Curve y^2 = x^3 + %sx + %s on %s" % (s.a, s.b, s.ring)

class ECPoint:
  def __init__(s, curve, x, y):
    s.c = curve
    s.ring = s.c.ring
    s.p = s.c.p
    s.x = s.ring(x, s.p)
    s.y = s.ring(y, s.p)
    if not(s.infinity() or s.c.isoncurve(s.x, s.y)):
      raise Exception("(%d, %d) is not curve point!" % (x, y))

  def infinity(s):
    return s.x == s.y == 0

  def __add__(s, o):
    P = s
    Q = o
    if P.infinity():
      P, Q = Q, P
    if Q.infinity():
      return P

    if P == Q:
      l = (3 * P.x**2 + curve.a) * modinv(2 * P.y, s.p)
    else:
      l = (Q.y - P.y) * modinv(Q.x - P.x, s.p)

    l = s.ring(l, s.p)
    Rx = l**2 - P.x - Q.x
    Ry = l*(P.x - Rx) - P.y
    return ECPoint(s.c, Rx, Ry)

  def __sub__(s, o):
    return s + -o

  def __neg__(s):
    if s.infinity(): return ECPoint(s.c, 0, 0)
    else: return ECPoint(s.c, s.x, -s.y)

  def __mul__(s, n):
    return pow(s, n)

  def __rmul__(s, n):
    return pow(s, n)

  def __pow__(s, n):
    P = s
    res = ECPoint(s.c, 0, 0)
    if n < 0:
      n = abs(n)
      P = -P
    while n != 0:
      if n & 1 == 1:
        res += P
      P += P
      n >>= 1
    return res

  def __repr__(s):
    return "ECPoint(%s, %s) on %s" % (s.x, s.y, s.c)