""" Part of the YABEE rev 12.0
"""

import bpy, os, sys, shutil
from mathutils import *
from math import pi
import io_scene_egg.yabee_libs.tbn_generator
from io_scene_egg.yabee_libs.texture_processor import SimpleTextures, TextureBaker
from io_scene_egg.yabee_libs.utils import *
import subprocess
import imp
imp.reload(io_scene_egg.yabee_libs.texture_processor)
imp.reload(io_scene_egg.yabee_libs.tbn_generator)
imp.reload(io_scene_egg.yabee_libs.utils)


FILE_PATH = None
ANIMATIONS = None
EXPORT_UV_IMAGE_AS_TEXTURE = None
COPY_TEX_FILES = None
TEX_PATH = None
SEPARATE_ANIM_FILE = None
ANIM_ONLY = None
CALC_TBS = None
TEXTURE_PROCESSOR = None
BAKE_LAYERS = None
MERGE_ACTOR_MESH = None
APPLY_MOD = None
PVIEW = True
STRF = lambda x: '%.6f' % x

class Group:
    """
    Representation of the EGG <Group> hierarchy structure as the
    linked list "one to many".
    """
    def __init__(self, obj):
        self.object = obj #: Link to the blender's object
        self.childs = []  #: List of children (Groups)
    
    def make_hierarchy_from_list(self, obj_list):
        """ This function make <Group> hierarchy from the list of
        Blender's objects. Self.object is the top level of the created 
        hierarchy. Usually in this case self.object == None
        
        @param obj_list: tuple or lis of blender's objects.
        """
        for obj in obj_list:
            if ((obj.parent == self.object) or 
                ((self.object == None) and 
                 (str(obj.parent) not in map(str,obj_list)) and 
                 (str(obj) not in [str(ch.object) for ch in self.childs]))):
                gr = self.__class__(obj)
                self.childs.append(gr)
                gr.make_hierarchy_from_list(obj_list)
                
    def print_hierarchy(self, level = 0):
        """ Debug function to print out hierarchy to console.
        
        @param level: starting indent level.
        """
        print('-' * level, self.object)
        for ch in self.childs:
            ch.print_hierarchy(level+1)
            
    def get_tags_egg_str(self, level = 0):
        """ Create and return <Tag> string from Blender's object 
        Game logic properties.
        
        @param level: indent level.
        
        @return: the EGG tags string.
        """
        egg_str = ''
        if self.object:
            for prop in self.object.game.properties:
                if prop.name in ('Collide', 'ObjectType'):
                    vals = ('  ' * level, prop.name, prop.value)
                    egg_str += '%s<%s> { %s }\n' % vals
                else:
                    vals = ('  ' * level, eggSafeName(prop.name), eggSafeName(prop.value))
                    egg_str += '%s<Tag> %s { %s }\n' % vals
        return egg_str
                
            
    def get_full_egg_str(self,level = 0):
        """ Create and return representation of the EGG  <Group>  
        with hierarchy, started from self.object. It's start point to
        generating EGG structure.
        
        @param level: starting indent level.
        
        @return: full EGG string of group.
        """
        egg_str = ''
        if self.object:
            egg_str += '%s<Group> %s {\n' % ('  ' * level, eggSafeName(self.object.yabee_name))
            egg_str += self.get_tags_egg_str(level + 1)
            if self.object.type == 'MESH':
                if (('ARMATURE' in [m.type for m in self.object.modifiers]) or 
                    (((self.object.data.shape_keys) and 
                      (len(self.object.data.shape_keys.key_blocks) > 1)))):
                    egg_str += '%s<Dart> { 1 }\n' % ('  ' * (level + 1))
                    egg_mesh = EGGActorObjectData(self.object)
                else:
                    egg_mesh = EGGMeshObjectData(self.object)
                for line in egg_mesh.get_full_egg_str().splitlines():
                    egg_str += '%s%s\n' % ('  ' * (level + 1), line)
            elif self.object.type == 'CURVE':
                egg_obj = EGGNurbsCurveObjectData(self.object)
                for line in egg_obj.get_full_egg_str().splitlines():
                    egg_str += '%s%s\n' % ('  ' * (level + 1), line)
            elif self.object.type == 'ARMATURE':
                egg_obj = EGGArmature(None)
                egg_obj.make_hierarchy_from_list(self.object.data.bones)
                egg_str += '%s<Dart> { 1 }\n' % ('  ' * (level + 1))
                for line in egg_obj.get_full_egg_str({}, self.object, -1).splitlines():
                    egg_str += '%s%s\n' % ('  ' * (level + 1), line)
            else:
                egg_obj = EGGBaseObjectData(self.object)
                for line in egg_obj.get_full_egg_str().splitlines():
                    egg_str += '%s%s\n' % ('  ' * (level + 1), line)
            for ch in self.childs:
                egg_str += ch.get_full_egg_str(level + 1)
            egg_str += '%s}\n' % ('  ' * level)
        else:        
            for ch in self.childs:
                egg_str += ch.get_full_egg_str(level + 1)
        return egg_str
                    

class EGGArmature(Group):
    """ Representation of the EGG <Joint> hierarchy. Recive Blender's 
    bones list as obj_list in constructor.
    """
    
    def get_full_egg_str(self, vrefs, arm_owner, level = 0):
        """ Create and return string representation of the EGG <Joint> 
        with hieratchy.
        
        @param vrefs: reference of vertices, linked to bones.
        @param arm_owner: Armature object - owner of the bones
        @param level: indent level.
        
        @return: the EGG string with joints hierarchy
        """
        egg_str = ''
        if self.object:
            egg_str += '%s<Joint> %s {\n' % ('  ' * level, eggSafeName(self.object.name))
            # Get vertices reference by Bone name from globlal armature vref
            if self.object.name in list(vrefs.keys()):
                vref = vrefs[self.object.name]
            else:
                vref = {}
            joint = EGGJointObjectData(self.object, vref, arm_owner)
            for line in joint.get_full_egg_str().splitlines():
                egg_str += '%s%s\n' % ('  ' * (level + 1), line)
            for ch in self.childs:
                egg_str += ch.get_full_egg_str(vrefs, arm_owner, level + 1)
            egg_str += '%s}\n' % ('  ' * level)
        else:
            for ch in self.childs:
                egg_str += ch.get_full_egg_str(vrefs, arm_owner, level + 1)
        return egg_str


