extends Node3D

## Loads a level heightmap (extracted by tools/generate_heightmap.py) and
## builds a Godot MeshInstance3D terrain from it.
##
## Drop a 16-bit greyscale PNG from assets/heightmaps/ onto level_heightmap_path,
## or call load_level(n) at runtime.

@export var level_index: int = 0
@export var height_scale: float = 48.0    # world-space Y for max terrain height (196)
@export var tile_size: float = 1.0        # horizontal spacing between height samples
@export var terrain_material: Material

const MAP_SIZE    = 256
const ASSETS_PATH = "res://assets/heightmaps/"


func _ready() -> void:
	load_level(level_index)


func load_level(n: int) -> void:
	var path = ASSETS_PATH + "level_%02d.png" % n
	var img = Image.load_from_file(ProjectSettings.globalize_path(path))
	if img == null:
		push_error("Heightmap not found: %s  —  run tools/generate_heightmap.py --level %d" % [path, n])
		return
	img.convert(Image.FORMAT_RF)
	_build_mesh(img)


func _build_mesh(img: Image) -> void:
	var st = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)

	var half = MAP_SIZE * tile_size * 0.5

	for z in range(MAP_SIZE - 1):
		for x in range(MAP_SIZE - 1):
			var h00 = _sample(img, x,     z)
			var h10 = _sample(img, x + 1, z)
			var h01 = _sample(img, x,     z + 1)
			var h11 = _sample(img, x + 1, z + 1)

			var v00 = Vector3(x       * tile_size - half, h00, z       * tile_size - half)
			var v10 = Vector3((x + 1) * tile_size - half, h10, z       * tile_size - half)
			var v01 = Vector3(x       * tile_size - half, h01, (z + 1) * tile_size - half)
			var v11 = Vector3((x + 1) * tile_size - half, h11, (z + 1) * tile_size - half)

			var uv00 = Vector2(float(x)     / MAP_SIZE, float(z)     / MAP_SIZE)
			var uv10 = Vector2(float(x + 1) / MAP_SIZE, float(z)     / MAP_SIZE)
			var uv01 = Vector2(float(x)     / MAP_SIZE, float(z + 1) / MAP_SIZE)
			var uv11 = Vector2(float(x + 1) / MAP_SIZE, float(z + 1) / MAP_SIZE)

			# Two triangles per cell (CCW winding)
			_add_tri(st, v00, uv00, v01, uv01, v10, uv10)
			_add_tri(st, v10, uv10, v01, uv01, v11, uv11)

	st.generate_normals()
	var mesh = st.commit()

	var mi = get_node_or_null("Terrain") as MeshInstance3D
	if mi == null:
		mi = MeshInstance3D.new()
		mi.name = "Terrain"
		add_child(mi)

	mi.mesh = mesh
	if terrain_material:
		mi.material_override = terrain_material
	else:
		var mat = StandardMaterial3D.new()
		mat.albedo_color = Color(0.45, 0.55, 0.35)
		mat.roughness = 0.9
		mi.material_override = mat


func _sample(img: Image, x: int, z: int) -> float:
	x = clamp(x, 0, MAP_SIZE - 1)
	z = clamp(z, 0, MAP_SIZE - 1)
	# 16-bit PNG loaded as FORMAT_RF: pixel value is 0.0–1.0 mapping 0–65535
	return img.get_pixel(x, z).r * height_scale


func _add_tri(st: SurfaceTool,
              a: Vector3, uva: Vector2,
              b: Vector3, uvb: Vector2,
              c: Vector3, uvc: Vector2) -> void:
	st.set_uv(uva); st.add_vertex(a)
	st.set_uv(uvb); st.add_vertex(b)
	st.set_uv(uvc); st.add_vertex(c)
