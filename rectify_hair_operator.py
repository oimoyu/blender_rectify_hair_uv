bl_info = {
    "name": "Rectify Hair UV",
    "author": "Oimoyu",
    "version": (1, 0),
    "blender": (3, 2, 2),
    "location": "UV Editor > Right-Click Menu",
    "description": "make all UV island into rect",
    "category": "UV",
}

import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class


from bpy_extras import mesh_utils
import bmesh
import math


class MY_OT_uv_unwrap_operator(Operator):
    bl_idname = "oimoyu.rectify_hair_operator"
    bl_label = "Rectify Hair UV"

    def execute(self, context):
        main()
        return {'FINISHED'}

def add_button(self, context):
    self.layout.separator()
    self.layout.operator("oimoyu.rectify_hair_operator")

def register():
    register_class(MY_OT_uv_unwrap_operator)
    bpy.types.IMAGE_MT_uvs_context_menu.append(add_button)

def unregister():
    unregister_class(MY_OT_uv_unwrap_operator)
    bpy.types.IMAGE_MT_uvs_context_menu.remove(add_button)








def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    

class UV_ISLAND:
    def __init__(self, obj, poly_idx_list):
        self.poly_idx_list = poly_idx_list
        self.obj = obj
        
        self.loop_idx_list = []
        for poly_idx in self.poly_idx_list:
            polygon = self.obj.data.polygons[poly_idx]
            self.loop_idx_list += polygon.loop_indices
            
    def test(self):
        uv_layer = self.uv_layer
        
        high_loop_idx = None
        low_loop_idx = None
        loop_idx_list = self.loop_idx_list
        
        uv_coord_list = [(uv_layer.data[loop_idx].uv,loop_idx) for loop_idx in loop_idx_list]
        
        high_result = max(uv_coord_list, key=lambda x: x[0][1])
        low_result = min(uv_coord_list, key=lambda x: x[0][1])
        
        high_vertex_loop_idx = high_result[1]
        high_vertex_idx = self.obj.data.loops[high_vertex_loop_idx].vertex_index
        high_vertex_coord = self.obj.data.vertices[high_vertex_idx].co
        
        low_vertex_loop_idx = low_result[1]
        low_vertex_idx = self.obj.data.loops[low_vertex_loop_idx].vertex_index
        low_vertex_coord = self.obj.data.vertices[low_vertex_idx].co


        right_result = max(uv_coord_list, key=lambda x: x[0][0])
        left_result = min(uv_coord_list, key=lambda x: x[0][0])
        
        right_vertex_loop_idx = right_result[1]
        right_vertex_idx = self.obj.data.loops[right_vertex_loop_idx].vertex_index
        right_vertex_coord = self.obj.data.vertices[right_vertex_idx].co
        
        left_vertex_loop_idx = left_result[1]
        left_vertex_idx = self.obj.data.loops[left_vertex_loop_idx].vertex_index
        left_vertex_coord = self.obj.data.vertices[left_vertex_idx].co
        
        uv_width = right_result[0][0] - left_result[0][0]
        uv_height = high_result[0][1] - low_result[0][1]
        
        if uv_width > uv_height:
            if right_vertex_coord[2] - left_vertex_coord[2] < 0:
                self.rotate(angle=-90,pivot=(0.5,0.5))
            else:
                self.rotate(angle=90,pivot=(0.5,0.5))

        else:
            if high_vertex_coord[2] - low_vertex_coord[2] < 0:
                self.rotate(angle=180,pivot=(0.5,0.5))
        
    def rectify(self):
        uv_layer = self.uv_layer
        
        rect_polygon = self.obj.data.polygons[self.poly_idx_list[0]]
    
        rect_loop_idx_list = rect_polygon.loop_indices
        
        if len(rect_loop_idx_list) !=4:
            ShowMessageBox("Not quad mesh", "error message", 'ERROR')
            return
        
        for i in ((0,1,True),(1,2,False),(2,3,True),(0,3,False)):
            loop_idx_i = rect_loop_idx_list[i[0]]
            loop_idx_j = rect_loop_idx_list[i[1]]
            uv_data_i = uv_layer.data[loop_idx_i]
            uv_data_j = uv_layer.data[loop_idx_j]
            
            uv_i = uv_data_i.uv
            uv_j = uv_data_j.uv
            
            avg_x = (uv_i[0] + uv_j[0]) / 2
            avg_y = (uv_i[1] + uv_j[1]) / 2
            
            if i[2]:
                uv_data_i.uv = (avg_x,uv_i[1])
                uv_data_j.uv = (avg_x,uv_j[1])
            else:
                uv_data_i.uv = (uv_i[0],avg_y)
                uv_data_j.uv = (uv_j[0],avg_y)
        