#-----------------------------------------------------------------------
#                           BASE OBJECT                                 
#-----------------------------------------------------------------------
class EGGBaseObjectData:
    """ Base representation of the EGG objects  data
    """
    
    def __init__(self, obj):
        self.obj_ref = obj
        self.transform_matrix = obj.matrix_world
        
    def get_transform_str(self):
        """ Return the EGG string representation of object transforms.
        """
        tr_str = '<Transform> {\n  <Matrix4> {\n'        
        for y in self.transform_matrix.col:
            tr_str += '    '
            for x in y[:]:
                tr_str += STRF( x ) + ' '
            tr_str += '\n'
        tr_str += '  }\n}\n'        
        return tr_str
        
    def get_full_egg_str(self):
        return self.get_transform_str() + '\n'
        

class EGGNurbsCurveObjectData(EGGBaseObjectData):
    """ Representation of the EGG NURBS Curve
    """
    def collect_vertices(self):
        #str6f = lambda x: '%.6f' % x
        vertices = []
        idx = 0
        for spline in self.obj_ref.data.splines:
            for vtx in spline.points:
                #co = vtx.co * self.obj_ref.matrix_world
                co = self.obj_ref.matrix_world * vtx.co
                vertices.append('<Vertex> %i {\n  %s\n}\n' % (idx, 
                                    ' '.join(map(STRF, co))))
                idx += 1
        return vertices
                
        
    def get_vtx_pool_str(self):
        """ Return the vertex pool string in the EGG syntax. 
        """
        vtx_pool = ''
        vertices = self.collect_vertices()
        if vertices:
            vtx_pool = '<VertexPool> %s {\n' % eggSafeName(self.obj_ref.yabee_name)
            for vtx_str in vertices:
                for line in vtx_str.splitlines():
                    vtx_pool += '  ' + line + '\n'
            vtx_pool += '}\n'
        return vtx_pool
        
    def get_curves_str(self):
        """ Return the <NURBSCurve> string. Blender 2.5 has not contain
        Knots information, seems it's calculating in runtime. 
        I got algorythm for the knots calculation from the OBJ exporter
        and modified it.
        """
        str2f = lambda x: '%.2f' % x
        cur_str = ''
        idx = 0
        for spline in self.obj_ref.data.splines:
            if spline.type == 'NURBS':
                knots_num = spline.point_count_u + spline.order_u
                knots = [i/(knots_num - 1) for i in range(knots_num)]
                if spline.use_endpoint_u:
                    for i in range(spline.order_u - 1):
                        knots[i] = 0.0
                        knots[-(i + 1)] = 1.0
                    for i in range(knots_num - (spline.order_u * 2) + 2):
                        knots[i + spline.order_u - 1] = i/(knots_num - (spline.order_u * 2) + 1)
                cur_str += '<NURBSCurve> {\n'
                cur_str += '  <Scalar> subdiv { %i }\n' % (spline.resolution_u * \
                                                    (spline.point_count_u - 1))
                cur_str += '  <Order> { %i }\n' % spline.order_u
                cur_str += '  <Knots> { %s }\n' % ' '.join(map(str2f, knots))
                cur_str += '  <VertexRef> {\n    %s\n    <Ref> { %s } \n  }\n' % ( 
                        ' '.join([str(i) for i in range(idx, idx + \
                        spline.point_count_u)]), eggSafeName(self.obj_ref.yabee_name))
                cur_str += '}\n'
                idx += spline.point_count_u
        return cur_str
        
    def get_full_egg_str(self):
        return self.get_transform_str() + self.get_vtx_pool_str() + self.get_curves_str()
        

class EGGJointObjectData(EGGBaseObjectData):
    """ Representation of the EGG <Joint> data
    """
    
    def __init__(self, obj, vref, arm_owner):
        """ @param vref: reference of vertices, linked to bone.
        @param arm_owner: Armature object - owner of the bones
        """
        self.obj_ref = obj
        self.arm_owner = arm_owner
        if not obj.parent:
            self.transform_matrix = arm_owner.matrix_world * obj.matrix_local
        else:
            self.transform_matrix = obj.parent.matrix_local.inverted() * obj.matrix_local
        self.vref = vref
        
    def get_vref_str(self):
        """ Convert vertex reference to the EGG string and return it.
        """
        vref_str = ''
        for vpool, data in self.vref.items():
            weightgroups = {}
            for idx, weight in data:
                wstr = '%s' % STRF(weight)
                if wstr not in list(weightgroups.keys()):
                    weightgroups[wstr] = []
                weightgroups[wstr].append(idx)
            for wgrp, idxs in weightgroups.items():
                vref_str += '<VertexRef> {\n'
                vref_str += '  ' + ' '.join(map(str,idxs)) + '\n'
                vref_str += '  <Scalar> membership { %s }' % wgrp
                vref_str += '  <Ref> { %s }\n}\n' % vpool
        return vref_str
    
    def get_full_egg_str(self):
        egg_str = ''
        egg_str += self.get_transform_str()
        egg_str += self.get_vref_str()
        for obj in [obj for obj in bpy.context.selected_objects \
                    if self.obj_ref.name == obj.parent_bone and self.arm_owner == obj.parent]:
            gr = Group(None)
            obj_list = []
            hierarchy_to_list(obj, obj_list)
            obj_list = [obj for obj in obj_list if (obj in bpy.context.selected_objects)]
            gr.make_hierarchy_from_list(obj_list)
            for line in gr.get_full_egg_str(-1).splitlines():
                egg_str += line + '\n'
        
        return  egg_str
        
        
