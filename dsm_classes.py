from math import log, cos, pi, sin


def get_fv(fos, cov=0.5, pdm=0.8):
    """
    根据规范 Table12 计算fv
    :param fos: 计算破坏模式对应的安全系数（ref: Table11）
    :param cov: 搅拌桩强度变化系数，可选 0.4、0.5、0.6，默认 0.5
    :param pdm: 实际强度超过规定强度的概率，可选 0.7、0.8、0.9，默认 0.8
    :return: 对应 fv 值
    """
    row = int(10 * cov) - 4
    column = int(10 * pdm) - 7
    if fos == 1.2:
        f = [
            [0.93, 1.05, 1.25],
            [0.88, 1.02, 1.26],
            [0.83, 0.99, 1.27]
        ]
    elif fos == 1.3:
        f = [
            [0.89, 1.01, 1.19],
            [0.82, 0.95, 1.17],
            [0.75, 0.9, 1.15]
        ]
    elif fos == 1.4:
        f = [
            [0.85, 0.97, 1.14],
            [0.76, 0.89, 1.09],
            [0.69, 0.82, 1.05]
        ]
    elif fos == 1.5:
        f = [
            [0.82, 0.93, 1.1],
            [0.72, 0.83, 1.03],
            [0.63, 0.75, 0.96]
        ]
    elif fos == 1.6:
        f = [
            [0.79, 0.9, 1.06],
            [0.68, 0.79, 0.97],
            [0.58, 0.69, 0.89]
        ]
    else:
        raise Exception

    return f[row][column]


class DSM:
    def __init__(self, diameter, length, construct_method='wet'):
        self.length = length                # 水泥搅拌桩长度，m
        self.diameter = diameter            # 水泥搅拌桩直径，m
        self.construct_method = construct_method        # 水泥搅拌桩施工方法

        self.upload_time = 60       # 加载龄期（路基填筑至75%高度的天数），day
        self.qdm_spec = 0.862       # 水泥土的28天无侧限抗压强度，MPa
        self.fr = 0.8               # 无侧限峰值强度与受限大应变之间的差异系数，通常在 0.65~0.9，路基建议 0.8
        self.fv = get_fv            # 指定参数获取对应 fv

        self.fc = None              # 强度放大系数（根据加载龄期对28天强度进行放大）
        self.Sdm = None             # 处置区域的抗剪强度设计值，MPa
        self.Edm = None             # 处治区域的弹性模量，MPa
        self.cal_shear_strength()
        self.cal_modulus()

    def cal_shear_strength(self):
        """
        根据规范 Step3，计算搅拌桩抗剪强度 Sdm
        :return:
        """
        self.fc = 0.187 * log(self.upload_time) + 0.375
        self.Sdm = 1 / 2 * self.fr * self.fc * self.qdm_spec

    def cal_modulus(self):
        """
        根据规范 Step3，计算搅拌桩弹性模量，
        :return:
        """
        if self.construct_method == 'wet':
            self.Edm = 300 * self.qdm_spec
        elif self.construct_method == 'dry':
            self.Edm = 150 * self.qdm_spec


class ShearDSM:
    def __init__(self, dsm: DSM, e):
        """
        设置搅拌桩剪力墙
        :param dsm: 单根搅拌桩
        :param e: 搅拌桩重叠长度，m
        """
        self.shear_strength = None
        self.e = e
        self.dsm = dsm

        self.beta = 2 * (1 / cos(1 - self.e / self.dsm.length))     # 一半角度
        self.c = self.dsm.diameter * sin(self.beta)                 # 重叠区宽度
        self.ae = (self.beta * 2 - sin(self.beta * 2)) / 3.1416

        # 剪力墙置换率及墙间距
        self.replacement_ratio = None       # 剪力墙区域面积置换率，大于等于
        self.wall_space = None     # 待补充

    def set_replacement_ratio(self, replace_ratio=0.25):
        """
        根据规范 Step4.1，设置剪力墙区域面积置换率，应大于等于中心桩面积置换率，且介于 0.2~0.4，默认采用 0.25，同时得到剪力墙间距（和设置中心距二选一）
        :param replace_ratio:
        :return:
        """
        self.replacement_ratio = replace_ratio
        self.wall_space = pi * self.dsm.diameter * (1 - self.ae) / replace_ratio / (4 * 1 - self.e / self.dsm.diameter)

    def set_s_shear(self, s_shear):
        """
        根据规范 Step4.1，设置剪力墙各墙中心距，也能得到置换率（和直接设置面积置换率只能二选一）
        :param s_shear: 剪力墙中心距
        :return:
        """
        self.wall_space = s_shear
        self.replacement_ratio = 3.1416 * self.dsm.diameter * (1 - self.ae) / (4 * s_shear * (1 - self.e / self.dsm.diameter))

    def get_c_divide_s_shear(self):
        """
        根据规范 Step4.3，计算得到剪力墙 c/s_shear 值，一般在 0.2~0.35 之间
        :return:
        """
        c_divide_s_shear = 2 * self.replacement_ratio * sin(self.beta) / (pi - self.beta + sin(self.beta))
        return c_divide_s_shear

    def cal_shear_strength(self, fs=1.5):
        """
        根据规范 Step6.1，计算剪力墙区域 Sdm，提供其他软件计算边坡稳定性（对应安全系数 Fs=1.5）
        :param fs: 边坡稳定性安全系数 Fs，默认为 1.5
        :return:
        """
        self.shear_strength = self.dsm.fv(fs) * self.replacement_ratio * self.dsm.Sdm
        return self.shear_strength


class CenterDSM:
    def __init__(self, dsm: DSM):
        self.dsm = dsm

        self.replacement_ratio = 0.2

        self.replacement_ratio_min = None
        self.shear_strength = None
        self.s_center = None

    def cal_replacement_ratio_min(self, q_emb, fcc=1.3):
        """
        根据规范 Step4.2，计算最小中心桩置换率
        :param q_emb: 路堤及附加垂直应力（即为路堤自重+车辆）
        :param fcc: 防止中间深层搅拌桩破碎的安全系数，默认为 1.3
        :return:
        """
        self.replacement_ratio_min = fcc * q_emb / (2 * self.dsm.Sdm * self.dsm.fv(fcc))

    def set_replacement_ratio(self, replace_ratio):
        """
        根据规范 Step4.1，设置中心桩区域面积置换率，应介于 0.2~0.4，默认采用 0.2，同时设置中心桩间距
        :param replace_ratio:
        :return:
        """
        self.replacement_ratio = replace_ratio
        self.s_center = ((3.1416 * self.dsm.diameter ** 2) / replace_ratio / 4) ** 0.5

    def set_s_center(self, s_center):
        """
        根据规范 Step4.1，设置中心桩间距，同时根据桩间距计算中心桩置换率
        :param s_center: 正方形布置中心桩间距，m
        :return:
        """
        self.s_center = s_center
        self.replacement_ratio = 3.1416 * self.dsm.diameter ** 2 / (4 * s_center ** 2)

    def cal_shear_strength(self, s_soil):
        """
        根据规范 Step6.1，计算中心区 Sdm，提供其他软件计算边坡稳定性系数
        :param s_soil: 路堤中心桩周土抗剪强度，KPa
        :return: 中心桩复合抗剪强度，KPa
        """
        s1 = self.replacement_ratio * 71.8 + (1 - self.replacement_ratio) * s_soil
        self.shear_strength = max(s1, s_soil)
        return self.shear_strength




