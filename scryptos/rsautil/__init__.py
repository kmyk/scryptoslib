from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from itertools import product
from sympy import Symbol, Poly, FiniteField
import random

###############################################################################
#                             Helper Functions                                #
###############################################################################
def force_zip(a,b):
  return zip(a + [None] * (max(len(b) - len(a), 0)), b + [None] * (max(len(a) - len(b)), 0))
def gcd(x,y):
  while y: x,y = y,(x%y)
  return x
def egcd(a, b):
    if a == 0:
      return (b, 0, 1)
    else:
      g, y, x = egcd(b % a, a)
      return (g, x - (b // a) * y, y)
def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
      raise Exception('modular inverse does not exist')
    else:
      return x % m
def chinese_remainder_theorem(items):
  N = reduce(lambda x,y:int(x)*y, [x[1] for x in items])
  result = 0
  for a, n in items:
    m = N/n
    d, r, s = egcd(n, m)
    if d != 1:
      raise Exception("Input not pairwise co-prime")
    result += a*s*m
  return result % N
def lcm(x,y):
  return (x*y)/gcd(x,y)
def totient(*args):
  return reduce(lambda x,y: x*(y-1), map(int, args))
def bitlength(x):
    assert x >= 0
    n = 0
    while x > 0:
        n = n+1
        x = x>>1
    return n
def nth_root(x,n):
    high = 1
    while high ** n < x:
        high *= 2
    low = high/2
    while low < high:
        mid = (low + high) // 2
        if low < mid and mid**n < x:
            low = mid
        elif high > mid and mid**n > x:
            high = mid
        else:
            return mid
    return mid + 1
def isqrt(n):
    if n < 0: raise ValueError('square root not defined for negative numbers')
    if n == 0: return 0
    a, b = divmod(bitlength(n), 2)
    x = 2**(a+b)
    while True:
        y = (x + n//x)//2
        if y >= x:
            return x
        x = y
def is_perfect_square(n):
    h = n & 0xF
    if h > 9: return -1
    if not(h == 2 or h == 3 or h == 5 or h == 6 or h == 7 or h == 8):
        t = isqrt(n)
        if t*t == n:
            return t
        else:
            return -1
    return -1
def rational_to_contfrac (x, y):
    a = x//y
    if a * y == x:
        return [a]
    else:
        pquotients = rational_to_contfrac(y, x - a * y)
        pquotients.insert(0, a)
        return pquotients
def convergents_from_contfrac(frac):    
    convs = [];
    for i in range(len(frac)):
        convs.append(contfrac_to_rational(frac[0:i]))
    return convs
def contfrac_to_rational (frac):
    if len(frac) == 0:
        return (0,1)
    elif len(frac) == 1:
        return (frac[0], 1)
    else:
        remainder = frac[1:len(frac)]
        (num, denom) = contfrac_to_rational(remainder)
        return (frac[0] * num + denom, num)
def gen_d(e, p, q):
  l = lcm(p-1, q-1)
  d = egcd(e, l)[1]
  if d < 0:
    d += l
  return d
def decrypt_pkcs1_oaep(ciphertext, rsa):
  key = PKCS1_OAEP.new(RSA.construct((rsa.n, rsa.e, rsa.d, rsa.p, rsa.q)))
  plaintext = key.decrypt(ciphertext.decode("base64"))
  return plaintext

class RSA:
  def __init__(s, e, n, **kwargs):
    s.e = e
    s.n = n
    if "p" in kwargs.keys():
      s.p = kwargs["p"]
      if "q" in kwargs.keys():
        s.q = kwargs["q"]
      else:
        s.q = s.n / p
      s.d = gen_d(s.e, s.p, s.q)
    elif "d" in kwargs.keys():
      s.d = kwargs["d"]
  def __getitem__(s, n):
    cond = {
        "e":s.e,
        "n":s.n,
        "p":s.p,
        "q":s.q,
        "d":s.d
    }
    if n in cond.keys():
      return cond[n]
  def decrypt(s, c):
    return pow(c, s.d, s.n)
  def encrypt(s, m):
    return pow(m, s.e, s.n)
  def sign(s, m):
    return pow(m, s.d, s.n)
  def verify(s, sig, m):
    return pow(sig, s.e, s.n) == m
  def has_private(s):
    return hasattr(s, "d")
  def __repr__(s):
    return "RSA %s Key(e=%d, n=%d%s)" % (s.has_private()and"Private"or"Public", s.e, s.n, ", p=%d, q=%d, d=%d" % (s.p, s.q, s.d) if s.has_private() else "")
  def export_pem(s):
    if s.has_private():
      d = RSA.construct((s.n, s.e, s.d, s.p, s.q))
    elif hasattr(s, "d"):
      d = RSA.construct((s.n, s.e, s.d))
    return d.exportKey()

###############################################################################
#                              Core Functions                                 #
###############################################################################
def load_rsa(fname, debug = False):
  rsa = RSA.importKey(open(fname).read())
  if debug:
    print "[+] Successfully Load File: %s" % fname
    if rsa.has_private():
      print "[+] This is Private Key"
      print "[+] p = %d\n[+] q = %d\n[+] d = %d\n" % (rsa.p, rsa.q, rsa.d)
    else:
      print "[+] This is Public Key"
    print "[+] e = %d\n[+] n = %d\n" % (rsa.e, rsa.n)
  if rsa.has_private():
    return RSA(rsa.e, rsa.n, p=rsa.p, q=rsa.q, d=rsa.d)
  else:
    return RSA(rsa.e, rsa.n)
def decrypt_rsa(dataset, cipherset = []):
  e = dataset[0].e
  n = dataset[0].n
  if e == len(dataset) and all([e == x["e"] for x in dataset]):
      print "[+] Hastad Broadcast Attack"
      return hastad_broadcast(dataset, cipherset)
  elif any([x.n == y.n and gcd(x.e, y.e) == 1 for x,y in product(dataset, repeat = 2)]):
    print "[+] Common Modulus Attack"
    return common_modulus(dataset, cipherset)
  elif any([x.e > 65537 ** 2 for x in dataset]):
    print "[-] Wiener's Attack"
    return wiener(dataset, cipherset)
  elif any([not (x == y or gcd(x.n, y.n) == 1) for x,y in product(dataset, repeat=2)]):
    print "[+] Found GCD!"
    for a,b in product(force_zip(dataset, cipherset), repeat=2):
      x = a[0]
      y = b[0]
      if not (x == y or gcd(x.n, y.n) == 1):
        p = gcd(x.n, y.n)
        print "x :",x,"\ny :",y
        print "p1 = p2 = gcd(n1,n2) =",p
        print "q1 =",x.n/p
        print "q2 =",y.n/p
        e = x.e
        n = x.n
        p = p
        q = x.n/p
        c = a[1]
        return RSA(e, n, p=p, q=q).decrypt(c)
        break
  elif any([(d.n%2) == 1 and len(hex(d.n).replace("ff", "")) < (len(hex(d.n)) - 5) for d in dataset]):
    print "[+] Trying Mersenne Prime Factorization..."
    for d,f in force_zip(dataset, cipherset):
      print d
      if (d.n%2) == 1 and len(hex(d.n).replace("ff", "")) < (len(hex(d.n)) - 5):
        n = d.n
        m = fact_mersenne(n)
        if not m == None:
          print "[+] p = %d, q = %d" % m
          return RSA(d.e, n, p=m[0], q=m[1])
    print "[-] Not Mersenne Prime..."
  else:
    print "[*] Unknown"

###############################################################################
#                              Sub Functions                                  #
###############################################################################
def common_modulus(dataset, cipherset):
  for r,s in product(zip(dataset, cipherset), repeat=2):
    x = r[0]
    y = s[0]
    if gcd(x.e, y.e) == 1:
      g, a, b = egcd(x.e, y.e)
      n = x.n
      if a < 0:
        i = modinv(r[1], n)
        return pow(i, -a, n) * pow(s[1], b, n) % n
      elif b < 0:
        i = modinv(s[1], n)
        return pow(r[1], a, n) * pow(i, -b, n) % n
      else:
        return pow(r[1], a, n) * pow(s[1], b, n) % n
  raise ValueError("Invalid Dataset")
def hastad_broadcast(dataset, cipherset):
  e = dataset[0].e
  if e == len(dataset) and all([e == x.e for x in dataset]):
    items = []
    for x,y in zip(dataset, cipherset):
      items.append((y, x.n))
    x = chinese_remainder_theorem(items)
    r = nth_root(x,e)
    return r
def wiener(dataset, cipherset):
  import sys
  sys.setrecursionlimit(65537)
  for x,y in zip(dataset, cipherset):
    e = x.e
    n = x.n
    frac = rational_to_contfrac(e, n)
    convergents = convergents_from_contfrac(frac)
    for (k,d) in convergents:
      if k!=0 and (e*d-1)%k == 0:
        phi = (e*d-1)//k
        s = n - phi + 1
        discr = s*s - 4*n
        if(discr>=0):
          t = is_perfect_square(discr)
          if t!=-1 and (s+t)%2==0:
            print "[+] d = %d" % d
            return pow(y, d, n)
def franklin_raiter(dataset, a, b, cipherset):
  F = FiniteField(dataset[0].n)
  x = Symbol("x")

  g1 = Poly(x**dataset[0].e - cipherset[0], domain=F)
  g2 = Poly(((a*x+b))**dataset[1].e - cipherset[1], domain=F)
  g = g1.gcd(g2).monic()
  print "[+] g = %s" % repr(g)

  m = -g.all_coeffs()[-1]
  return m

###############################################################################
#                        Factorization Functions                              #
###############################################################################
def fact_mersenne(n):
  for x in xrange(2, 65536):
    if n%(2**x-1) == 0:
      return ((2**x-1), n/(2**x-1))
  return None
def fact_fermat(n):
  x = isqrt(n) + 1
  y = isqrt(x**2-n)
  while True:
    w = x**2 - n - y**2
    if w == 0:
      break
    if w > 0:
      y += 1
    else:
      x += 1
  return (x+y, x-y)
def fact_p1(n):
  if n%2==0: return 2
  x = random.randint(1, n-1)
  y = x
  c = random.randint(1, n-1)
  g = 1
  while g==1:            
    x = ((x*x)%n+c)%n
    y = ((y*y)%n+c)%n
    y = ((y*y)%n+c)%n
    g = gcd(abs(x-y),n)
  return (g, n/g)
def fact_brent(n):
  if n%2==0: return 2
  y,c,m = random.randint(1, n-1),random.randint(1, n-1),random.randint(1, n-1)
  g,r,q = 1,1,1
  while g==1:
    x = y
    for i in range(r):
      y = ((y*y)%n+c)%n
    k = 0
    while k<r and g==1:
      ys = y
      for i in range(min(m,r-k)):
        y = ((y*y)%n+c)%n
        q = q*(abs(x-y))%n
      g = gcd(q,n)
      k = k + m
    r = r*2
  if g==n:
    while True:
      ys = ((ys*ys)%n+c)%n
      g = gcd(abs(x-ys),n)
      if g>1: break
  return (g, n/g)