#-----------------------------------------------------------------------
#                           MESH OBJECT                                 
#-----------------------------------------------------------------------
class EGGMeshObjectData(EGGBaseObjectData):
    """ EGG data representation of the mesh object
    """

    def __init__(self, obj):
        EGGBaseObjectData.__init__(self, obj)
        self.smooth_vtx_list = self.get_smooth_vtx_list()
        self.poly_vtx_ref = self.pre_convert_poly_vtx_ref()
        self.colors_vtx_ref = self.pre_convert_vtx_color()
        self.uvs_list = self.pre_convert_uvs()
        if CALC_TBS == 'INTERNAL':
            self.tbs = io_scene_egg.yabee_libs.tbn_generator.TBNGenerator(obj).generate()
        else:
            self.tbs = None
            


    #-------------------------------------------------------------------
    #                           AUXILIARY                               

    def get_smooth_vtx_list(self):
        """ Collect the smoothed polygon vertices 
        for write normals of the vertices. In the EGG for the smooth 
        shading used normals of vertices. For solid - polygons.
        """
        vtx_list = []
        for f in self.obj_ref.data.polygons:
            if f.use_smooth:
                for v in f.vertices:                
                    vtx_list.append(v)
        return set(vtx_list)
        
    def pre_convert_uvs(self):
        """ Blender uses shared vertices, but for the correct working 
        UV and shading in the Panda needs to convert they are in the 
        individual vertices for each polygon.
        """
        uv_list = []
        self.obj_ref.data.update(calc_tessface=True)
        for uv_layer in self.obj_ref.data.tessface_uv_textures:
            data = []
            for uv_face in uv_layer.data:
                for u,v in uv_face.uv:
                    data.append((u,v))
            uv_list.append((uv_layer.name, data))
        return uv_list
        
    def pre_convert_poly_vtx_ref(self):
        """ Blender uses shared vertices, but for the correct working 
        UV and shading in the Panda needs to convert they are in the 
        individual vertices for each polygon.
        """
        poly_vtx_ref = []
        idx = 0
        for face in self.obj_ref.data.polygons:
            vtxs = []
            for v in face.vertices:
                vtxs.append(idx)
                idx += 1
            poly_vtx_ref.append(vtxs)
        return poly_vtx_ref
        
    def pre_convert_vtx_color(self):
        color_vtx_ref = []
        if self.obj_ref.data.vertex_colors.active:
            for col in self.obj_ref.data.vertex_colors.active.data:
                color_vtx_ref.append(col.color) # We have one color per data color
            #for fi, face in enumerate(self.obj_ref.data.polygons):
            #    col = self.obj_ref.data.vertex_colors.active.data[fi]
            #    col = col.color1[:], col.color2[:], col.color3[:], col.color4[:]
            #    for vi, v in enumerate(face.vertices):
            #        color_vtx_ref.append(col[vi])
        return color_vtx_ref
    
    #-------------------------------------------------------------------
    #                           VERTICES                                

    def collect_vtx_xyz(self, vidx, attributes):
        """ Add coordinates of the vertex to the vertex attriibutes list
        
        @param vidx: Blender's internal vertex index.
        @param attributes: list of vertex attributes
        
        @return: list of vertex attributes.
        """
        #co = self.obj_ref.data.vertices[vidx].co * self.obj_ref.matrix_world
        co = self.obj_ref.matrix_world * self.obj_ref.data.vertices[vidx].co
        #co = map(STRF, co)
        co = map(str, co)
        attributes.append('\n' + ' '.join(co))
        return attributes
        
    def collect_vtx_dxyz(self, vidx, attributes):
        """ Add morph target <Dxyz> to the vertex attributes list.
        
        @param vidx: Blender's internal vertex index.
        @param attributes: list of vertex attributes
        
        @return: list of vertex attributes.
        """
        if ((self.obj_ref.data.shape_keys) and (len(self.obj_ref.data.shape_keys.key_blocks) > 1)):
            for i in range(1,len(self.obj_ref.data.shape_keys.key_blocks)):
                key = self.obj_ref.data.shape_keys.key_blocks[i]
                vtx = self.obj_ref.data.vertices[vidx]
                co = key.data[vidx].co * self.obj_ref.matrix_world - \
                     vtx.co * self.obj_ref.matrix_world
                if co.length > 0.000001:
                    attributes.append('<Dxyz> "%s" { %s %s %s }\n' % \
                                      (key.name, STRF(co[0]), STRF(co[1]), STRF(co[2])))
        return attributes
        
    def collect_vtx_normal(self, vidx, attributes):
        """ Add <Normal> to the vertex attributes list.
        
        @param vidx: Blender's internal vertex index.
        @param attributes: list of vertex attributes
        
        @return: list of vertex attributes.
        """
        if vidx in self.smooth_vtx_list:
            #no = self.obj_ref.data.vertices[vidx].normal * self.obj_ref.matrix_world.to_euler().to_matrix()
            no = self.obj_ref.matrix_world.to_euler().to_matrix() * self.obj_ref.data.vertices[vidx].normal
            attributes.append('<Normal> { %s %s %s }' % (STRF(no[0]), STRF(no[1]), STRF(no[2])))
        return attributes
        
    def collect_vtx_rgba(self, vidx, attributes):
        if self.colors_vtx_ref:
            col = self.colors_vtx_ref[vidx]
            attributes.append('<RGBA> { %s %s %s 1.0 }' % (STRF(col[0]), STRF(col[1]), STRF(col[2])))
        return attributes
        
    def collect_vtx_uv(self, vidx, ividx, attributes):
        """ Add <UV> to the vertex attributes list.
        
        @param vidx: the EGG (converted) vertex index.
        @param attributes: list of vertex attributes
        
        @return: list of vertex attributes.
        """
        for i in range(len(self.uvs_list)):
            name, data = self.uvs_list[i]
            if i == 0: name = ''
            if self.tbs:
                t = self.tbs[vidx][0][i]
                b = self.tbs[vidx][1][i]
            try:
                uv_str = '\n<UV> %s {\n  %s %s\n' % (name, STRF(data[ividx][0]), STRF(data[ividx][1]))
                if self.tbs:
                    uv_str += '  <Tangent> { %s %s %s }\n' % (STRF(t[0]), STRF(t[1]), STRF(t[2]))
                    uv_str += '  <Binormal> { %s %s %s }\n' % (STRF(b[0]), STRF(b[1]), STRF(b[2]))
                uv_str  += '}'
                attributes.append(uv_str)
                #attributes.append('<UV> %s { %.6f %.6f }' % (name, data[ividx][0], data[ividx][1]))
            except:
                print('ERROR: can\'t get UV information in "collect_vtx_uv"')
        return attributes
        
    def collect_vertices(self):
        """ Convert and collect vertices info. 
        """
        vertices = []
        idx = 0
        for f in self.obj_ref.data.polygons:
            for v in f.vertices:
                # v - Blender inner vertex index
                # idx - Vertex index for the EGG
                attributes = []
                self.collect_vtx_xyz(v, attributes)
                self.collect_vtx_dxyz(v, attributes)
                self.collect_vtx_normal(v, attributes)
                self.collect_vtx_rgba(idx, attributes)
                self.collect_vtx_uv(v, idx, attributes)
                str_attr = '\n'.join(attributes)
                str_attr = str_attr.replace('\n', '\n  ')
                #vtx = '\n<Vertex> %s {%s\n}' % (idx, str_attr)
                vtx = '\n<Vertex> ' + str(idx) + ' {' + str_attr + '\n}'
                vertices.append(vtx)
                idx += 1
        return vertices
    
    #-------------------------------------------------------------------
    #                           POLYGONS                                
    
    def collect_poly_tref(self, face, attributes):
        """ Add <TRef> to the polygon's attributes list.
        
        @param face: face index.
        @param attributes: list of polygon's attributes.
        
        @return: list of polygon's attributes.
        """
        if TEXTURE_PROCESSOR == 'SIMPLE':
            if EXPORT_UV_IMAGE_AS_TEXTURE:
                for uv_tex in self.obj_ref.data.uv_textures:
                    #if uv_tex.data[face.index].use_image:
                    if uv_tex.data[face.index].image.source == 'FILE':
                        attributes.append('<TRef> { %s }' % uv_tex.data[face.index].image.name)
            if face.material_index < len(self.obj_ref.data.materials):
                mat = self.obj_ref.data.materials[face.material_index]
                tex_idx = 0
                for tex in [tex for tex in mat.texture_slots if tex]:
                    if ((tex.texture_coords == 'UV') 
                         and (not tex.texture.use_nodes)
                         and (mat.use_textures[tex_idx])):
                            if tex.texture.image and tex.texture.image.source == 'FILE' and not tex.use_map_alpha:
                                attributes.append('<TRef> { %s }' % tex.texture.name)
                    tex_idx += 1
        elif TEXTURE_PROCESSOR == 'BAKE':
            #if [uv for uv in self.obj_ref.data.uv_textures if uv.active]:
            if self.obj_ref.data.uv_textures:
                for btype, params in BAKE_LAYERS.items():
                    if len(params) == 2:
                        params = (params[0], params[0], params[1])
                    if params[2]:
                        attributes.append('<TRef> { %s }' % (self.obj_ref.yabee_name + '_' + btype))
        return attributes
    
    def collect_poly_mref(self, face, attributes):
        """ Add <MRef> to the polygon's attributes list.
        
        @param face: face index.
        @param attributes: list of polygon's attributes.
        
        @return: list of polygon's attributes.
        """
        #if face.material_index < len(bpy.data.materials):
        #    mat = bpy.data.materials[face.material_index]
        if face.material_index < len(self.obj_ref.data.materials):
            mat = self.obj_ref.data.materials[face.material_index]
            attributes.append('<MRef> { %s }' % eggSafeName(mat.name))
        return attributes
    
    def collect_poly_normal(self, face, attributes):
        """ Add <Normal> to the polygon's attributes list.
        
        @param face: face index.
        @param attributes: list of polygon's attributes.
        
        @return: list of polygon's attributes.
        """
        #no = face.normal * self.obj_ref.matrix_world.to_euler().to_matrix()
        no = self.obj_ref.matrix_world.to_euler().to_matrix() * face.normal
        attributes.append('<Normal> {%s %s %s}' % (STRF(no[0]), STRF(no[1]), STRF(no[2])))
        return attributes
    
    def collect_poly_rgba(self, face, attributes):
        return attributes
    
    def collect_poly_bface(self, face, attributes):
        """ Add <BFace> to the polygon's attributes list.
        
        @param face: face index.
        @param attributes: list of polygon's attributes.
        
        @return: list of polygon's attributes.
        """
        #if [uv_face.data[face.index] for uv_face in self.obj_ref.data.uv_textures if uv_face.data[face.index].use_twoside]:
        #    attributes.append('<BFace> { 1 }')
        if face.material_index < len(self.obj_ref.data.materials):
            #print('+++', face.material_index, self.obj_ref.data.materials[face.material_index].game_settings.use_backface_culling)
            if not self.obj_ref.data.materials[face.material_index].game_settings.use_backface_culling:
                attributes.append('<BFace> { 1 }')
        return attributes
        
    def collect_poly_vertexref(self, face, attributes):
        """ Add <VertexRef> to the polygon's attributes list.
        
        @param face: face index.
        @param attributes: list of polygon's attributes.
        
        @return: list of polygon's attributes.
        """
        vr = ' '.join(map(str,self.poly_vtx_ref[face.index]))
        attributes.append('<VertexRef> { %s <Ref> { %s }}' % (vr, self.obj_ref.yabee_name))
        return attributes
    
    def collect_polygons(self):
        """ Convert and collect polygons info 
        """
        polygons = []
        for f in self.obj_ref.data.polygons:
            poly = '<Polygon> {\n'
            attributes = []
            self.collect_poly_tref(f, attributes)
            self.collect_poly_mref(f, attributes)
            self.collect_poly_normal(f, attributes)
            self.collect_poly_rgba(f, attributes)
            self.collect_poly_bface(f, attributes)
            self.collect_poly_vertexref(f, attributes)
            for attr in attributes:
                for attr_str in attr.splitlines():
                    poly += '  ' + attr_str + '\n'
            poly += '}\n'
            polygons.append(poly)
        return polygons
        
    def get_vtx_pool_str(self):
        """ Return the vertex pool string in the EGG syntax. 
        """
        vtx_pool = '<VertexPool> %s {\n' % self.obj_ref.yabee_name
        vtxs = ''.join(self.collect_vertices())
        vtxs = vtxs.replace('\n', '\n  ')
        vtx_pool += vtxs
        vtx_pool += '}\n'
        return vtx_pool
        
    def get_polygons_str(self):
        """ Return polygons string in the EGG syntax 
        """
        polygons = '\n' + ''.join(self.collect_polygons())
        return polygons
        
    def get_full_egg_str(self):
        """ Return full mesh data representation in the EGG string syntax 
        """
        return self.get_transform_str() + '\n' \
                + self.get_vtx_pool_str() + '\n' \
                + self.get_polygons_str()


