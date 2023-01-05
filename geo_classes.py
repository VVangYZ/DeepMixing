from math import tan, atan


class GeoMaterial:
    def __init__(self, gamma, c, phi, f0):
        self.phi = phi
        self.c = c
        self.gamma = gamma

        self.cm = self.c / f0                   # 修正的黏聚力
        self.phi_m = atan(tan(self.phi) / f0)   # 修正的总应力摩擦角


class Sand(GeoMaterial):
    def __init__(self, gamma, phi, f0):
        super().__init__(gamma, c=0, phi=phi, f0=f0)


class Clay(GeoMaterial):
    def __init__(self, gamma, c, phi, f0):
        super().__init__(gamma, c, phi, f0)


class GeoLayer:
    def __init__(self, name: str, material: GeoMaterial, top_lv, thickness):

        self.name = name
        self.material = material
        self.level = [top_lv - thickness, top_lv]
        self.thickness = thickness

        # 土层的主动土压力
        self.Pa_rect = None
        self.Pa_tri = None

        # 土层的被动土压力
        self.Pp_tri = None
        self.Pp_rect = None

        # 计算线重度
        self.line_weight = None

        # 计算剪力
        self.V = None

    def cal_active_earth_pressure(self, upper_load, cal_h=0):
        cal_h = self.thickness if cal_h == 0 else cal_h

        if type(self.material) == Clay:
            self.Pa_rect = cal_h * (upper_load - 2 * self.material.cm)
        elif type(self.material) == Sand:
            self.Pa_rect = cal_h * upper_load

        self.Pa_tri = 0.5 * self.material.gamma * cal_h ** 2

    def cal_passive_earth_pressure(self, cal_h=0):
        cal_h = self.thickness if cal_h == 0 else cal_h

        if type(self.material) == Clay:
            self.Pp_rect = cal_h * 2 * self.material.cm
        elif type(self.material) == Sand:
            self.Pp_rect = 0

        self.Pp_tri = 0.5 * self.material.gamma * cal_h ** 2

    def cal_line_weight(self, cal_h=0):
        cal_h = self.thickness if cal_h == 0 else cal_h

        self.line_weight = cal_h * self.material.gamma

    def cal_shear_force(self, cal_h=0):
        cal_h = self.thickness if cal_h == 0 else cal_h

        if type(self.material) == Clay:
            self.V = cal_h * self.material.cm
        elif type(self.material) == Sand:
            self.V = 0


class RoadBed:
    def __init__(self, material: GeoMaterial, width, height, slope, vehicle_load):
        self.vehicle_load = vehicle_load
        self.width = width
        self.slope = slope
        self.width_side = slope * height
        self.height = height
        self.material = material

        # 路基荷载计算
        self.road_bed_load = self.material.gamma * self.height
        self.total_load = self.road_bed_load + self.vehicle_load

        # 路堤主动土压力计算
        self.Ka = tan(45 - self.material.phi_m / 2) ** 2
        self.Pa = 0.5 * self.Ka * self.material.gamma * self.height ** 2
        self.Pa_vehicle = self.Ka * self.vehicle_load * self.height

        # 路基重力
        self.weight_center = self.width * self.height * self.material.gamma
        self.weight_side = 0.5 * self.width_side * self.height * self.material.gamma

    










