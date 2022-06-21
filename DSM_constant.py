import numpy as np

# 1. 安全系数 (根据 Deep mixing for Embankment and Foundation Support)

F_cc = 1.3  # 防止中间深层搅拌桩破碎的安全系数
F_s = 1.5  # 防止边坡稳定性破坏的安全系数
F_0 = 1.3  # 剪力墙抗倾覆及承载力破坏的安全系数
F_c = 1.3  # 剪力墙下卧层承载力安全系数
F_v = 1.3  # 剪力墙垂直平面上抗剪安全系数
F_e = 1.3  # 剪力墙受土体挤压破坏的安全系数


# 3. 确定水泥搅拌桩属性

def get_fc(t):
    """
    计算剪力墙处置区承载力安全系数，时间 t 的无侧限抗压强度与28天时的无侧限抗压强度之比
    根据 Deep mixing for Embankment and Foundation Support 计算
    :param t: 养护时间（天）
    :return: 剪力墙处置区承载力安全系数（无量纲）
    """
    return 0.187 * np.log(t) + 0.375


def get_S_dm(fc, q_dm_spce=0.862, fr=0.8):
    """
    计算水泥搅拌桩处置区的抗剪强度
    :param fc: 剪力墙处置区承载力安全系数（可通过get_fc函数获取）
    :param q_dm_spce: 水泥土28天无侧限抗压强度（kPa），一般为 0.52~1.03，测试项目为 0.862
    :param fr: 无侧限峰值强度与受限大应变之间的差异系数，通常在 0.65~0.9，路基建议 0.8
    :return: 水泥搅拌桩处置区的抗剪强度（kPa）
    """
    return 0.5 * fr * fc * q_dm_spce


# 4. 确定水泥搅拌桩布置方案
## 4.2 确定中心桩置换率

def get_min_a_s_center(qemb, qperm, S_dm, fv):
    """
    计算最小中心桩置换率
    :type qemb: 路基荷载（kPa）
    :param qperm: 路基顶面永久荷载（kPa）
    :param S_dm:水泥搅拌桩处置区抗剪强度（kPa，可通过 get_S_dm 函数获取）
    :param fv: 参考 Table 12 获取
    :return: 确定最小中心桩置换率，设计指南建议控制在 0.2~0.4,测试项目为 0.2
    """
    q = qemb + qperm
    return F_cc * q / (2 * S_dm * fv)


## 4.3 确定剪力墙面积置换率

def get_c_s_shear(e, d, a_s_shear=0.25):
    """
    确定剪力墙面积置换率
    :param e: 桩重叠距离（m）
    :param d: 桩直径（m）
    :param a_s_shear: 暂时不知道是啥***
    :return: 剪力墙面积置换率
    """
    beta = 2 * np.arccos(1 - e / d)
    c_s_shear = 2 * a_s_shear * np.sin(beta) / (np.pi - beta) + np.sin(beta)
    return c_s_shear


# 5. 沉降分析

def get_H_dm1(Msoil_1, a_s_center, E_dm):
    M_comp1 = a_s_center * E_dm + (1 - a_s_center) * Msoil_1
    return M_comp1

# 6 稳定性分析

def get_S_dm_wall():
    pass
