#-----------------------------------------------------------------------
#                           ACTOR OBJECT                                
#-----------------------------------------------------------------------
class EGGActorObjectData(EGGMeshObjectData):
    """ Representation of the EGG animated object data
    """
    
    def __init__(self, obj):
        EGGMeshObjectData.__init__(self,obj)
        self.joint_vtx_ref = self.pre_convert_joint_vtx_ref()
        
    def pre_convert_joint_vtx_ref(self):
        """ Collect and convert vertices, assigned to the bones
        """
        joint_vref = {}
        idx = 0
        for face in self.obj_ref.data.polygons:
            for v in face.vertices:
                for g in self.obj_ref.data.vertices[v].groups:
                    gname = self.obj_ref.vertex_groups[g.group].name
                    # Goup name = Joint (bone) name
                    if gname not in list(joint_vref.keys()):
                        joint_vref[gname] = {}
                    # Object name = vertices pool name
                    if self.obj_ref.yabee_name not in list(joint_vref[gname].keys()):
                        joint_vref[gname][self.obj_ref.yabee_name] = []
                    joint_vref[gname][self.obj_ref.yabee_name].append((idx, g.weight))
                idx += 1
        return joint_vref
        
    def get_joints_str(self):
        """ Make  the EGGArmature object from the bones, pass the 
        vertex referense to it, and return the EGG string representation 
        of the joints hierarchy.
        """
        j_str = ''
        for mod in self.obj_ref.modifiers:
            if mod.type == 'ARMATURE':
                ar = EGGArmature(None)
                ar.make_hierarchy_from_list(mod.object.data.bones)
                j_str += ar.get_full_egg_str(self.joint_vtx_ref, mod.object, -1)
        return j_str
        
    def get_full_egg_str(self):
        """ Return string representation of the EGG animated object data.
        """
        return self.get_vtx_pool_str() + '\n' \
                + self.get_polygons_str() + '\n' \
                + self.get_joints_str() + '\n'


