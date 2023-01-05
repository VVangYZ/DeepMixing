import dsm_classes
import geo_classes
from typing import List
from math import sin

safe_factor = {
    'Fcc': 1.3,     # 防止中间深层搅拌桩破碎的安全系数
    'Fs': 1.5,      # 防止边坡稳定性破坏的安全系数，包括整体稳定性破坏及穿过处治区的剪切破坏
    'Fo': 1.3,      # 剪力墙抗倾覆及承载力破坏的安全系数
    'Fc': 1.3,      # 剪力墙下卧层承载力安全系数
    'Fv': 1.3,      # 剪力墙垂直平面上的抗剪安全系数
    'Fe': 1.3       # 剪力墙受土体挤压破坏的安全系数
}


class ProjectLayout:
    def __init__(self,
                 layers: List[geo_classes.GeoLayer],
                 roadbed: geo_classes.RoadBed,
                 center_dsm: dsm_classes.CenterDSM,
                 shear_dsm: dsm_classes.ShearDSM,
                 water_level: float
                 ):

        self.dsm_shear = shear_dsm
        self.dsm_center = center_dsm
        self.roadbed = roadbed
        self.layers = layers
        self.water_level = water_level
        self.ground_level = self.layers[0].level[1]

        # 判断桩长及持力层
        self.dsm_shear_bot_lv = self.ground_level - self.dsm_shear.dsm.length
        if layers[-1].level[0] > self.dsm_shear_bot_lv:
            print('桩长超过了土层范围')
            raise Exception

        for i in layers:
            if i.level[0] < self.dsm_shear_bot_lv:
                self.bearing_layer = i
                break

        # 主动土压力
        self.ha = None
        self.Pa = None
        self.Pa_dict = None

        # 被动土压力
        self.hp = None
        self.Pp = None
        self.Pp_dict = None

        # 自重
        self.xw = None
        self.W = None
        self.weight_dict = None

        # 剪力
        self.xv = None
        self.V = None
        self.V_dict = None

        # 竖向力、水压力、有效力
        self.xne = None
        self.Ne = None
        self.xn = None
        self.xu = None
        self.U = None

        # 脚趾处应力
        self.q_toe = None

        # 剪力墙承载力验算
        self.qall_dsm = None

        # 剪力墙垂直平面剪力计算
        self.tao_all = None
        self.tao_v = None

        # 挤土稳定性验算结果
        self.soil_squeeze_res = None

    def get_settlement(self, m_soil):
        """
        规范 Step 5，计算沉降量
        :param m_soil:
        :return:
        """
        self.dsm_center.dsm.cal_modulus()
        m_comp = self.dsm_center.replacement_ratio * self.dsm_center.dsm.Edm
        m_comp += (1 - self.dsm_center.replacement_ratio) * m_soil

        settlement = self.dsm_center.dsm.length * self.roadbed.total_load / m_comp

        return settlement

    def get_active_earth_pressure(self):
        """
        计算搅拌桩左侧主动土压力
        :return:
        """
        dsm_bot_lv = self.ground_level - self.dsm_shear.dsm.length

        active_p = {
            'embankment': [self.roadbed.Pa, self.dsm_shear.dsm.length + self.roadbed.height / 3],
            'vehicle': [self.roadbed.Pa_vehicle, self.dsm_shear.dsm.length + self.roadbed.height / 2]
        }

        i_layer = 0
        i_depth = self.ground_level
        i_load = self.roadbed.total_load
        while True:

            if i_depth > dsm_bot_lv:
                layer_cal_height = i_depth - max(
                    dsm_bot_lv,
                    self.layers[i_layer].level[0]
                )
                self.layers[i_layer].cal_active_earth_pressure(upper_load=i_load, cal_h=layer_cal_height)

                active_p[f'{i_layer + 1}-{self.layers[i_layer].name}-rect'] = [
                    self.layers[i_layer].Pa_rect,
                    (i_depth - layer_cal_height / 2) - dsm_bot_lv
                ]

                active_p[f'{i_layer + 1}-{self.layers[i_layer].name}-tri'] = [
                    self.layers[i_layer].Pa_tri,
                    (i_depth - layer_cal_height * 2 / 3) - dsm_bot_lv
                ]

                i_layer += 1
                i_depth -= layer_cal_height
                i_load += self.layers[i_layer].material.gamma * layer_cal_height

            else:
                break

        self.Pa_dict = active_p
        self.Pa = sum([active_p[i][0] for i in active_p])
        self.ha = sum([active_p[i][0] * active_p[i][0] for i in active_p]) / self.Pa

    def get_passive_earth_pressure(self):
        """
        计算水泥搅拌桩剪力墙右侧被动土压力
        :return:
        """
        dsm_bot_lv = self.ground_level - self.dsm_shear.dsm.length
        passive_p = {}

        i_layer = 0
        i_depth = self.ground_level
        while True:
            if i_depth > dsm_bot_lv:
                layer_cal_height = i_depth - max(
                    dsm_bot_lv,
                    self.layers[i_layer].level[0]
                )

                self.layers[i_layer].cal_passive_earth_pressure(layer_cal_height)

                passive_p[f'{i_layer + 1}-{self.layers[i_layer].name}-rect'] = [
                    self.layers[i_layer].Pp_rect,
                    (i_depth - layer_cal_height / 2) - dsm_bot_lv
                ]

                passive_p[f'{i_layer + 1}-{self.layers[i_layer].name}-tri'] = [
                    self.layers[i_layer].Pp_tri,
                    (i_depth - layer_cal_height * 2 / 3) - dsm_bot_lv
                ]

                i_layer += 1
                i_depth -= layer_cal_height

            else:
                break

        self.Pp_dict = passive_p
        self.Pp = sum([passive_p[i][0] for i in passive_p])
        self.hp = sum([passive_p[i][0] * passive_p[i][0] for i in passive_p]) / self.Pp

    def get_weight(self):
        """
        计算搅拌桩底处所受重力，各层按照天然重度（不考虑搅拌桩增量）
        :return:
        """

        dsm_bot_lv = self.ground_level - self.dsm_shear.dsm.length
        weights = {
            'embankment': [self.roadbed.weight_side, self.roadbed.width_side * 2 / 3]
        }

        i_layer = 0
        i_depth = self.ground_level
        while True:
            if i_depth > dsm_bot_lv:
                layer_cal_height = i_depth - max(
                    dsm_bot_lv,
                    self.layers[i_layer].level[0]
                )

                self.layers[i_layer].cal_line_weight(layer_cal_height)

                weights[f'{i_layer + 1}-{self.layers[i_layer].name}'] = [
                    self.layers[i_layer].line_weight * self.roadbed.width_side,
                    self.roadbed.width_side / 2
                ]

                i_layer += 1
                i_depth -= layer_cal_height

            else:
                break

        self.weight_dict = weights
        self.W = sum([weights[i][0] for i in weights])
        self.xw = sum([weights[i][0] * weights[i][0] for i in weights]) / self.W

    def get_shear_force(self):
        """
        计算搅拌桩所受剪力（竖直方向），因默认左右两侧采用相同土层，估左右两侧剪力相等，竖向力等于重力
        :return:
        """

        dsm_bot_lv = self.ground_level - self.dsm_shear.dsm.length
        shear_forces = {}

        i_layer = 0
        i_depth = self.ground_level
        while True:
            if i_depth > dsm_bot_lv:
                layer_cal_height = i_depth - max(
                    dsm_bot_lv,
                    self.layers[i_layer].level[0]
                )

                self.layers[i_layer].cal_shear_force(layer_cal_height)

                shear_forces[f'{i_layer + 1}-{self.layers[i_layer].name}'] = self.layers[i_layer].V

                i_layer += 1
                i_depth -= layer_cal_height

            else:
                break

        self.V_dict = shear_forces
        self.V = sum([shear_forces[i][0] for i in shear_forces])
        self.xv = self.roadbed.width_side / 2

    def get_effective_force(self):
        """
        计算搅拌桩底有效压力信息
        :return:
        """
        water_height = self.water_level - (self.ground_level - self.dsm_shear.dsm.length)
        self.U = water_height * 9.8 * self.roadbed.width_side
        self.xu = self.roadbed.width_side / 2

        self.xn = (self.Pp * self.hp + self.W * self.xw + self.V * self.xv - self.Pa * self.ha) / self.W

        self.Ne = self.W - self.U
        self.xne = (self.W * self.xn - self.U * self.xu) / self.Ne

    def get_toe_pressure(self):
        """
        计算搅拌桩右下角压应力
        :return:
        """
        self.q_toe = self.Ne / self.roadbed.width_side * \
                     (2 * self.roadbed.weight_side / 3 * self.xn * self.dsm_shear.replacement_ratio -
                      1 / self.dsm_shear.replacement_ratio + 1)

    def get_toe_qall(self):
        pass

    def get_ground_qall(self):
        """
        规范 Step6.3，计算剪力墙下卧层强度 qall（对应安全系数 Fc）
        :return:
        """
        k0 = 1 - sin(self.bearing_layer.material.phi_m)
        sigma_v_e = self.W / self.roadbed.width_side - 9.8 * (self.water_level - self.dsm_shear_bot_lv)
        sigma_h_e = k0 * sigma_v_e

        self.qall_dsm = 2 * self.dsm_shear.dsm.Sdm * self.dsm_shear.dsm.fv(safe_factor['Fc'])

    def get_shear_inf(self):
        """
        根据6.4章，计算搅拌桩水平剪应力
        :return:
        """
        self.tao_v = self.V / self.dsm_shear.dsm.length
        self.tao_v += 3 * self.W / (4 * self.dsm_shear.dsm.length) * (1 - 3 * self.xn / (2 * self.roadbed.width_side)) ** 2

        self.tao_all = self.dsm_shear.dsm.fv['other'] * self.dsm_shear.get_c_divide_s_shear() * self.dsm_shear.dsm.Sdm / safe_factor['Fv']

    def get_soil_squeeze_result(self):
        """
        根据6.5章，计算搅拌桩剪力墙间软土挤出结果
        :return:
        """

        all_clay_layer = {}
        sigma_va_minus_vp = self.roadbed.material.gamma * self.roadbed.height + self.roadbed.vehicle_load

        for j, i in enumerate(self.layers):
            if i.level[1] > self.dsm_shear_bot_lv:
                layer_cal_height = i.level[1] - max(
                    self.dsm_shear_bot_lv,
                    i.level[0]
                )
                if type(i.material) == geo_classes.Clay:
                    all_clay_layer[f'{j + 1}-{i.name}'] = [i.material.c, layer_cal_height]
            else:
                break

        if len(all_clay_layer) == 0:
            self.soil_squeeze_res = []
        else:
            he = sum([all_clay_layer[i][1]] for i in all_clay_layer)
            cm = sum([all_clay_layer[i][0] * all_clay_layer[i][1] for i in all_clay_layer]) / he

            self.soil_squeeze_res = [
                self.dsm_shear.wall_space - self.dsm_shear.dsm.diameter,
                1 / (safe_factor['Fe'] * sigma_va_minus_vp / (2 * cm) - 2) * (1 / self.roadbed.width_side) - 1 / he
            ]


if __name__ == '__main__':
    pass