#        # unwrap_follow_active_quad ----------------------------------------------------
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(self.obj.data)
        
        bm.faces.ensure_lookup_table()

        first_plygon_idx = self.poly_idx_list[0]
        first_face = bm.faces[first_plygon_idx]

        for temp in self.poly_idx_list:
            bm.faces[temp].select = True

        bm.faces.active = first_face
        
        bpy.ops.uv.follow_active_quads(mode='LENGTH_AVERAGE')
    
    
    # need to be recalculated in case change
    @property
    def rect_coord(self):
        uv_layer = self.uv_layer
        
        # search island rect 4 uv coordnate 
        min_x, min_y = 1, 1
        max_x, max_y  = 0, 0
        
        for poly_idx in self.poly_idx_list:
            polygon = self.obj.data.polygons[poly_idx]
            loop_idx_list = polygon.loop_indices

            for loop_idx in loop_idx_list:
                coordnate = uv_layer.data[loop_idx].uv
                min_x = coordnate[0] if coordnate[0] < min_x else min_x
                min_y = coordnate[1] if coordnate[1] < min_y else min_y
                max_x = coordnate[0] if coordnate[0] >= max_x else max_x
                max_y = coordnate[1] if coordnate[1] >= max_y else max_y
        
        return (min_x, min_y, max_x, max_y)
    
    @property
    def uv_layer(self):
        bpy.ops.object.mode_set(mode='OBJECT')
        uv_layer = self.obj.data.uv_layers.active
        return uv_layer
        
    def move(self,vector):
        uv_layer = self.uv_layer
        loop_idx_list = self.loop_idx_list
        
        for loop_idx in loop_idx_list:
            uv_data = uv_layer.data[loop_idx]
            uv_data.uv = (uv_data.uv[0]+vector[0],uv_data.uv[1]+vector[1])

    def scale(self,scale_x,scale_y, pivot):
        uv_layer = self.uv_layer
        loop_idx_list = self.loop_idx_list
        for loop_idx in loop_idx_list:
            uv_data = uv_layer.data[loop_idx]
            uv_data.uv = scale_vector(vector=uv_data.uv, scale_x=scale_x, scale_y=scale_y, pivot=pivot)

    def rotate(self,angle,pivot):
        uv_layer = self.uv_layer
        loop_idx_list = self.loop_idx_list
        for loop_idx in loop_idx_list:
            uv_data = uv_layer.data[loop_idx]
            uv_data.uv = rotate_vector(vector=uv_data.uv, angle=angle,pivot=pivot)


def get_island_list(obj,mesh):
    island_poly_idx_list = mesh_utils.mesh_linked_uv_islands(mesh)

    # def island
    island_list = []
    for poly_idx_list in island_poly_idx_list:
        island = UV_ISLAND(obj, poly_idx_list)
        island_list.append(island)
    
    return island_list


def scale_vector(vector, scale_x, scale_y, pivot):
    x = vector[0] - pivot[0]
    y = vector[1] - pivot[1]

    # Scale the vector with the given scale factors
    x *= scale_x
    y *= scale_y

    # Translate the vector back to its original position relative to the pivot point
    x += pivot[0]
    y += pivot[1]

    return (x, y)


def rotate_vector(vector, angle, pivot):
    angle = angle / 180 * math.pi
    x, y = vector
    pivot_x, pivot_y = pivot
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    x_prime = pivot_x + (x - pivot_x) * cos_angle - (y - pivot_y) * sin_angle
    y_prime = pivot_y + (x - pivot_x) * sin_angle + (y - pivot_y) * cos_angle
    return x_prime, y_prime


def main():
    # Get the active object
    selected_list = bpy.context.selected_objects

    if not selected_list or selected_list[-1].type != 'MESH':
        ShowMessageBox("No mesh selected!", "error message", 'ERROR')
        return

    obj = selected_list[-1]
    mesh = obj.data


    # 1.1 get island_list
    # select uv island list every item is polygon idx list
    bpy.ops.object.mode_set(mode='OBJECT') # if not in object mode mesh_linked_uv_islands raise error, do not know why
    island_list = get_island_list(obj,mesh)

    
    # 2.rectify the island
    for island in island_list:
        island.rectify()
        
    # 4.r
    for island in island_list:
        island.test()
        
    # 3.move to stack and scale
    polygon_num_list = [len(island.poly_idx_list) for island in island_list]

    polygon_num_list = list(dict.fromkeys(polygon_num_list))
    polygon_num_list.sort()

    back_num_list = polygon_num_list[:len(polygon_num_list)//2]
    front_num_list = polygon_num_list[len(polygon_num_list)//2:]

    for island in island_list:
        (min_x, min_y, max_x, max_y) = island.rect_coord
        
        width = max_x - min_x
        height = max_y - min_y
        
        scale_x = 0.125 / width
        scale_y = 0.5 / height
        
        if len(island.poly_idx_list) in front_num_list:
            island.move((-min_x,-min_y))
            island.scale(scale_x=scale_x,scale_y=scale_y, pivot=(0,0))
            
        if len(island.poly_idx_list) in back_num_list:
            island.move((-min_x+0.5,-min_y))
            island.scale(scale_x=scale_x,scale_y=scale_y, pivot=(0.5,0))
        

    ShowMessageBox(f"process {len(island_list)} island", "Done", )
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')


if __name__ == "__main__":
    register()