class EGGAnimJoint(Group):
    """ Representation of the <Joint> animation data. Has the same 
    hierarchy as the character's skeleton.
    """
    
    def get_full_egg_str(self, anim_info, framerate, level = 0):
        """ Create and return the string representation of the <Joint>
        animation data, included all joints hierarchy.
        """
        egg_str = ''
        if self.object:
            egg_str += '%s<Table> %s {\n' % ('  ' * level, eggSafeName(self.object.name))
            bone_data = anim_info['<skeleton>'][self.object.name]
            egg_str += '%s  <Xfm$Anim> xform {\n' % ('  ' * level)
            egg_str += '%s    <Scalar> order { sprht }\n' % ('  ' * level)
            egg_str += '%s    <Scalar> fps { %i }\n' % ('  ' * level, framerate)
            egg_str += '%s    <Scalar> contents { ijkprhxyz }\n' % ('  ' * level)
            egg_str += '%s    <V> {\n' % ('  ' * level)
            for i in range(len(bone_data['r'])):
                egg_str += '%s      %s %s %s %s %s %s %s %s %s\n' % (
                                                    '  ' * level, 
                                                    STRF(1.0), 
                                                    STRF(1.0), 
                                                    STRF(1.0), 
                                                    STRF(bone_data['p'][i]), 
                                                    STRF(bone_data['r'][i]), 
                                                    STRF(bone_data['h'][i]),
                                                    STRF(bone_data['x'][i]), 
                                                    STRF(bone_data['y'][i]), 
                                                    STRF(bone_data['z'][i]))
            egg_str += '%s    }\n' % ('  ' * level)
            egg_str += '%s  }\n' % ('  ' * level)
            for ch in self.childs:
                egg_str += ch.get_full_egg_str(anim_info, framerate, level + 1)
            egg_str += '%s}\n' % ('  ' * level)
        else:        
            for ch in self.childs:
                egg_str += ch.get_full_egg_str(anim_info, framerate, level + 1)
        return egg_str

