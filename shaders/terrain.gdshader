// Magic Carpet terrain shader — Forward+ / Vulkan
//
// Triplanar texture blending driven by surface normal, with slope-based
// material mixing: flat=grass/sand, steep=rock, high=snow.
// Plug in your own albedo textures; the original MC1 tiles are in assets/textures/.

shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D texture_grass   : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D texture_rock    : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D texture_sand    : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D texture_snow    : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D heightmap       : hint_default_white, filter_linear;

uniform float uv_scale      = 0.05;   // texture tiling frequency
uniform float slope_rock    = 0.55;   // normal.y threshold below which rock shows
uniform float snow_height   = 0.75;   // normalised world-Y above which snow shows
uniform float height_scale  = 48.0;   // must match terrain_loader.gd height_scale

uniform float roughness     = 0.85;
uniform float metallic      = 0.0;

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos    = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec4 triplanar(sampler2D tex, vec3 pos, vec3 normal, float scale) {
	vec3 w  = pow(abs(normal), vec3(4.0));
	w /= (w.x + w.y + w.z + 0.001);
	vec4 xy = texture(tex, pos.xy * scale);
	vec4 xz = texture(tex, pos.xz * scale);
	vec4 yz = texture(tex, pos.yz * scale);
	return xy * w.z + xz * w.y + yz * w.x;
}

void fragment() {
	float slope      = 1.0 - world_normal.y;           // 0=flat, 1=vertical
	float norm_height = clamp(world_pos.y / height_scale, 0.0, 1.0);

	vec4 c_grass = triplanar(texture_grass, world_pos, world_normal, uv_scale);
	vec4 c_rock  = triplanar(texture_rock,  world_pos, world_normal, uv_scale);
	vec4 c_sand  = triplanar(texture_sand,  world_pos, world_normal, uv_scale);
	vec4 c_snow  = triplanar(texture_snow,  world_pos, world_normal, uv_scale);

	// Slope blend: grass → rock
	float rock_blend = smoothstep(slope_rock - 0.1, slope_rock + 0.1, slope);
	vec4 surface = mix(c_grass, c_rock, rock_blend);

	// Low-height beach blend: grass → sand
	float sand_blend = smoothstep(0.08, 0.02, norm_height);
	surface = mix(surface, c_sand, sand_blend);

	// High-height snow blend
	float snow_blend = smoothstep(snow_height - 0.05, snow_height + 0.05, norm_height);
	surface = mix(surface, c_snow, snow_blend * (1.0 - rock_blend));

	ALBEDO    = surface.rgb;
	ROUGHNESS = roughness;
	METALLIC  = metallic;
}
