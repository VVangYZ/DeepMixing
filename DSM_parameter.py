import math

# 设计假设

fc = 1.14       # fc 范围 (1, 1.48)
fr = 0.8        # 推荐值 0.8，范围 (0.65, 0.9)
fv = 0.95       # 深层混合区，参考 Table 12
fvs = 0.83      # 滑坡稳定性，参考 Table 12

# 剪力墙
e = 0.27
d = 0.92
beta = 2 * math.acos(e / d)

# 地质条件
Hdm = 3.44

# 路基
gamma_emb = 19      # 单位重量
Hemb = 7.88         # 高度
Bdm = 7.78          # 深层混合区宽度
Btoe = 0            # 扩大深层混合区宽度
B = Bdm + Btoe      # 深层混合区总宽度
qemb = gamma_emb * Hemb     # 路基荷载
qperm = 9.58        # 路基顶面永久荷载

# 岩土地层
gamma_1 = 18
gamma_2 = 16
gamma_3 = 18
gamma_4 = 20