class AnimCollector():
    """ Collect an armature and a shapekeys animation data and 
    convert it to the EGG string.
    """
    
    def __init__(self, obj_list, start_f, stop_f, framerate, name):
        """ @param obj_list: list or tuple of the Blender's objects
        for wich needed to collect animation data.
        @param start_f: number of the "from" frame.
        @param stop_f: number of the "to" frame.
        @param framerate: framerate for the given animation.
        @param name: name of the animation for access in the Panda.
        """
        self.obj_list = obj_list
        self.start_f = start_f
        self.stop_f = stop_f
        self.framerate = framerate
        self.name = name
        self.bone_groups = {}
        for arm in bpy.data.armatures:
            arm.pose_position = 'POSE'
        self.obj_anim_ref = {}
        for obj in obj_list:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod:
                        if mod.type == 'ARMATURE':
                            self.bone_groups[obj.yabee_name] = EGGAnimJoint(None)
                            self.bone_groups[obj.yabee_name].make_hierarchy_from_list(mod.object.data.bones)
                            if obj.yabee_name not in list(self.obj_anim_ref.keys()):
                                self.obj_anim_ref[obj.yabee_name] = {}
                            self.obj_anim_ref[obj.yabee_name]['<skeleton>'] = \
                                    self.collect_arm_anims(mod.object)
                if ((obj.data.shape_keys) and (len(obj.data.shape_keys.key_blocks) > 1)):
                    if obj.yabee_name not in list(self.obj_anim_ref.keys()):
                        self.obj_anim_ref[obj.yabee_name] = {}
                    self.obj_anim_ref[obj.yabee_name]['morph'] = self.collect_morph_anims(obj)
            elif obj.type == 'ARMATURE':
                self.bone_groups[obj.yabee_name] = EGGAnimJoint(None)
                self.bone_groups[obj.yabee_name].make_hierarchy_from_list(obj.data.bones)
                if obj.yabee_name not in list(self.obj_anim_ref.keys()):
                    self.obj_anim_ref[obj.yabee_name] = {}
                self.obj_anim_ref[obj.yabee_name]['<skeleton>'] = \
                        self.collect_arm_anims(obj)
    def collect_morph_anims(self, obj):
        """ Collect an animation data for the morph target (shapekeys).
        
        @param obj: Blender's object for wich need to collect an animation data
        """
        keys = {}
        if ((obj.data.shape_keys) and (len(obj.data.shape_keys.key_blocks) > 1)):
            current_f = bpy.context.scene.frame_current
            anim_dict = {}
            for f in range(self.start_f, self.stop_f):
                bpy.context.scene.frame_current = f
                bpy.context.scene.frame_set(f)
                for i in range(1,len(obj.data.shape_keys.key_blocks)):
                    key = obj.data.shape_keys.key_blocks[i]
                    if key.name not in list(keys.keys()):
                        keys[key.name] = []
                    keys[key.name].append(key.value)
            bpy.context.scene.frame_current = current_f
        return keys
    
    def collect_arm_anims(self, arm):
        """ Collect an animation data for the skeleton (Armature).
        
        @param arm: Blender's Armature for wich need to collect an animation data
        """
        current_f = bpy.context.scene.frame_current
        anim_dict = {}
        for f in range(self.start_f, self.stop_f):
            bpy.context.scene.frame_current = f
            bpy.context.scene.frame_set(f)
            for bone in arm.pose.bones:
                if bone.name not in list(anim_dict.keys()):
                    anim_dict[bone.name] = {}
                for k in 'ijkabcrphxyz':
                    if k not in list(anim_dict[bone.name].keys()):
                        anim_dict[bone.name][k] = []
                if bone.parent:
                    matrix = bone.parent.matrix.inverted() * bone.matrix
                else:
                    matrix = arm.matrix_world * bone.matrix

                p, r, h = matrix.to_euler()
                anim_dict[bone.name]['p'].append(p/pi*180)
                anim_dict[bone.name]['r'].append(r/pi*180)
                anim_dict[bone.name]['h'].append(h/pi*180)
                x, y, z = matrix.to_translation()
                anim_dict[bone.name]['x'].append(x)
                anim_dict[bone.name]['y'].append(y)
                anim_dict[bone.name]['z'].append(z)
        bpy.context.scene.frame_current = current_f
        return anim_dict
    
    def get_morph_anim_str(self, obj_name):
        """ Create and return the EGG string of the morph animation for
        the given object.
        
        @param obj_name: name of the Blender's object
        """
        morph_str = ''
        data = self.obj_anim_ref[obj_name]
        if 'morph' in list(data.keys()):
            #str4f = lambda x: '%.4f' % x
            morph_str += '<Table> morph {\n'
            for key, anim_vals in data['morph'].items():
                morph_str += '  <S$Anim> %s {\n' % eggSafeName(key)
                morph_str += '    <Scalar> fps { %i }\n' % self.framerate
                morph_str += '    <V> { %s }\n' % (' '.join(map(STRF, anim_vals)))
                morph_str += '  }\n'
            morph_str += '}\n'
        return morph_str

    def get_skeleton_anim_str(self, obj_name):
        """ Create and return the EGG string of the Armature animation for
        the given object.
        
        @param obj_name: name of the Blender's object
        """
        skel_str = ''
        data = self.obj_anim_ref[obj_name]
        if '<skeleton>' in list(data.keys()):
            skel_str += '<Table> "<skeleton>" {\n'
            for line in self.bone_groups[obj_name].get_full_egg_str(data, self.framerate, -1).splitlines():
                skel_str += '  %s\n' % line
            skel_str += '}\n'
        return skel_str
              
    def get_full_egg_str(self):
        """ Create and return the full EGG string for the animation, wich
        has been setup in the object constructor (__init__)
        """
        egg_str = ''
        if self.obj_anim_ref:
            egg_str += '<Table> {\n'
            for obj_name, obj_data in self.obj_anim_ref.items():
                yabee_obj_name = bpy.data.objects[obj_name].yabee_name
                if self.name:
                    anim_name = self.name
                else:
                    anim_name = obj_name
                if SEPARATE_ANIM_FILE:
                    egg_str += '  <Bundle> %s {\n' % eggSafeName(yabee_obj_name)
                else:
                    egg_str += '  <Bundle> %s {\n' % eggSafeName(anim_name)
                for line in self.get_skeleton_anim_str(obj_name).splitlines():
                    egg_str += '    %s\n' % line
                for line in self.get_morph_anim_str(obj_name).splitlines():
                    egg_str += '    %s\n' % line
                egg_str += '  }\n'
            egg_str += '}\n'
        return egg_str

#-----------------------------------------------------------------------
#                     SCENE MATERIALS & TEXTURES                        
#-----------------------------------------------------------------------
def get_used_materials():
    """ Collect Materials used in the selected object. 
    """
    m_list = []
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            for f in obj.data.polygons:
                if f.material_index < len(obj.data.materials):
                    m_list.append(obj.data.materials[f.material_index].name)
    return set(m_list)



