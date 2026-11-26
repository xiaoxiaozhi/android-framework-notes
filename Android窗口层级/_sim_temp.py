# Faithful port of HierarchyBuilder.build() passes 1+2 (AOSP12 r32)
MAXL = 36  # getMaxWindowLayer()
APPLICATION_LAYER = 2
TASK, IME, TOKENS = 1, 2, 0

def rng(a, b):
    return set(range(a, b + 1))

# Feature layer sets, derived exactly per Feature.Builder semantics
WM   = rng(0, 31)
HDC  = (rng(0, MAXL) - {24, 25, 17, 19}) - {36}
OHBP = {0, 1}
OH   = (rng(0, MAXL) - {24, 25}) - {36}
FM   = (rng(0, MAXL) - {32, 15, 16, 28, 24, 25}) - {36}
IMEf = {15, 16}
FEATURES = [('WM', WM), ('HDC', HDC), ('OHBP', OHBP), ('OH', OH), ('FM', FM), ('IME', IMEf)]

def type_of_layer(L):
    if L == APPLICATION_LAYER:
        return TASK
    if L in (15, 16):
        return IME
    return TOKENS

class PA:
    def __init__(self, feature, minL, parent, existing=None, skip=False, tag=''):
        self.feature = feature
        self.minL = minL
        self.maxL = minL
        self.parent = parent
        self.children = []
        self.existing = existing
        self.skipTokens = skip
        self.tag = tag
    def label(self):
        return 'root' if self.feature is None else '%s(%d~%d)' % (self.feature, self.minL, self.maxL)

root = PA(None, 0, None)
area = [root] * (MAXL + 1)

# Pass 1: features
for name, S in FEATURES:
    fa = None
    for L in range(MAXL + 1):
        if L in S:
            if fa is None or fa.parent is not area[L]:
                fa = PA(name, L, area[L])
                fa.parent.children.append(fa)
            area[L] = fa
        else:
            fa = None

# Pass 2: leaves
leaf = None
leafType = TOKENS
events = []
tdaNodes = []
for L in range(MAXL + 1):
    t = type_of_layer(L)
    if leaf is None or leaf.parent is not area[L] or t != leafType:
        leaf = PA(None, L, area[L])
        leaf.parent.children.append(leaf)
        leafType = t
        if t == TASK:
            tda = PA(None, L, area[L], existing='DefaultTaskDisplayArea', tag='TDA')
            area[L].children.append(tda)
            tdaNodes.append(tda)
            leaf.skipTokens = True
            act = 'NEW placeholder(skip) + TDA sibling'
        elif t == IME:
            leaf.existing = 'ImeContainer'
            leaf.skipTokens = True
            leaf.tag = 'IME'
            act = 'NEW IME leaf (mExisting=ImeContainer)'
        else:
            act = 'NEW Tokens'
    else:
        act = 'reuse, extend maxLayer'
    leaf.maxL = L
    events.append((L, t, act, leaf, area[L]))

def cmax(n):
    for c in n.children:
        cmax(c)
    if n.children:
        n.maxL = max(n.minL, max(c.maxL for c in n.children))
cmax(root)

tname = {TASK: 'TASK', IME: 'IME', TOKENS: 'TOKENS'}
print('=== pass-2 per-layer events ===')
for L, t, act, n, par in events:
    print('L%2d %-6s %-38s leaf=%d:%d parent=%s' % (L, tname[t], act, n.minL, n.maxL, par.label()))

def da_name(c):
    if c.feature is not None:
        return '%s:%d:%d' % (c.feature, c.minL, c.maxL)
    if c.existing is not None:
        return c.existing + (' (leaf %d:%d)' % (c.minL, c.maxL) if c.tag == 'IME' else '')
    if c.skipTokens:
        return None
    return 'Leaf:%d:%d' % (c.minL, c.maxL)

print()
print('=== instantiated tree (sorted by minLayer, placeholders skipped) ===')
def inst(n, d=0):
    for c in sorted(n.children, key=lambda x: x.minL):
        nm = da_name(c)
        if nm is None:
            print('  ' * d + '[skip TASK placeholder %d:%d]' % (c.minL, c.maxL))
            continue
        print('  ' * d + nm)
        inst(c, d + 1)
inst(root)

print()
tokens_leaves = []
def collect(n):
    for c in n.children:
        if c.feature is None and c.existing is None and not c.skipTokens:
            tokens_leaves.append((c.minL, c.maxL))
        collect(c)
collect(root)
print('Tokens leaves:', ['%d:%d' % a for a in tokens_leaves])
print('count =', len(tokens_leaves))