def get_egg_materials_str():
    """ Return the EGG string of used materials
    """
    if not bpy.context.selected_objects:
        return ''
    mat_str = ''
    for m_idx in get_used_materials():
        mat = bpy.data.materials[m_idx]
        mat_str += '<Material> %s {\n' % eggSafeName(mat.name)
        if TEXTURE_PROCESSOR == 'SIMPLE':
            mat_str += '  <Scalar> diffr { %s }\n' % STRF(mat.diffuse_color[0] * mat.diffuse_intensity)
            mat_str += '  <Scalar> diffg { %s }\n' % STRF(mat.diffuse_color[1] * mat.diffuse_intensity)
            mat_str += '  <Scalar> diffb { %s }\n' % STRF(mat.diffuse_color[2] * mat.diffuse_intensity)
            if mat.alpha == 0.0:
                mata = 1.0
            else:
                mata = mat.alpha
            if mata != 1.0:
                mat_str += '  <Scalar> diffa { %s }\n' % STRF(mata)
        elif TEXTURE_PROCESSOR == 'BAKE':
            mat_str += '  <Scalar> diffr { 1.0 }\n'
            mat_str += '  <Scalar> diffg { 1.0 }\n'
            mat_str += '  <Scalar> diffb { 1.0 }\n'
        mat_str += '  <Scalar> specr { %s }\n' % STRF(mat.specular_color[0] * mat.specular_intensity)
        mat_str += '  <Scalar> specg { %s }\n' % STRF(mat.specular_color[1] * mat.specular_intensity)
        mat_str += '  <Scalar> specb { %s }\n' % STRF(mat.specular_color[2] * mat.specular_intensity)
        mat_str += '  <Scalar> shininess { %s }\n' % (mat.specular_hardness / 512 * 128)
        mat_str += '  <Scalar> emitr { %s }\n' % STRF(mat.emit * 0.1)
        mat_str += '  <Scalar> emitg { %s }\n' % STRF(mat.emit * 0.1)
        mat_str += '  <Scalar> emitb { %s }\n' % STRF(mat.emit * 0.1)
        matas = mat.specular_alpha
        if matas == 0.0:
            matas = 1.0
        if matas != 1.0:
            mat_str += '  <Scalar> speca { %s }\n' % STRF(matas)
        #file.write('  <Scalar> ambr { %s }\n' % STRF(mat.ambient))
        #file.write('  <Scalar> ambg { %s }\n' % STRF(mat.ambient))
        #file.write('  <Scalar> ambb { %s }\n' % STRF(mat.ambient))
        mat_str += '}\n\n'
    if TEXTURE_PROCESSOR == 'SIMPLE':
        st = SimpleTextures(bpy.context.selected_objects, 
                            EXPORT_UV_IMAGE_AS_TEXTURE, 
                            COPY_TEX_FILES, 
                            FILE_PATH, TEX_PATH)
        used_textures = st.get_used_textures()
    elif TEXTURE_PROCESSOR == 'BAKE':
        tb = TextureBaker(bpy.context.selected_objects, FILE_PATH, TEX_PATH)
        used_textures = tb.bake(BAKE_LAYERS)
    print(used_textures)
    #for name, path in used_textures.items():
    #    mat_str += '<Texture> %s {\n' % name
    #    mat_str += '  "' + convertFileNameToPanda(path[1]) + '"\n'
    #    if path[0]:
    #        mat_str += '  <Scalar> uv-name { %s }\n' % path[0]
    #    if path[2] != 'MODULATE':
    #        mat_str += '  <Scalar> envtype { %s }\n' % path[2]
    #    mat_str += '}\n\n'
    for name, params in used_textures.items():
        mat_str += '<Texture> %s {\n' % name
        mat_str += '  "' + convertFileNameToPanda(params['path']) + '"\n'
        for scalar in params['scalars']:
            mat_str += ('  <Scalar> %s { %s }\n' % scalar)
        mat_str += '}\n\n'
    return mat_str
    
    
#-----------------------------------------------------------------------
#                   Preparing & auxiliary functions                     
#-----------------------------------------------------------------------
def hierarchy_to_list(obj, list):
    list.append(obj)
    for ch in obj.children:
        if ch not in list:
            hierarchy_to_list(ch, list)


def merge_objects():
    """ Merge objects, which armatured by single Armature.
    """
    join_to_arm = {}
    selection = []
    for obj in bpy.context.selected_objects:
        to_join = False
        if obj.type == 'MESH':
            for mod in obj.modifiers:
                if mod and mod.type == 'ARMATURE':
                    if mod.object not in join_to_arm.keys():
                        join_to_arm[mod.object] = []
                    join_to_arm[mod.object].append(obj)
                    to_join = True
        if not to_join:
            selection.append(obj)
    for objects in join_to_arm.values():
        bpy.ops.object.select_all(action = 'DESELECT')
        for obj in objects:
            obj.select = True
        #print('selected', bpy.context.selected_objects)
        if len(bpy.context.selected_objects[:]) > 1:
            bpy.context.scene.objects.active = bpy.context.selected_objects[0]
            bpy.ops.object.join()
        selection += bpy.context.selected_objects[:]
    bpy.ops.object.select_all(action = 'DESELECT')
    for obj in selection:
        obj.select = True


def parented_to_armatured():
    """ Convert parented to bone objects to armatured objects.
    """
    arm_objects = []
    old_selection = bpy.context.selected_objects[:]
    bpy.ops.object.select_all(action = 'DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' \
           and obj.parent \
           and obj.parent.type == 'ARMATURE' \
           and obj.parent_bone:
            bpy.ops.object.select_all(action = 'DESELECT')
            obj.select = True
            arm = obj.parent
            bone = obj.parent_bone
            bpy.ops.object.select_hierarchy(direction = 'CHILD', extend = True)
            has_selected = [obj for obj \
                            in bpy.context.selected_objects if \
                            obj in old_selection]
            if has_selected:
                for sobj in has_selected:
                    arm_objects.append((sobj, arm, bone))
    for obj, arm, bone in arm_objects:
        modifiers = [mod.type for mod in obj.modifiers]
        if 'ARMATURE' not in modifiers:
            obj.vertex_groups.new(bone)
            obj.modifiers.new(type = 'ARMATURE', name = 'PtA')
            obj.modifiers['PtA'].object = arm
            idxs = [vtx.index for vtx in obj.data.vertices]
            obj.vertex_groups[bone].add(index = idxs, weight = 1.0, type = 'ADD')
            obj.matrix_local = obj.matrix_parent_inverse * obj.matrix_world
            obj.parent = None
    for obj in old_selection:
        obj.select = True


def apply_modifiers():
    for obj in bpy.context.selected_objects:
        for mod in obj.modifiers:
            if mod and mod.type != 'ARMATURE':
                bpy.context.scene.objects.active = obj
                bpy.ops.object.modifier_apply(modifier = mod.name)


#-----------------------------------------------------------------------
#                           WRITE OUT                                   
#-----------------------------------------------------------------------
def write_out(fname, anims, uv_img_as_tex, sep_anim, a_only, copy_tex, 
              t_path, fp_accuracy, tbs, tex_processor, b_layers, 
              m_actor, apply_m, pview):
    global FILE_PATH, ANIMATIONS, EXPORT_UV_IMAGE_AS_TEXTURE, \
           COPY_TEX_FILES, TEX_PATH, SEPARATE_ANIM_FILE, ANIM_ONLY, \
           STRF, CALC_TBS, TEXTURE_PROCESSOR, BAKE_LAYERS, \
           MERGE_ACTOR_MESH, APPLY_MOD, PVIEW
    imp.reload(io_scene_egg.yabee_libs.texture_processor)
    imp.reload(io_scene_egg.yabee_libs.tbn_generator)
    imp.reload(io_scene_egg.yabee_libs.utils)
    # === prepare to write ===
    FILE_PATH = fname
    ANIMATIONS = anims
    EXPORT_UV_IMAGE_AS_TEXTURE = uv_img_as_tex
    SEPARATE_ANIM_FILE = sep_anim
    ANIM_ONLY = a_only
    CALC_TBS = tbs
    COPY_TEX_FILES = copy_tex
    TEX_PATH = t_path
    TEXTURE_PROCESSOR = tex_processor
    BAKE_LAYERS = b_layers
    MERGE_ACTOR_MESH = m_actor
    APPLY_MOD = apply_m
    PVIEW = pview
    s_acc = '%.' + str(fp_accuracy) + 'f'
    def str_f(x):
        #s = '%.' + str(fp_accuracy) + 'f'
        return s_acc % x
    STRF = str_f
    # Prepare copy of the scene.
    # Sync objects names with custom property "yabee_name" 
    # to be able to get basic object name in the copy of the scene.
    for obj in bpy.data.objects:
        obj.yabee_name = obj.name
    old_data = {}
    for d in (bpy.data.materials, bpy.data.objects, bpy.data.textures,
              bpy.data.armatures, bpy.data.actions, bpy.data.brushes, 
              bpy.data.cameras, bpy.data.curves, bpy.data.groups, 
              bpy.data.images, bpy.data.lamps, bpy.data.meshes, 
              bpy.data.metaballs, bpy.data.movieclips, 
              bpy.data.node_groups, bpy.data.particles, bpy.data.screens, 
              bpy.data.scripts, bpy.data.shape_keys, bpy.data.sounds, 
              bpy.data.speakers, bpy.data.texts, bpy.data.window_managers, 
              bpy.data.worlds, bpy.data.grease_pencil):
        old_data[d] = d[:]
    bpy.ops.scene.new(type = 'FULL_COPY')
    if APPLY_MOD:
        apply_modifiers()
    parented_to_armatured()
    if MERGE_ACTOR_MESH:
        merge_objects()
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    gr = Group(None)
    obj_list = [obj for obj in bpy.context.selected_objects if obj.type != 'ARMATURE']
    print('obj list', obj_list)
    gr.make_hierarchy_from_list(obj_list)
    #gr.print_hierarchy()
    fdir, fname = os.path.split(os.path.abspath(FILE_PATH))
    if not os.path.exists(fdir):
        print('PATH %s not exist. Trying to make path' % fdir)
        os.makedirs(fdir)
    # === write egg data ===
    print('WRITE main EGG to %s' % os.path.abspath(FILE_PATH))
    if ((not ANIM_ONLY) or (not SEPARATE_ANIM_FILE)):
        file = open(FILE_PATH, 'w')
    if not ANIM_ONLY:
        file.write('<CoordinateSystem> { Z-up } \n')
        file.write(get_egg_materials_str())
        file.write(gr.get_full_egg_str())
    fpa = []
    for a_name, frames in ANIMATIONS.items():
        ac = AnimCollector(obj_list, 
                            frames[0], 
                            frames[1], 
                            frames[2], 
                            a_name)
        if not SEPARATE_ANIM_FILE:
            file.write(ac.get_full_egg_str())
        else:
            a_path = FILE_PATH
            if a_path[-4:].upper() == '.EGG':
                a_path = a_path[:-4] + '-' + a_name + a_path[-4:]
            else:
                a_path = a_path + '-' + a_name + '.egg'
            a_egg_str = ac.get_full_egg_str()
            if len(a_egg_str) > 0:
                a_file = open(a_path, 'w')
                a_file.write('<CoordinateSystem> { Z-up } \n')
                a_file.write(ac.get_full_egg_str())
                a_file.close()
                fpa.append(a_path)
    if ((not ANIM_ONLY) or (not SEPARATE_ANIM_FILE)):
        file.close()
    if CALC_TBS == 'PANDA':
        try:
            fp = os.path.abspath(FILE_PATH)
            for line in os.popen('egg-trans -tbnall -o "%s" "%s"' % (fp, fp)).readlines():
                print(line)
        except:
            print('ERROR: Can\'t calculate TBS through panda\'s egg-trans')
    if PVIEW:
        try:
            fp = os.path.abspath(FILE_PATH)
            subprocess.Popen(['pview', fp] + fpa)
        except:
            print('ERROR: Can\'t execute pview')
    # Clearing the scene. 
    # (!) Possible Incomplete. 
    # Whenever we are deleted our copy of the scene, 
    # Blender won't to delete other objects, created with the scene, so 
    # we should do it by hand. I recommend to save the .blend file before 
    # exporting and reload it after.
    bpy.ops.scene.delete()
    for d in old_data:
        for obj in d:
            if obj not in old_data[d]:
                obj.user_clear()
                d.remove(obj)


def write_out_test(fname, anims, uv_img_as_tex, sep_anim, a_only, copy_tex, 
              t_path, fp_accuracy, tbs, tex_processor, b_layers):
    import profile
    import pstats
    wo = "write_out('%s', %s, %s, %s, %s, %s, '%s', %s, '%s', '%s', %s)" % \
            (fname, anims, uv_img_as_tex, sep_anim, a_only, copy_tex, 
             t_path, fp_accuracy, tbs, tex_processor, b_layers)
    profile.runctx(wo, globals(), {}, 'main_prof')
    stats = pstats.Stats('main_prof')
    stats.strip_dirs()
    stats.sort_stats('time')
    stats.print_stats(10)
