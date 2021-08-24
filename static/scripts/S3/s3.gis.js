/**
/**
 * Used by the Map (modules/s3/s3gis.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/**
 * Global vars
 * - usage minimised
 * - per-map configuration & objects are in S3.gis.maps[map_id].s3.xxx
 */
S3.gis.maps = {}; // Array of all the maps in the page
S3.gis.timeouts = {}; // Array of all the timeouts in the page
S3.gis.proj4326 = new OpenLayers.Projection('EPSG:4326');

// Configure OpenLayers
OpenLayers.ImgPath = S3.Ap.concat('/static/img/gis/openlayers/'); // Path for OpenLayers to find it's Theme images
OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3; // avoid pink tiles
OpenLayers.Util.onImageLoadErrorColor = 'transparent';
OpenLayers.ProxyHost = S3.Ap.concat('/gis/proxy?url=');

/*
 * List of URN codes for EPSG in which axis order
 * of coordinates are y,x (e.g. lat, long)
 *
 * Copied from:
 * https://github.com/geopython/OWSLib/blob/master/owslib/crs.py
 *
 * @ToDo: Introspect server side using code like this:
 * https://git.osgeo.org/gitea/GDI-RP/MapSkinner/src/branch/pre_master/service/helper/epsg_api.py
 */
S3.gis.yx = [
    2036, 2044, 2045, 2065, 2081, 2082, 2083, 2085, 2086, 2091, 2092, 2093,
    2096, 2097, 2098, 2105, 2106, 2107, 2108, 2109, 2110, 2111, 2112, 2113,
    2114, 2115, 2116, 2117, 2118, 2119, 2120, 2121, 2122, 2123, 2124, 2125,
    2126, 2127, 2128, 2129, 2130, 2131, 2132, 2166, 2167, 2168, 2169, 2170,
    2171, 2172, 2173, 2174, 2175, 2176, 2177, 2178, 2179, 2180, 2193, 2199,
    2200, 2206, 2207, 2208, 2209, 2210, 2211, 2212, 2319, 2320, 2321, 2322,
    2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334,
    2335, 2336, 2337, 2338, 2339, 2340, 2341, 2342, 2343, 2344, 2345, 2346,
    2347, 2348, 2349, 2350, 2351, 2352, 2353, 2354, 2355, 2356, 2357, 2358,
    2359, 2360, 2361, 2362, 2363, 2364, 2365, 2366, 2367, 2368, 2369, 2370,
    2371, 2372, 2373, 2374, 2375, 2376, 2377, 2378, 2379, 2380, 2381, 2382,
    2383, 2384, 2385, 2386, 2387, 2388, 2389, 2390, 2391, 2392, 2393, 2394,
    2395, 2396, 2397, 2398, 2399, 2400, 2401, 2402, 2403, 2404, 2405, 2406,
    2407, 2408, 2409, 2410, 2411, 2412, 2413, 2414, 2415, 2416, 2417, 2418,
    2419, 2420, 2421, 2422, 2423, 2424, 2425, 2426, 2427, 2428, 2429, 2430,
    2431, 2432, 2433, 2434, 2435, 2436, 2437, 2438, 2439, 2440, 2441, 2442,
    2443, 2444, 2445, 2446, 2447, 2448, 2449, 2450, 2451, 2452, 2453, 2454,
    2455, 2456, 2457, 2458, 2459, 2460, 2461, 2462, 2463, 2464, 2465, 2466,
    2467, 2468, 2469, 2470, 2471, 2472, 2473, 2474, 2475, 2476, 2477, 2478,
    2479, 2480, 2481, 2482, 2483, 2484, 2485, 2486, 2487, 2488, 2489, 2490,
    2491, 2492, 2493, 2494, 2495, 2496, 2497, 2498, 2499, 2500, 2501, 2502,
    2503, 2504, 2505, 2506, 2507, 2508, 2509, 2510, 2511, 2512, 2513, 2514,
    2515, 2516, 2517, 2518, 2519, 2520, 2521, 2522, 2523, 2524, 2525, 2526,
    2527, 2528, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 2538,
    2539, 2540, 2541, 2542, 2543, 2544, 2545, 2546, 2547, 2548, 2549, 2551,
    2552, 2553, 2554, 2555, 2556, 2557, 2558, 2559, 2560, 2561, 2562, 2563,
    2564, 2565, 2566, 2567, 2568, 2569, 2570, 2571, 2572, 2573, 2574, 2575,
    2576, 2577, 2578, 2579, 2580, 2581, 2582, 2583, 2584, 2585, 2586, 2587,
    2588, 2589, 2590, 2591, 2592, 2593, 2594, 2595, 2596, 2597, 2598, 2599,
    2600, 2601, 2602, 2603, 2604, 2605, 2606, 2607, 2608, 2609, 2610, 2611,
    2612, 2613, 2614, 2615, 2616, 2617, 2618, 2619, 2620, 2621, 2622, 2623,
    2624, 2625, 2626, 2627, 2628, 2629, 2630, 2631, 2632, 2633, 2634, 2635,
    2636, 2637, 2638, 2639, 2640, 2641, 2642, 2643, 2644, 2645, 2646, 2647,
    2648, 2649, 2650, 2651, 2652, 2653, 2654, 2655, 2656, 2657, 2658, 2659,
    2660, 2661, 2662, 2663, 2664, 2665, 2666, 2667, 2668, 2669, 2670, 2671,
    2672, 2673, 2674, 2675, 2676, 2677, 2678, 2679, 2680, 2681, 2682, 2683,
    2684, 2685, 2686, 2687, 2688, 2689, 2690, 2691, 2692, 2693, 2694, 2695,
    2696, 2697, 2698, 2699, 2700, 2701, 2702, 2703, 2704, 2705, 2706, 2707,
    2708, 2709, 2710, 2711, 2712, 2713, 2714, 2715, 2716, 2717, 2718, 2719,
    2720, 2721, 2722, 2723, 2724, 2725, 2726, 2727, 2728, 2729, 2730, 2731,
    2732, 2733, 2734, 2735, 2738, 2739, 2740, 2741, 2742, 2743, 2744, 2745,
    2746, 2747, 2748, 2749, 2750, 2751, 2752, 2753, 2754, 2755, 2756, 2757,
    2758, 2935, 2936, 2937, 2938, 2939, 2940, 2941, 2953, 2963, 3006, 3007,
    3008, 3009, 3010, 3011, 3012, 3013, 3014, 3015, 3016, 3017, 3018, 3019,
    3020, 3021, 3022, 3023, 3024, 3025, 3026, 3027, 3028, 3029, 3030, 3034,
    3035, 3038, 3039, 3040, 3041, 3042, 3043, 3044, 3045, 3046, 3047, 3048,
    3049, 3050, 3051, 3058, 3059, 3068, 3114, 3115, 3116, 3117, 3118, 3120,
    3126, 3127, 3128, 3129, 3130, 3131, 3132, 3133, 3134, 3135, 3136, 3137,
    3138, 3139, 3140, 3146, 3147, 3150, 3151, 3152, 3300, 3301, 3328, 3329,
    3330, 3331, 3332, 3333, 3334, 3335, 3346, 3350, 3351, 3352, 3366, 3386,
    3387, 3388, 3389, 3390, 3396, 3397, 3398, 3399, 3407, 3414, 3416, 3764,
    3788, 3789, 3790, 3791, 3793, 3795, 3796, 3819, 3821, 3823, 3824, 3833,
    3834, 3835, 3836, 3837, 3838, 3839, 3840, 3841, 3842, 3843, 3844, 3845,
    3846, 3847, 3848, 3849, 3850, 3851, 3852, 3854, 3873, 3874, 3875, 3876,
    3877, 3878, 3879, 3880, 3881, 3882, 3883, 3884, 3885, 3888, 3889, 3906,
    3907, 3908, 3909, 3910, 3911, 4001, 4002, 4003, 4004, 4005, 4006, 4007,
    4008, 4009, 4010, 4011, 4012, 4013, 4014, 4015, 4016, 4017, 4018, 4019,
    4020, 4021, 4022, 4023, 4024, 4025, 4026, 4027, 4028, 4029, 4030, 4031,
    4032, 4033, 4034, 4035, 4036, 4037, 4038, 4040, 4041, 4042, 4043, 4044,
    4045, 4046, 4047, 4052, 4053, 4054, 4055, 4074, 4075, 4080, 4081, 4120,
    4121, 4122, 4123, 4124, 4125, 4126, 4127, 4128, 4129, 4130, 4131, 4132,
    4133, 4134, 4135, 4136, 4137, 4138, 4139, 4140, 4141, 4142, 4143, 4144,
    4145, 4146, 4147, 4148, 4149, 4150, 4151, 4152, 4153, 4154, 4155, 4156,
    4157, 4158, 4159, 4160, 4161, 4162, 4163, 4164, 4165, 4166, 4167, 4168,
    4169, 4170, 4171, 4172, 4173, 4174, 4175, 4176, 4178, 4179, 4180, 4181,
    4182, 4183, 4184, 4185, 4188, 4189, 4190, 4191, 4192, 4193, 4194, 4195,
    4196, 4197, 4198, 4199, 4200, 4201, 4202, 4203, 4204, 4205, 4206, 4207,
    4208, 4209, 4210, 4211, 4212, 4213, 4214, 4215, 4216, 4218, 4219, 4220,
    4221, 4222, 4223, 4224, 4225, 4226, 4227, 4228, 4229, 4230, 4231, 4232,
    4233, 4234, 4235, 4236, 4237, 4238, 4239, 4240, 4241, 4242, 4243, 4244,
    4245, 4246, 4247, 4248, 4249, 4250, 4251, 4252, 4253, 4254, 4255, 4256,
    4257, 4258, 4259, 4260, 4261, 4262, 4263, 4264, 4265, 4266, 4267, 4268,
    4269, 4270, 4271, 4272, 4273, 4274, 4275, 4276, 4277, 4278, 4279, 4280,
    4281, 4282, 4283, 4284, 4285, 4286, 4287, 4288, 4289, 4291, 4292, 4293,
    4294, 4295, 4296, 4297, 4298, 4299, 4300, 4301, 4302, 4303, 4304, 4306,
    4307, 4308, 4309, 4310, 4311, 4312, 4313, 4314, 4315, 4316, 4317, 4318,
    4319, 4322, 4324, 4326, 4327, 4329, 4339, 4341, 4343, 4345, 4347, 4349,
    4351, 4353, 4355, 4357, 4359, 4361, 4363, 4365, 4367, 4369, 4371, 4373,
    4375, 4377, 4379, 4381, 4383, 4386, 4388, 4417, 4434, 4463, 4466, 4469,
    4470, 4472, 4475, 4480, 4482, 4483, 4490, 4491, 4492, 4493, 4494, 4495,
    4496, 4497, 4498, 4499, 4500, 4501, 4502, 4503, 4504, 4505, 4506, 4507,
    4508, 4509, 4510, 4511, 4512, 4513, 4514, 4515, 4516, 4517, 4518, 4519,
    4520, 4521, 4522, 4523, 4524, 4525, 4526, 4527, 4528, 4529, 4530, 4531,
    4532, 4533, 4534, 4535, 4536, 4537, 4538, 4539, 4540, 4541, 4542, 4543,
    4544, 4545, 4546, 4547, 4548, 4549, 4550, 4551, 4552, 4553, 4554, 4555,
    4557, 4558, 4568, 4569, 4570, 4571, 4572, 4573, 4574, 4575, 4576, 4577,
    4578, 4579, 4580, 4581, 4582, 4583, 4584, 4585, 4586, 4587, 4588, 4589,
    4600, 4601, 4602, 4603, 4604, 4605, 4606, 4607, 4608, 4609, 4610, 4611,
    4612, 4613, 4614, 4615, 4616, 4617, 4618, 4619, 4620, 4621, 4622, 4623,
    4624, 4625, 4626, 4627, 4628, 4629, 4630, 4631, 4632, 4633, 4634, 4635,
    4636, 4637, 4638, 4639, 4640, 4641, 4642, 4643, 4644, 4645, 4646, 4652,
    4653, 4654, 4655, 4656, 4657, 4658, 4659, 4660, 4661, 4662, 4663, 4664,
    4665, 4666, 4667, 4668, 4669, 4670, 4671, 4672, 4673, 4674, 4675, 4676,
    4677, 4678, 4679, 4680, 4681, 4682, 4683, 4684, 4685, 4686, 4687, 4688,
    4689, 4690, 4691, 4692, 4693, 4694, 4695, 4696, 4697, 4698, 4699, 4700,
    4701, 4702, 4703, 4704, 4705, 4706, 4707, 4708, 4709, 4710, 4711, 4712,
    4713, 4714, 4715, 4716, 4717, 4718, 4719, 4720, 4721, 4722, 4723, 4724,
    4725, 4726, 4727, 4728, 4729, 4730, 4731, 4732, 4733, 4734, 4735, 4736,
    4737, 4738, 4739, 4740, 4741, 4742, 4743, 4744, 4745, 4746, 4747, 4748,
    4749, 4750, 4751, 4752, 4753, 4754, 4755, 4756, 4757, 4758, 4759, 4760,
    4761, 4762, 4763, 4764, 4765, 4766, 4767, 4768, 4769, 4770, 4771, 4772,
    4773, 4774, 4775, 4776, 4777, 4778, 4779, 4780, 4781, 4782, 4783, 4784,
    4785, 4786, 4787, 4788, 4789, 4790, 4791, 4792, 4793, 4794, 4795, 4796,
    4797, 4798, 4799, 4800, 4801, 4802, 4803, 4804, 4805, 4806, 4807, 4808,
    4809, 4810, 4811, 4812, 4813, 4814, 4815, 4816, 4817, 4818, 4819, 4820,
    4821, 4822, 4823, 4824, 4839, 4855, 4856, 4857, 4858, 4859, 4860, 4861,
    4862, 4863, 4864, 4865, 4866, 4867, 4868, 4869, 4870, 4871, 4872, 4873,
    4874, 4875, 4876, 4877, 4878, 4879, 4880, 4883, 4885, 4887, 4889, 4891,
    4893, 4895, 4898, 4900, 4901, 4902, 4903, 4904, 4907, 4909, 4921, 4923,
    4925, 4927, 4929, 4931, 4933, 4935, 4937, 4939, 4941, 4943, 4945, 4947,
    4949, 4951, 4953, 4955, 4957, 4959, 4961, 4963, 4965, 4967, 4969, 4971,
    4973, 4975, 4977, 4979, 4981, 4983, 4985, 4987, 4989, 4991, 4993, 4995,
    4997, 4999, 5012, 5013, 5017, 5048, 5105, 5106, 5107, 5108, 5109, 5110,
    5111, 5112, 5113, 5114, 5115, 5116, 5117, 5118, 5119, 5120, 5121, 5122,
    5123, 5124, 5125, 5126, 5127, 5128, 5129, 5130, 5132, 5167, 5168, 5169,
    5170, 5171, 5172, 5173, 5174, 5175, 5176, 5177, 5178, 5179, 5180, 5181,
    5182, 5183, 5184, 5185, 5186, 5187, 5188, 5224, 5228, 5229, 5233, 5245,
    5246, 5251, 5252, 5253, 5254, 5255, 5256, 5257, 5258, 5259, 5263, 5264,
    5269, 5270, 5271, 5272, 5273, 5274, 5275, 5801, 5802, 5803, 5804, 5808,
    5809, 5810, 5811, 5812, 5813, 5814, 5815, 5816,
    20004, 20005, 20006, 20007, 20008, 20009, 20010, 20011, 20012, 20013,
    20014, 20015, 20016, 20017, 20018, 20019, 20020, 20021, 20022, 20023,
    20024, 20025, 20026, 20027, 20028, 20029, 20030, 20031, 20032, 20064,
    20065, 20066, 20067, 20068, 20069, 20070, 20071, 20072, 20073, 20074,
    20075, 20076, 20077, 20078, 20079, 20080, 20081, 20082, 20083, 20084,
    20085, 20086, 20087, 20088, 20089, 20090, 20091, 20092, 21413, 21414,
    21415, 21416, 21417, 21418, 21419, 21420, 21421, 21422, 21423, 21453,
    21454, 21455, 21456, 21457, 21458, 21459, 21460, 21461, 21462, 21463,
    21473, 21474, 21475, 21476, 21477, 21478, 21479, 21480, 21481, 21482,
    21483, 21896, 21897, 21898, 21899, 22171, 22172, 22173, 22174, 22175,
    22176, 22177, 22181, 22182, 22183, 22184, 22185, 22186, 22187, 22191,
    22192, 22193, 22194, 22195, 22196, 22197, 25884, 27205, 27206, 27207,
    27208, 27209, 27210, 27211, 27212, 27213, 27214, 27215, 27216, 27217,
    27218, 27219, 27220, 27221, 27222, 27223, 27224, 27225, 27226, 27227,
    27228, 27229, 27230, 27231, 27232, 27391, 27392, 27393, 27394, 27395,
    27396, 27397, 27398, 27492, 28402, 28403, 28404, 28405, 28406, 28407,
    28408, 28409, 28410, 28411, 28412, 28413, 28414, 28415, 28416, 28417,
    28418, 28419, 28420, 28421, 28422, 28423, 28424, 28425, 28426, 28427,
    28428, 28429, 28430, 28431, 28432, 28462, 28463, 28464, 28465, 28466,
    28467, 28468, 28469, 28470, 28471, 28472, 28473, 28474, 28475, 28476,
    28477, 28478, 28479, 28480, 28481, 28482, 28483, 28484, 28485, 28486,
    28487, 28488, 28489, 28490, 28491, 28492, 29701, 29702, 30161, 30162,
    30163, 30164, 30165, 30166, 30167, 30168, 30169, 30170, 30171, 30172,
    30173, 30174, 30175, 30176, 30177, 30178, 30179, 30800, 31251, 31252,
    31253, 31254, 31255, 31256, 31257, 31258, 31259, 31275, 31276, 31277,
    31278, 31279, 31281, 31282, 31283, 31284, 31285, 31286, 31287, 31288,
    31289, 31290, 31466, 31467, 31468, 31469, 31700
    ];

// Module pattern to hide internal vars
(function() {

    "use strict";

    // Module scope
    var format_geojson = new OpenLayers.Format.GeoJSON();
    // Silently ignore 3rd dimension (e.g. USGS Quakes feed)
    format_geojson.ignoreExtraDims = true;

    var marker_url_path = S3.Ap.concat('/static/img/markers/'),
        proj4326 = S3.gis.proj4326;

    // Default values if not set by the layer
    // Also in modules/s3/s3gis.py
    // http://dev.openlayers.org/docs/files/OpenLayers/Strategy/Cluster-js.html
    //var cluster_attribute_default = 'colour';
    var cluster_distance_default = 20,   // pixels
        cluster_threshold_default = 2;   // minimum # of features to form a cluster

    // Default values if not set by the map
    // Also in modules/s3/s3gis.py
    var fill_default = '#f5902e',          // fill colour for unclustered Point
        cluster_fill_default = '8087ff',   // fill colour for clustered Point
        cluster_stroke_default = '2b2f76', // stroke colour for clustered Point
        select_fill_default = 'ffdc33',    // fill colour for selected Point
        select_stroke_default = 'ff9933';  // stroke colour for selected Point

    /**
     * Main Start Function
     * - called by yepnope callback in s3.gis.loader
     *
     * Parameters:
     * map_id - {String} A unique ID for this map
     * options - {Array} An array of options for this map
     *
     * Returns:
     * {OpenLayers.Map} The openlayers map.
     */
    S3.gis.show_map = function(map_id, options) {

        if (!map_id) {
            map_id = 'default_map';
        }
        if (undefined === options) {
            // Lookup options
            options = S3.gis.options[map_id];
        }

        var projection = options.projection,
            projection_current = new OpenLayers.Projection('EPSG:' + projection);
        options.projection_current = projection_current;
        if (projection == 900913) {
            options.maxExtent = new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34);
            options.maxResolution = 156543.0339;
            options.units = 'm';
        } else if (projection == 4326) {
            options.maxExtent = new OpenLayers.Bounds(-180, -90, 180, 90);
            options.maxResolution = 1.40625;
            options.units = 'degrees';
        } else {
            var maxExtent = options.maxExtent.split(',');
            options.maxExtent = new OpenLayers.Bounds(maxExtent[0], maxExtent[1], maxExtent[2], maxExtent[3]);
            options.maxResolution = 'auto';
        }

        // Configure the Viewport
        var lat = options.lat,
            lon = options.lon,
            bounds,
            center;
        if ((lat !== undefined) && (lon !== undefined)) {
            center = new OpenLayers.LonLat(lon, lat);
            center.transform(proj4326, projection_current);
        } else {
            // BBOX
            bounds = OpenLayers.Bounds.fromArray(options.bbox);
            center = bounds.getCenterLonLat();
        }
        options.center = center;

        // Configue clustering
        if (undefined === options.cluster_label) {
            // Default to on
            options.cluster_label = true;
        }

        // Build the OpenLayers map
        var map = addMap(map_id, options);

        // Allow more room for Features
        map.Z_INDEX_BASE.Popup = 900;

        // Resize the Map when the Browser window is resized
        var map_div = $('#' + map_id + '_panel');
        map_div.css('width', '100%');
        $(window).resize(function() {
            //map.updateSize();
            var w = map_div.width();
            map.s3.mapWin.setWidth(w);
            //var h = w * 3/4;
            //map.s3.mapWin.setSize(w, h);
            //map_div.css('height', h);
        });

        // Add the GeoExt UI
        // @ToDo: Make this optional
        options.renderTo = map_id + '_panel';
        addMapUI(map);

        // If we were instantiated with bounds, use these now
        if (bounds) {
            bounds.transform(proj4326, projection_current);
            map.zoomToExtent(bounds);
        }

        // Listen to Events
        map.events.on({
            'movestart': function(/* event */) {
                // Hide any warnings (e.g. 'Too Many Features')
                S3.hideAlerts('warning');
            }
        });

        $.when(layersLoaded(map_id)).then(
            function(status) {
                // Success:
                s3_debug(status);
                // - check that Tiles are Loaded
                $.when(tilesLoaded(S3.gis.maps[map_id].baseLayer)).then(
                    function(status) {
                        // Success
                        s3_debug(status);
                        // Hide Throbber
                        hideThrobber(null, map);
                        // Set a flag to show that we've completed loading
                        // - used by gis.get_screenshot()
                        // NB: Even after all tiles are loaded, they may still
                        //     be in the drawing queue hence invisible - wait
                        //     until the tile manager has unqueued them all
                        setTimeout(function drawing() {
                            try {
                                if (map.tileManager.tileQueue[map.id].length) {
                                    setTimeout(drawing, 250);
                                } else {
                                    map.s3.loaded = true;
                                }
                            } catch(e) {
                                // What? No tile queue? Well, then we have to... :/
                                setTimeout(function() { map.s3.loaded = true; }, 50000);
                            }
                        }, 1);
                    },
                    function(status) {
                        // Failed
                        s3_debug(status);
                    },
                    function(status) {
                        // Progress
                        showThrobber(map_id);
                        s3_debug(status);
                    }
                );
            },
            function(status) {
                // Failed
                s3_debug(status);
            },
            function(status) {
                // Progress
                s3_debug(status);
            }
        );

        // Return the map object
        return map;
    };

    /**
     * Check that all Map layers are Loaded
     */
    var layersLoaded = function(map_id) {

        var dfd = new jQuery.Deferred();

        // Test every half-second
        setTimeout(function working() {
            var layers_loading = S3.gis.maps[map_id].s3.layers_loading;
            if (layers_loading.length == 0) {
                dfd.resolve('Layers loaded');
            } else if (dfd.state() === 'pending') {
                // Notify progress
                dfd.notify('waiting for Layers to load...');
                // Loop
                setTimeout(working, 250);
            } else {
                // Failed!?
            }
        }, 1);

        // Return the Promise so caller can't change the Deferred
        return dfd.promise();
    };

    /**
     * Check that all Layer Tiles are Loaded
     */
    var tilesLoaded = function(layer) {

        if (undefined === layer.numLoadingTiles) {
            return true;
        }

        var dfd = new jQuery.Deferred();

        // NB: numLoadingTiles is incremented/decremented individually per each
        //     asynchronously loading tile - thus it is 0 both before /and/ after
        //     tile loading, and sometimes even in between when loading is very
        //     fast - so we must wait for loadend before checking, otherwise the
        //     dfd will be resolved instantly with not a single tile loaded yet ;)
        layer.events.register('loadend', '', function() {
            if (layer.numLoadingTiles == 0) {
                dfd.resolve('Tiles loaded');
            } else if (dfd.state() === 'pending') {
                dfd.reject('Tile loading failed');
            } else {
                // Failed!?
            }
        });

        // Return the Promise so caller can't change the Deferred
        return dfd.promise();
    };

    /**
     * Zoom a map to the specified OpenLayers.Bounds (in WGS84: Lat/Lon)
     * - ensuring a minimal bbox & a little padding
     */
    var zoomBounds = function(map, bounds, minBBOX) {

        var bbox = bounds.toArray(),
            lon_min = bbox[0],
            lat_min = bbox[1],
            lon_max = bbox[2],
            lat_max = bbox[3];

        // Ensure a minimal BBOX in case we just have a single data point
        var min_size = minBBOX || 0.05,
            delta = (min_size - Math.abs(lon_max - lon_min)) / 2;
        if (delta > 0) {
            lon_min -= delta;
            lon_max += delta;
        }
        delta = (min_size - Math.abs(lat_max - lat_min)) / 2;
        if (delta > 0) {
            lat_min -= delta;
            lat_max += delta;
        }

        // Add an Inset in order to not have points right at the edges of the map
        var inset = min_size / 7;
        lon_min -= inset;
        lon_max += inset;
        // @todo: -90 > lat > 90 doesn't give valid bounds (returns NaN)
        lat_min = Math.max(lat_min - inset, -90.0);
        lat_max = Math.min(lat_max + inset, 90.0);
        bounds = new OpenLayers.Bounds(lon_min, lat_min, lon_max, lat_max);
        bounds.transform(proj4326, map.getProjectionObject());
        // Zoom to Bounds
        map.zoomToExtent(bounds);
    };

    // Pass to Global scope to be called from s3.ui.locationselector.js
    S3.gis.zoomBounds = zoomBounds;

    /**
     * Callback to Re-cluster Search Results after an AJAX refresh
     * - to ensure that bounds are set correctly
     */
    var search_layer_loadend = function(event) {

        // Search results have Loaded
        var layer = event.object;

        // Read Bounds for Zoom
        var bounds = layer.getDataExtent();

        // Zoom Out to Cluster
        //layer.map.zoomTo(0)
        if (bounds) {
            // Convert to WGS84: Lat/Lon
            var map = layer.map;
            bounds.transform(map.getProjectionObject(), proj4326);
            zoomBounds(map, bounds);
        }

        var strategy,
            strategies = layer.strategies;
        for (var i=0, len=strategies.length; i < len; i++) {
            strategy = strategies[i];
            if (strategy.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
                // Re-enable
                strategy.activate();
                // cacheFeatures
                strategy.features = layer.features;
                // Re-Cluster
                strategy.recluster();
                break;
            }
        }
        // Enable the layer if it isn't visible yet
        if (!layer.visibility) {
            layer.setVisibility(true);
        }
        // Disable this event
        layer.events.un({
            'loadend': search_layer_loadend
        });
    };
    // Pass to Global scope to be called from s3.dataTables.js (obsolete?)
    S3.gis.search_layer_loadend = search_layer_loadend;

    /**
     * Refresh the given layer on all maps
     * - called by s3.filter.js
     *
     * Parameters:
     * layer_id - {String} ID of the layer to be refreshed
     * queries - {Array} Optional list of Queries to be applied to the Layer
     *                   [[key, value], [key, value], ...]
     */
    S3.gis.refreshLayer = function(layer_id, queries) {

        var refreshLayer = function(layer) {

            if (layer && (layer.s3_layer_id == layer_id)) {

                var url = layer.protocol.url,
                    protocol_options = layer.protocol.options,
                    ajax_options;

                if (queries && queries.length) {

                    // Apply filters to ajax URL
                    url = S3.search.filterURL(url, queries);

                    // Convert to POST
                    ajax_options = {
                        data: [],
                        type: 'GET',
                        url: url,
                    };
                    S3.search.searchRewriteAjaxOptions(ajax_options, 'form');

                    // Update protocol options
                    protocol_options.params = ajax_options.data;
                    protocol_options.readWithPOST = true;
                    protocol_options.url = ajax_options.url;
                }

                // If map is showing then refresh the layer
                map = this.map;
                if (map.s3.mapWin.isVisible()) {

                    // Enable the layer if not visible yet
                    if (!layer.visibility) {
                        layer.setVisibility(true);
                    }

                    // Wait for layersLoaded
                    $.when(layersLoaded(this.map_id)).then(
                        function(/* status */) {

                            var strategies = layer.strategies,
                                numStrategies = strategies.length,
                                strategy,
                                i;

                            // Disable clustering until refreshed
                            for (i = 0; i < numStrategies; i++) {
                                strategy = strategies[i];
                                if (strategy.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
                                    strategy.deactivate();
                                    break;
                                }
                            }
                            // Set an event to re-enable Clustering when the layer has been reloaded
                            // - we do this only on loadstart, because if there is a previous
                            //   response (e.g. from initial layer loading after switching to
                            //   the map tab of summary), triggerRead will fire loadend first,
                            //   thereby consuming our one-off loadend handler before the reload
                            //   even starts
                            var set_search_layer_loadend = function() {
                                layer.events.on({'loadend': search_layer_loadend});
                                layer.events.un({'loadstart': set_search_layer_loadend});
                            };
                            // Close open popups before reloading
                            while (layer.map.popups.length) {
                                layer.map.removePopup(layer.map.popups[0]);
                            }
                            // Reload the layer, disabling current bounds
                            for (i = 0; i < numStrategies; i++) {
                                strategy = strategies[i];
                                if (strategy.CLASS_NAME == 'OpenLayers.Strategy.BBOX' ||
                                    strategy.CLASS_NAME == 'OpenLayers.Strategy.ZoomBBOX') {
                                    // Set bounds to maxExtent so that filter doesn't apply
                                    strategy.bounds = null;
                                    // Trigger read to reload the layer
                                    layer.events.on({
                                        'loadstart': set_search_layer_loadend
                                    });
                                    strategy.triggerRead();
                                    break;
                                }
                            }
                            // Call Custom Call-back
                            if (undefined !== map.s3.layerRefreshed) {
                                map.s3.layerRefreshed(layer);
                            }
                        },
                        function(status) {
                            // Layer-loading failed
                            s3_debug(status);
                        },
                        function(status) {
                            // Layer-loading still in progress
                            s3_debug(status);
                        }
                    );
                }
            }
        };

        var maps = S3.gis.maps,
            map_id,
            map;

        for (map_id in maps) {
            map = maps[map_id];
            map.layers.forEach(refreshLayer, {"map_id": map_id, "map": map});
        }
    };

    /**
     * Build the OpenLayers map
     */
    var addMap = function(map_id, options) {

        var fallThrough;
        if (i18n.gis_name_map) {
            // prevent the savePanel clickout handler from getting swallowed by the map
            fallThrough = true;
        } else {
            // Keep Defaults where we can
            fallThrough = false;
        }

        var tileManager = new OpenLayers.TileManager();

        var map_options = {
            // We will add these ourselves later for better control
            controls: [],
            displayProjection: proj4326,
            projection: options.projection_current,
            fallThrough: fallThrough,
            // This means that Images get hidden by scrollbars
            //paddingForPopups: new OpenLayers.Bounds(50, 10, 200, 300),
            maxResolution: options.maxResolution,
            maxExtent: options.maxExtent,
            // Apply only for ZoomToMaxExtent
            //restrictedExtent: options.restrictedExtent,
            numZoomLevels: options.numZoomLevels,
            // Use Manual stylesheet download (means can be done in HEAD to not delay page load)
            theme: null,
            tileManager: tileManager,
            units: options.units
        };

        var map = new OpenLayers.Map('center', map_options);

        // Add this map to the global list of maps
        S3.gis.maps[map_id] = map;

        // Create an Array to hold the S3 elements specific for this map
        map.s3 = {};

        // Store the map_id
        map.s3.id = map_id;

        // Store the options used to instantiate the map
        map.s3.options = options;

        // Register Plugins
        map.s3.plugins = [];
        map.registerPlugin = function(plugin) {
            plugin.map = this;
            this.s3.plugins.push(plugin);
        };

        // Layers
        addLayers(map);

        // Controls (add these after the layers)
        addControls(map);

        return map;
    };

    /**
     * Add the GeoExt UI
     */
    var addMapUI = function(map) {

        var s3 = map.s3,
            options = s3.options;

        var mapPanel = new GeoExt.MapPanel({
            //cls: 'mappanel',
            // Ignored
            //height: options.map_height,
            //width: options.map_width,
            xtype: 'gx_mappanel',
            map: map,
            center: options.center,
            zoom: options.zoom,
            plugins: []
        });

        // Pass to Global Scope
        s3.mapPanel = mapPanel;

        // Set up shortcuts to allow GXP Plugins to work (needs to find mapPanel)
        var portal = {};
        portal.map = mapPanel;
        s3.portal = portal;

        if (options.legend || options.layers_wms) {

            var layers = map.layers,
                mp_items = mapPanel.layers.data.items;

            for (var i = 0; i < layers.length; i++) {
                // Ensure that legendPanel knows about the Markers for our Feature layers
                if (layers[i].legendURL) {
                    mp_items[i].data.legendURL = layers[i].legendURL;
                }
                // Add any Custom Legend Titles
                if (layers[i].legendTitle) {
                    mp_items[i].data.title = layers[i].legendTitle;
                }
                // Ensure that mapPanel knows about whether our WMS layers are queryable
                if (layers[i].queryable) {
                    mp_items[i].data.queryable = 1;
                }
            }
        }

        // Which Elements do we want in our mapWindow?
        // @ToDo: Move all these to Plugins

        // Layer Tree
        var layerTree = addLayerTree(map);

        // Collect Items for the West Panel
        var west_panel_items = [layerTree];

        // WMS Browser
        if (options.wms_browser_url) {
            var wmsBrowser = addWMSBrowser(map);
            if (wmsBrowser) {
                west_panel_items.push(wmsBrowser);
            }
        }

        // Legend Panel
        if (options.legend) {
            var legendPanel;
            if (options.legend == 'float') {
                // Floating
                legendPanel = addLegendPanel(map);
            } else {
                // Integrated in West Panel
                legendPanel = new GeoExt.LegendPanel({
                    //cls: 'legendpanel',
                    title: i18n.gis_legend,
                    defaults: {
                        //labelCls: 'mylabel',
                        //style: 'padding:4px'
                    },
                    //bodyStyle: 'padding:4px',
                    autoScroll: true,
                    collapsible: true,
                    collapseMode: 'mini'
                    //lines: false
                });
                west_panel_items.push(legendPanel);
            }
            // Allow us to retrieve the legendPanel
            mapPanel.legendPanel = legendPanel;
        }

        // Plugins
        var plugins = s3.plugins;
        for (var j = 0, len = plugins.length; j < len; ++j) {
            plugins[j].setup(map);
            plugins[j].addToMapWindow(west_panel_items);
        }

        // Pass to Global Scope
        s3.west_panel_items = west_panel_items;

        // Instantiate the main Map window
        if (options.window) {
            addMapWindow(map);
        } else {
            // Embedded Map
            addMapPanel(map);
        }

        // Trigger a layout update on the westPanelContainer
        // - this fixes up layout if the layerTree has scrollbars initially
        var westPanelContainer = s3.westPanelContainer;
        westPanelContainer.fireEvent('collapse');
        window.setTimeout(function() {
            westPanelContainer.fireEvent('expand');
        }, 300);

        // Disable throbber when unchecked
        layerTree.root.eachChild( function() {
            // no layers at top-level, so recurse inside
            this.eachChild( function() {
                if (this.isLeaf()) {
                    this.on('checkchange', function(event, checked) {
                        if (!checked) {
                            // Cancel any associated throbber
                            hideThrobber(this.layer);
                        }
                    });
                } else {
                    // currently this will not be hit, but when we have sub-folders it will (to 1 level)
                    this.eachChild( function() {
                        if (this.isLeaf()) {
                            this.on('checkchange', function(event, checked) {
                                if (!checked) {
                                    // Cancel any associated throbber
                                    hideThrobber(this.layer);
                                }
                            });
                        }
                    });
                }
            });
        });

        // Toolbar Tooltips
        Ext.QuickTips.init();
    };

    /**
     * Create an embedded Map Panel
     * - this is also called when a fullscreen map is made to go embedded
     */
    var addMapPanel = function(map) {

        var s3 = map.s3,
            options = s3.options;

        var westPanelContainer = addWestPanel(map);
        var mapPanelContainer = addMapPanelContainer(map);

        var mapWin = new Ext.Panel({
            //cls: 'gis-map-panel',
            renderTo: options.renderTo,
            //autoScroll: true, // Having this on adds scrollbars which make map navigation awkward as the map size is always large enough to trigger these :/
                                // Having this off means the map is completely unresponsive
            autoWidth: true,
            //maximizable: true,
            titleCollapse: true,
            height: options.map_height,
            //width: options.map_width,
            layout: 'border',
            items: [
                westPanelContainer,
                mapPanelContainer
            ]
        });

        // Pass to global scope
        s3.mapWin = mapWin;
    };
    // Pass to global scope so that s3.gis.fullscreen.js can call it to return from fullscreen
    S3.gis.addMapPanel = addMapPanel;

    /**
     * Create a floating Map Window
     */
    var addMapWindow = function(map) {

        var s3 = map.s3,
            options = s3.options;

        var westPanelContainer = addWestPanel(map);
        var mapPanelContainer = addMapPanelContainer(map);

        var mapWin = new Ext.Window({
            cls: 'gis-map-window',
            collapsible: false,
            constrain: true,
            closable: !options.windowNotClosable,
            closeAction: 'hide',
            autoScroll: true,
            maximizable: options.maximizable,
            titleCollapse: false,
            height: options.map_height,
            width: options.map_width,
            layout: 'border',
            items: [
                westPanelContainer,
                mapPanelContainer
            ]
        });

        mapWin.on('beforehide', function(mw) {
            if (mw.maximized) {
                mw.restore();
            }
        });

        mapWin.on('move', function(/* mw */) {
            map.events.clearMouseCache();
        });

        mapWin.on('resize', function(mw, width, height) {
            // Tweak the CSS for Legend & Save Panels based on browser height
            //var height = $('.gis-map-window .x-window-bwrap').height();
            if (height < 842) {
                $('#' + s3.id).removeClass('a0 a1 a2 a3')
                              .addClass('a4');
            } else if (height < 1191) {
                $('#' + s3.id).removeClass('a0 a1 a2 a4')
                              .addClass('a3');
            } else if (height < 1684) {
                $('#' + s3.id).removeClass('a0 a1 a3 a4')
                              .addClass('a2');
            } else if (height < 2384) {
                $('#' + s3.id).removeClass('a0 a2 a3 a4')
                              .addClass('a1');
            } else {
                $('#' + s3.id).removeClass('a1 a2 a3 a4')
                              .addClass('a0');
            }
        });

        // Set Options
        if (!options.windowHide) {
            // If the window is meant to be displayed immediately then display it now that it is ready
            mapWin.show();
            mapWin.maximize();
        }

        // pass to Global Scope
        s3.mapWin = mapWin;
    };
    // Pass to global scope so that s3.gis.fullscreen.js can call it to go fullscreen
    S3.gis.addMapWindow = addMapWindow;

    /**
     * Put into a Container to allow going fullscreen from a BorderLayout
     */
    var addWestPanel = function(map) {

        var s3 = map.s3,
            west_collapsed = s3.options.west_collapsed || false;

        var mapWestPanel = new Ext.Panel({
            //cls: 'gis_west',
            header: false,
            border: false,
            split: true,
            items: s3.west_panel_items
        });

        var autoWidth;
        if (Ext.isChrome) {
            // Chrome is buggy with autoWidth :/
            autoWidth = false;
        } else {
            autoWidth = true;
        }

        var westPanelContainer = new Ext.Panel({
            cls: 'gis_west',
            region: 'west',
            //header: true,
            header: false, // Can't collapse Panel if this is hidden unless we create custom control
            border: true,
            //autoScroll: true,
            autoWidth: autoWidth,
            width: 250,
            collapsible: true,
            collapseMode: 'mini',
            collapsed: west_collapsed,
            items: [
                mapWestPanel
            ]/*, @ToDo: Provide custom control to collapse westPanel without a header
            listeners: {
                collapse: function(panel) {
                    console.log('collapsed');
                    //'<div class="x-layout-cmini-east x-layout-mini"></div>'
                    //onClick() { toggleCollapse()};
                },
                expand: function(panel) {
                    console.log('expanded');
                }
            }*/
        });
        // Pass to Global Scope for s3.gis.fullscreen.js
        s3.westPanelContainer = westPanelContainer;
        return westPanelContainer;
    };

    /**
     * Put into a Container to allow going fullscreen from a BorderLayout
     * - we had to put the mapPanel inside a 'card' container for the Google Earth Panel
     * - since this is deprecated, we are free to redesign this
     */
    var addMapPanelContainer = function(map) {

        var s3 = map.s3,
            options = s3.options,
            toolbar;

        // Toolbar
        if (options.toolbar) {
            toolbar = addToolbar(map);
        } else {
            // Enable Controls which we may want independent of the Toolbar
            var active;
            if (options.draw_feature) {
                active = options.draw_feature == 'active';
                addPointControl(map, null, active);
            }
            if (options.draw_line) {
                active = options.draw_line == 'active';
                addLineControl(map, null, active);
            }
            if (options.draw_polygon) {
                active = options.draw_polygon == 'active';
                addPolygonControl(map, null, active, true);
            }
            if (options.draw_circle) {
                active = options.draw_circle == 'active';
                addCircleControl(map, null, active);
            }
            addThrobber(map);
        }
        if (options.save == 'float') {
            addSavePanel(map);
        }

        var mapPanelContainer = new Ext.Panel({
            layout: 'card',
            region: 'center',
            cls: 'mappnlcntr',
            defaults: {
                // applied to each contained panel
                border: false
            },
            items: [
                s3.mapPanel
            ],
            activeItem: 0,
            tbar: toolbar,
            scope: this
        });
        // Pass to Global Scope for s3.gis.fullscreen.js (and was for addGoogleEarthControl)
        s3.mapPanelContainer = mapPanelContainer;

        /*
        if (options.Google && options.Google.Earth) {
            // Instantiate afresh after going fullscreen as fails otherwise
            var googleEarthPanel = new gxp.GoogleEarthPanel({
                mapPanel: s3.mapPanel
            });
            // Add now rather than when button pressed as otherwise 1st press doesn't do anything
            mapPanelContainer.items.items.push(googleEarthPanel);
            // Pass to global scope to be accessible from addGoogleEarthControl & addGoogleEarthKmlLayers
            s3.googleEarthPanel = googleEarthPanel;
            // Pass to global scope to be accessible from googleEarthKmlLoaded callback
            // => max 1/page!
            S3.gis.googleEarthPanel = googleEarthPanel;
        } */

        return mapPanelContainer;
    };

    /**
     * Add LayerTree (to be called after the layers are added)
     */
    var addLayerTree = function(map) {

        // Extend LayerNodeUI to not force a folder with Radio buttons to have one active
        // - so opening folder doesn't open first layer
        // - so we can deselect a layer
        GeoExt.tree.LayerNodeUIS3 = Ext.extend(GeoExt.tree.LayerNodeUI, {
            onClick: function(e) {
                if (e.getTarget('.x-tree-node-cb', 1)) {

                    var node = this.node,
                        attributes = node.attributes,
                        group = attributes.checkedGroup;

                    if (group && group !== 'baselayer') {
                        // Radio button folders need different behaviour
                        var checked = !attributes.checked;
                        attributes.checked = checked;
                        node.ui.checkbox.checked = checked;
                        node.layer.setVisibility(checked);
                        this.enforceOneVisible();
                    } else {
                        // Normal behaviour for Checkbox folders & Base Layers folder
                        this.toggleCheck(this.isChecked());
                    }
                } else {
                    GeoExt.tree.LayerNodeUI.superclass.onClick.apply(this, arguments);
                }
            },
            enforceOneVisible: function() {

                var attributes = this.node.attributes,
                    group = attributes.checkedGroup;

                // If we are in the baselayer group, the map will take care of
                // enforcing visibility.
                if (group && group !== 'baselayer') {

                    var layer = this.node.layer,
                        checkedNodes = this.node.getOwnerTree().getChecked();

                    //var checkedCount = 0;
                    // enforce "not more than one visible"
                    Ext.each(checkedNodes, function(n){
                        var l = n.layer;
                        if (!n.hidden && n.attributes.checkedGroup === group) {
                            //checkedCount++;
                            if (l != layer && attributes.checked) {
                                l.setVisibility(false);
                            }
                        }
                    });
                    /*if (!emptyok) {
                        // enforce "at least one visible"
                        if(checkedCount === 0 && attributes.checked == false) {
                            layer.setVisibility(true);
                        }
                    }*/
                }
            }
        });

        // Extend LayerNode to use our new LayerNodeUIS3
        GeoExt.tree.LayerNodeS3 = Ext.extend(GeoExt.tree.LayerNode, {
            constructor: function(/* config */) {
                this.defaultUI = GeoExt.tree.LayerNodeUIS3;
                GeoExt.tree.LayerNodeS3.superclass.constructor.apply(this, arguments);
            }
        });
        Ext.tree.TreePanel.nodeTypes.gx_layer = GeoExt.tree.LayerNodeS3;

        var s3 = map.s3,
            options = s3.options,
            base,
            overlays,
            expanded,
            folders_radio,
            collapsible;

        if (options.hide_base) {
            base = false;
        } else {
            base = true;
        }
        if (options.hide_overlays) {
            overlays = false;
        } else {
            overlays = true;
        }
        // @ToDo: Make this a per-Folder config
        if (options.folders_closed) {
            expanded = false;
        } else {
            expanded = true;
        }
        // @ToDo: Make this a per-Folder config
        if (options.folders_radio) {
            folders_radio = true;
        } else {
            folders_radio = false;
        }
        if (options.wms_browser_url || (options.legend && options.legend != 'float')) {
            collapsible = true;
        } else {
            collapsible = false;
        }

        var layerStore = s3.mapPanel.layers,
            nodesArr = [];

        var leaf_listeners = {
            click: function(node) {
                // Provide a bigger click target area, by allowing click on layer name as well as checkbox/radio
                var attributes = node.attributes;
                if (attributes.checkedGroup == 'baselayer') {
                    // Base Layer - allow normal behaviour
                    node.ui.toggleCheck(!node.ui.isChecked());
                } else {
                    // Overlay
                    var checked = !attributes.checked;
                    attributes.checked = checked;
                    node.ui.checkbox.checked = checked;
                    node.layer.setVisibility(checked);
                }
            }
        };

        var updateLayout = function() {
            // Trigger a layout update on the westPanelContainer
            var westPanelContainer = s3.westPanelContainer;
            westPanelContainer.fireEvent('collapse');
            window.setTimeout(function() {
                westPanelContainer.fireEvent('expand');
            }, 300);
        };
        var folder_listeners = {
            collapse: function(/* node */) {
                // Trigger a layout update on the westPanelContainer
                updateLayout();
            },
            expand: function(/* node */) {
                // Trigger a layout update on the westPanelContainer
                updateLayout();
            }
        };

        if (base) {
            // Default Folder for Base Layers
            var layerTreeBase = {
                text: i18n.gis_base_layers,
                nodeType: 'gx_baselayercontainer',
                layerStore: layerStore,
                loader: {
                    baseAttrs: {
                        listeners: leaf_listeners
                    },
                    filter: function(record) {
                        var layer = record.getLayer();
                        return layer.displayInLayerSwitcher === true &&
                               layer.isBaseLayer === true &&
                               (layer.dir === undefined || layer.dir === '');
                    }
                },
                leaf: false,
                listeners: folder_listeners,
                singleClickExpand: true,
                expanded: expanded
            };
            nodesArr.push(layerTreeBase);
        }

        if (overlays) {
            // Default Folder for Overlays
            var layerTreeOverlays = {
                text: i18n.gis_overlays,
                nodeType: 'gx_overlaylayercontainer',
                layerStore: layerStore,
                loader: {
                    baseAttrs: {
                        listeners: leaf_listeners
                    },
                    filter: function(record) {
                        var layer = record.getLayer();
                        return layer.displayInLayerSwitcher === true &&
                               layer.isBaseLayer === false &&
                               (layer.dir === undefined || layer.dir === '');
                    }
                },
                leaf: false,
                listeners: folder_listeners,
                singleClickExpand: true,
                expanded: expanded
            };
            nodesArr.push(layerTreeOverlays);
        }

        // User-specified Folders
        var dirs = map.s3.dirs, // A simple Array of folder names: []
            len = dirs.length;
        if (len) {
            // Extend GeoExt to support sub-folders
            GeoExt.tree.LayerLoaderS3 = function(config) {
                Ext.apply(this, config);
                GeoExt.tree.LayerLoaderS3.superclass.constructor.call(this);
            };
            Ext.extend(GeoExt.tree.LayerLoaderS3, GeoExt.tree.LayerLoader, {
                load: function(node, callback) {
                    if (this.fireEvent('beforeload', this, node)) {
                        this.removeStoreHandlers();
                        // Clear all current children
                        while (node.firstChild) {
                            node.removeChild(node.firstChild);
                        }

                        if (!this.uiProviders) {
                            this.uiProviders = node.getOwnerTree().getLoader().uiProviders;
                        }

                        // Add Layers
                        if (!this.store) {
                            this.store = GeoExt.MapPanel.guess().layers;
                        }
                        this.store.each(function(record) {
                            this.addLayerNode(node, record);
                        }, this);
                        this.addStoreHandlers(node);

                        // Add Folders
                        var children = node.attributes.children,
                            len = children.length;
                        if (len) {
                            var child,
                                dir,
                                sibling;
                            for (var i=0; i < len; i++) {
                                dir = children[i];
                                //child = this.createNode(dir); // Adds baseAttrs which we don't want
                                child = new Ext.tree.TreePanel.nodeTypes[dir.nodeType](dir);
                                sibling = node.item(0);
                                if (sibling) {
                                    node.insertBefore(child, sibling);
                                } else {
                                    node.appendChild(child);
                                }
                            }
                        }

                        if (typeof callback == 'function') {
                            callback();
                        }

                        this.fireEvent('load', this, node);
                    }
                }
            });

            var baseAttrs,
                child,
                children,
                dir,
                _dir,
                _dirs,
                _dirslength,
                folder,
                folders = {},
                _folders,
                i,
                j,
                loader,
                parent,
                sub;

            // Place folders into subfolders
            for (i = 0; i < len; i++) {
                dir = dirs[i];
                _dirs = dir.split('/');
                _dirslength = _dirs.length;
                for (j = 0; j < _dirslength; j++) {
                    if (j == 0) {
                        // Top level
                        _folders = folders;
                    } else {
                        parent = folder;
                        _folders = _folders[parent];
                    }
                    folder = _dirs[j];
                    if (!_folders.hasOwnProperty(folder)) {
                        // Not yet in Hash, so add it
                        _folders[folder] = {};
                    }
                }
            }
            for (dir in folders) {
                _dir = folders[dir];
                children = [];
                // @ToDo: Recursive (currently just 1 layer)
                for (sub in _dir) {
                    baseAttrs = {
                        listeners: leaf_listeners
                    };
                    // @ToDo: Allow per-folder configuration
                    if (folders_radio) {
                        // @ToDo: Don't assume all folders have unique names
                        baseAttrs.checkedGroup = sub;
                    }
                    loader = new GeoExt.tree.LayerLoaderS3({
                        baseAttrs: baseAttrs,
                        filter: (function(dir, sub) {
                            return function(read) {
                                if (read.data.layer.dir !== 'undefined') {
                                    return read.data.layer.dir === dir + '/' + sub;
                                }
                            };
                        })(dir, sub)
                    });
                    child = {
                        text: sub,
                        nodeType: 'gx_layercontainer',
                        layerStore: layerStore,
                        // @ToDo: Sub-folders
                        children: [],
                        loader: loader,
                        leaf: false,
                        listeners: folder_listeners,
                        singleClickExpand: true,
                        expanded: expanded
                    };
                    children.push(child);
                }
                baseAttrs = {
                    listeners: leaf_listeners
                };
                // @ToDo: Allow per-folder configuration
                if (folders_radio) {
                    // @ToDo: Don't assume all folders have unique names
                    baseAttrs.checkedGroup = dir;
                }
                loader = new GeoExt.tree.LayerLoaderS3({
                    baseAttrs: baseAttrs,
                    filter: (function(dir) {
                        return function(read) {
                            if (read.data.layer.dir !== 'undefined') {
                                return read.data.layer.dir === dir;
                            }
                        };
                    })(dir)
                });
                child = {
                    text: dir,
                    nodeType: 'gx_layercontainer',
                    layerStore: layerStore,
                    children: children,
                    loader: loader,
                    leaf: false,
                    listeners: folder_listeners,
                    singleClickExpand: true,
                    expanded: expanded
                };
                nodesArr.push(child);
            }
        }

        var treeRoot = new Ext.tree.AsyncTreeNode({
            expanded: true,
            children: nodesArr
        });

        var clear_layers = options.clearlayers & options.clearlayers != 'toolbar',
            tbar;

        if (clear_layers || i18n.gis_properties || i18n.gis_uploadlayer) {
            tbar = new Ext.Toolbar();
        } else {
            tbar = null;
        }

        var layerTree = new Ext.tree.TreePanel({
            //cls: 'gis_layer_tree',
            //height: options.map_height,
            title: i18n.gis_layers,
            loaderloader: new Ext.tree.TreeLoader({applyLoader: false}),
            root: treeRoot,
            rootVisible: false,
            split: true,
            //autoScroll: true,
            //containerScroll: true,
            collapsible: collapsible,
            collapseMode: 'mini',
            lines: false,
            tbar: tbar,
            enableDD: false
        });
        new Ext.tree.TreeSorter(layerTree, {
            sortType: function(value, node) {
                if (node.attributes.nodeType == 'gx_baselayercontainer') {
                    // Base layers always first
                    return ' ';
                } else if (node.attributes.nodeType == 'gx_overlaylayercontainer') {
                    // Default Overlays always second
                    return '!';
                } else {
                    // Alpha-sort the rest
                    return node.text;
                }
            }
        });

        // Add/Remove Layers
        if (i18n.gis_uploadlayer) {
            addRemoveLayersControl(map, layerTree);
        }
        // Layer Properties
        if (i18n.gis_properties) {
            addLayerPropertiesButton(map, layerTree);
        }
        // Clear Layers
        if (clear_layers) {
            addClearLayersButton(map, layerTree.getTopToolbar());
        }

        return layerTree;
    };

    /**
     * Add WMS Browser
     */
    var addWMSBrowser = function(map) {

        var options = map.s3.options;

        var root = new Ext.tree.AsyncTreeNode({
            expanded: true,
            loader: new GeoExt.tree.WMSCapabilitiesLoader({
                url: OpenLayers.ProxyHost + options.wms_browser_url,
                layerOptions: {buffer: 1, singleTile: false, ratio: 1, wrapDateLine: true},
                layerParams: {'TRANSPARENT': 'TRUE'},
                // customize the createNode method to add a checkbox to nodes
                createNode: function(attr) {
                    attr.checked = attr.leaf ? false : undefined;
                    return GeoExt.tree.WMSCapabilitiesLoader.prototype.createNode.apply(this, [attr]);
                }
            })
        });
        var wmsBrowser = new Ext.tree.TreePanel({
            //cls: 'wmsbrowser',
            title: options.wms_browser_name,
            root: root,
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            listeners: {
                // Add layers to the map when checked, remove when unchecked.
                // Note that this does not take care of maintaining the layer
                // order on the map.
                'checkchange': function(node, checked) {
                    if (checked === true) {
                        map.addLayer(node.attributes.layer);
                    } else {
                        map.removeLayer(node.attributes.layer);
                    }
                }
            }
        });

        return wmsBrowser;
    };

    /* Layers */

    // @ToDo: Rewrite with layers as inheriting classes

    /**
     * Show the Throbber
     */
    var showThrobber = function(map_id) {

        $('#' + map_id + ' .layer_throbber').show().removeClass('hide');
    };

    /**
     * Hide the Throbber
     * - if all layers have removed their link to it
     */
    var hideThrobber = function(layer, map) {

        var s3,
            layers_loading;

        if (layer) {
            s3 = layer.map.s3;
            layers_loading = s3.layers_loading;
            layers_loading.pop(layer.s3_layer_id);
        } else {
            s3 = map.s3;
            layers_loading = map.s3.layers_loading;
        }
        if (layers_loading.length === 0) {
            $('#' + s3.id + ' .layer_throbber').hide().addClass('hide');
        }
    };

    /**
     * Callback for all layers on 'loadstart'
     * - show Throbber
     */
    var layer_loadstart = function(event) {

        var layer = event.object,
            s3 = layer.map.s3;

        showThrobber(s3.id);

        var layer_id = layer.s3_layer_id;

        //s3_debug('Loading Layer ' + layer_id);
        var layers_loading = s3.layers_loading;
        if (layers_loading.indexOf(layer_id) == -1) { // we never want 2 pushed
            layers_loading.push(layer_id);
        }
    };

    /**
     * Callback for all layers on 'loadend'
     * - cancel Throbber (unless other layers have a lock on it still)
     * - report if too many features to download and display
     * - parse S3 custom parameters
     */
    var layer_loadend = function(event) {

        var layer = event.object,
            response = event.response,
            s3,
            priv;

        if (response && response.priv) {
            priv = response.priv;
            try {
                s3 = JSON.parse(priv.responseText).s3;
            } catch(e) {}
        } else {
            // Hide the Throbber
            hideThrobber(layer);
            // Nothing more to do
            return;
        }

        var restyle,
            features,
            features_len,
            marker_url,
            i;

        if (undefined !== s3) {

            var strategies = layer.strategies,
                numStrategies = strategies.length,
                strategy;

            // Read custom data in GeoJSON response
            //s3_debug(s3);
            if (undefined !== s3.level) {
                // We are displaying aggregated data
                // - update the strategy with the level of aggregation
                for (i = 0; i < numStrategies; i++) {
                    strategy = strategies[i];
                    if (strategy.CLASS_NAME == 'OpenLayers.Strategy.ZoomBBOX') {
                        strategy.level = s3.level;
                        break;
                    }
                }
            }
            if (undefined !== s3.style) {
                // Apply the style to the layer
                restyle = true;

                var style = s3.style,
                    result = createStyleMap(layer.map, style);

                marker_url = result[1];
                layer.legendURL = marker_url;
                layer.styleMap = result[0]; // featureStyleMap
                layer.s3_popup_format = style.popup_format;
                layer.s3_style = style.style;
                layer.s3_url_format = style.url_format;
                // Update the cluster strategy
                for (i = 0; i < numStrategies; i++) {
                    strategy = strategies[i];
                    if (strategy.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
                        var cluster_threshold = cluster_threshold_default;
                        if (style.cluster_threshold !== undefined) {
                            cluster_threshold = style.cluster_threshold;
                        }
                        if (cluster_threshold) {
                            var cluster_distance = style.cluster_distance || cluster_distance_default;
                            if ((!strategy.active) || (cluster_distance != strategy.distance) || (cluster_threshold != strategy.threshold)) {
                                // Configure
                                strategy.distance = cluster_distance;
                                strategy.threshold = cluster_threshold;
                                // Enable
                                strategy.activate();
                                // cacheFeatures
                                strategy.features = layer.features;
                                // Re-Cluster
                                strategy.recluster();
                            }
                        } else if (strategy.active) {
                            // Disable
                            strategy.deactivate();
                            // Remove existing clusters & restore member features
                            features = layer.features;
                            features_len = features.length;
                            var j,
                                cluster,
                                _cluster,
                                clusters = [],
                                cluster_len,
                                new_features = [];
                            for (i = 0; i < features_len; i++) {
                                if (features[i].cluster) {
                                    cluster = features[i];
                                    _cluster = cluster.cluster;
                                    cluster_len = _cluster.length;
                                    for (j = 0; j < cluster_len; j++) {
                                        new_features.push(_cluster[j]);
                                    }
                                    clusters.push(cluster);
                                }
                            }
                            layer.removeFeatures(clusters);
                            layer.addFeatures(new_features);
                        }
                        break;
                    }
                }
            }
        }

        // Hide the Throbber
        hideThrobber(layer);

        var rules;
        if (priv.status == 509) {
            S3.showAlert(i18n.gis_too_many_features, 'warning');
        } else {
            // Do we need to re-calculate the style for coloured Polygons?
            var s3_style = layer.s3_style;
            if (s3_style && Object.prototype.toString.call(s3_style) === '[object Array]' && s3_style.length == 1) {
                rules = reStyle(layer);
                restyle = true;
            }
        }

        if (undefined !== restyle) {
            // Redraw the features with the new styleMap
            features = layer.features;
            features_len = features.length;
            for (i = 0; i < features_len; i++) {
                layer.drawFeature(features[i]);
            }

            // Redraw the Legend
            var legendPanel = layer.map.s3.mapPanel.legendPanel;
            if (legendPanel) {

                // Find the right layerLegend
                var layerLegend,
                    layerLegends = legendPanel.items.items,
                    layerLegends_len = layerLegends.length,
                    s3_layer_id = layer.s3_layer_id;

                for (i=0; i < layerLegends_len; i++) {
                    layerLegend = layerLegends[i];
                    if ((layerLegend.layer) && (layerLegend.layer.s3_layer_id == s3_layer_id)) {
                        // @ToDo: Fix this - not currently working
                        var record;
                        if (undefined !== rules) {
                            if (layerLegend.xtype == 'gx_vectorlegend') {
                                layerLegend.rules = rules;
                                layerLegend.update();
                            } else {
                                // Need to change the type
                                record = layerLegend.layerRecord;
                                legendPanel.removeLegend(record);
                                legendPanel.addLegend(record, i);
                            }
                        } else if (undefined !== marker_url) {
                            if (layerLegend.xtype == 'gx_urllegend') {
                                layerLegend.layerRecord.data.legendURL = marker_url;
                                layerLegend.update();
                            } else {
                                // Need to change the type
                                record = layerLegend.layerRecord;
                                record.data.legendURL = marker_url;
                                legendPanel.removeLegend(record);
                                legendPanel.addLegend(record, i);
                            }
                        }
                        break;
                    }
                }
            }
        }
    };

    /**
     * Re-style a layer dynamically based on the data contents
     */
    var reStyle = function(layer) {

        var defaults = layer.s3_style[0];

        // Read the data
        var prop = defaults.prop,
            features = layer.features,
            features_len = features.length,
            i,
            data = [];

        for (i = 0; i < features_len; i++) {
            data.push(features[i].attributes[prop]);
        }

        // Sort the data
        data.sort(function(a, b) {
            return a - b;
        });

        // How many unique values do we have?
        var seen = {};
        $.each(data, function(){
            seen[this] = 1;
        });

        // How many classes should we use?
        // Color schemes from ColorBrewer2.org
        // YlOrRd sequential schemes from ColorBrewer which are colorblind-safe, print-friendly and photocopy-safe
        var numClasses = Object.keys(seen).length,
            colors;
        if (numClasses >= 5) {
            numClasses = 5;
            colors = ['ffffb2', 'fecc5c', 'fd8d3c', 'f03b20', 'bd0026'];
        } else if (numClasses == 4) {
            colors = ['ffffb2', 'fecc5c', 'fd8d3c', 'e31a1c'];
        } else if (numClasses == 3) {
            colors = ['ffeda0', 'feb24c', 'f03b20'];
        } else if (numClasses == 2) {
            colors = ['ffeda0', 'f03b20'];
        } else if (numClasses == 1) {
            colors = ['feb24c'];
        }

        // What is the size of each class?
        var classSize = Math.round(features_len / numClasses),
            step = classSize;

        // Set first value
        var breaks = [data[0]];
        for (i = 1; i < numClasses; i++) {
            breaks[i] = data[step] || data[features_len - 1];
            step += classSize;
        }
        // Set last value
        breaks.push(data[features_len - 1]);

        var low,
            high,
            _style,
            style = [];

        for (i=0; i < numClasses; i++) {
            low = breaks[i];
            high = breaks[i + 1];
            _style = $.extend({}, defaults); // Make a copy
            _style.fill = colors[i];
            _style.low = low;
            _style.high = high;
            if (low == high) {
                _style.label = low.toString();
            } else {
                _style.label = low + ' - ' + high;
            }
            style.push(_style);
        }

        // Build and apply the new rules
        var _layer = {'style': style,
                      'cluster_threshold': 0,
                      'opacity': 0.9 // trigger the 'select' renderIntent -> Opaque
                      };
        var rules = styleRules(_layer);
        layer.styleMap.styles['default'].rules = rules;

        return rules;
    };

    /**
     * Callback for all layers on 'visibilitychanged'
     * - show legendPanel if not displayed
     */
    var layer_visibilitychanged = function(event) {

        showLegend(event.object.map);
    };

    /**
     * Add Layers from the Catalogue
     * - private function called from addMap()
     *
     * Parameters:
     * map - {OpenLayers.Map}
     *
     * Returns:
     * {null}
     */
    var addLayers = function(map) {

        var s3 = map.s3,
            options = s3.options;

        // List of folders for the LayerTree
        s3.dirs = [];

        // Counter to know whether there are layers still loading
        s3.layers_loading = [];

        // List of layer names to exclude from Popups
        s3.layers_nopopups = [];

        // @ToDo: Strategy to allow common clustering of multiple layers
        //s3.common_cluster_strategy = new OpenLayers.Strategy.AttributeClusterMultiple({
        //    attribute: 'colour',
        //    distance: cluster_distance_default,
        //    threshold: cluster_threshold_default
        //})

        var i;
        /* Base Layers */
        // OSM
        if (options.layers_osm) {
            var layers_osm = options.layers_osm;
            for (i = layers_osm.length; i > 0; i--) {
                addOSMLayer(map, layers_osm[i - 1]);
            }
        }
        // Google
        try {
            // Only load Google layers if GoogleAPI downloaded ok
            // - allow rest of map to work offline
            if (options.Google) {
                addGoogleLayers(map);
            }
        } catch(e) {}

        // Bing
        if (options.Bing) {
            addBingLayers(map);
        }
        // TMS
        if (options.layers_tms) {
            var layers_tms = options.layers_tms;
            for (i = layers_tms.length; i > 0; i--) {
                addTMSLayer(map, layers_tms[i - 1]);
            }
        }
        // WMS
        if (options.layers_wms) {
            var layers_wms = options.layers_wms;
            for (i = layers_wms.length; i > 0; i--) {
                addWMSLayer(map, layers_wms[i - 1]);
            }
        }
        // XYZ
        if (options.layers_xyz) {
            var layers_xyz = options.layers_xyz;
            for (i = layers_xyz.length; i > 0; i--) {
                addXYZLayer(map, layers_xyz[i - 1]);
            }
        }
        // Empty
        if (options.EmptyLayer) {
            var layer = new OpenLayers.Layer(options.EmptyLayer.name, {
                    isBaseLayer: true,
                    displayInLayerSwitcher: true,
                    // This is used to Save State
                    s3_layer_id: options.EmptyLayer.id,
                    s3_layer_type: 'empty'
                }
            );
            map.addLayer(layer);
            if (options.EmptyLayer.base) {
                map.setBaseLayer(layer);
            }
        }
        // Raw Javascript layers
        if (options.layers_js) {
            var layers_js = options.layers_js;
            for (i = layers_js.length; i > 0; i--) {
                eval(map, layers_js[i - 1]);
            }
        }

        /* Overlays */
        // Theme
        if (options.layers_theme) {
            var layers_theme = options.layers_theme;
            for (i = layers_theme.length; i > 0; i--) {
                addGeoJSONLayer(map, layers_theme[i - 1]);
            }
        }
        // GeoJSON
        if (options.layers_geojson) {
            var layers_geojson = options.layers_geojson;
            for (i = layers_geojson.length; i > 0; i--) {
                addGeoJSONLayer(map, layers_geojson[i - 1]);
            }
        }
        // GPX
        if (options.layers_gpx) {
            var layers_gpx = options.layers_gpx;
            for (i = layers_gpx.length; i > 0; i--) {
                addGPXLayer(map, layers_gpx[i - 1]);
            }
        }
        // ArcGIS REST
        if (options.layers_arcrest) {
            var layers_arcrest = options.layers_arcrest;
            for (i = layers_arcrest.length; i > 0; i--) {
                addArcRESTLayer(map, layers_arcrest[i - 1]);
            }
        }
        // CoordinateGrid
        if (options.CoordinateGrid) {
            addCoordinateGrid(map);
        }
        // GeoRSS
        if (options.layers_georss) {
            var layers_georss = options.layers_georss;
            for (i = layers_georss.length; i > 0; i--) {
                addGeoJSONLayer(map, layers_georss[i - 1]);
            }
        }
        // KML
        if (options.layers_kml) {
            var layers_kml = options.layers_kml;
            for (i = layers_kml.length; i > 0; i--) {
                addKMLLayer(map, layers_kml[i - 1]);
            }
        }
        // OpenWeatherMap
        if (options.layers_openweathermap) {
            addOWMLayers(map);
        }
        // Shapefiles
        if (options.layers_shapefile) {
            var layers_shapefile = options.layers_shapefile;
            for (i = layers_shapefile.length; i > 0; i--) {
                addGeoJSONLayer(map, layers_shapefile[i - 1]);
            }
        }
        // WFS
        if (options.layers_wfs) {
            var layers_wfs = options.layers_wfs;
            for (i = layers_wfs.length; i > 0; i--) {
                addWFSLayer(map, layers_wfs[i - 1]);
            }
        }
        // Feature Queries from Mapping API
        if (options.feature_queries) {
            var feature_queries = options.feature_queries;
            for (i = feature_queries.length; i > 0; i--) {
                addGeoJSONLayer(map, feature_queries[i - 1]);
            }
        }
        // Feature Resources (e.g. Search Results or S3Profile)
        if (options.feature_resources) {
            var feature_resources = options.feature_resources;
            for (i = feature_resources.length; i > 0; i--) {
                addGeoJSONLayer(map, feature_resources[i - 1]);
            }
        }
        // Feature Layers from Catalogue
        if (options.layers_feature) {
            var layers_feature = options.layers_feature;
            for (i = layers_feature.length; i > 0; i--) {
                addGeoJSONLayer(map, layers_feature[i - 1]);
            }
        }
        // Draft Layers
        var draftLayer;
        if (options.features || options.draw_feature || options.draw_polygon || options.draw_circle || navigator.geolocation) {
            draftLayer = addDraftLayer(map);
        }
        // Simple Features
        // e.g. S3LocationSelectorWidget
        if (options.features) {

            var features = options.features,
                current_projection = map.getProjectionObject();

            //var parseFeature = format_geojson.parseFeature;
            //var parseGeometry = format_geojson.parseGeometry;
            for (i = 0; i < features.length; i++) {
                var feature = format_geojson.parseFeature(features[i]);
                feature.geometry.transform(proj4326, current_projection);
                draftLayer.addFeatures([feature]);
            }
        }
    };

    /**
     * Private Functions
     */

    /**
     * ArcGIS REST
     *
     * @ToDo: Features not Images, so that we can have popups
     * - will require a new OpenLayers.Format.ArcREST
     *
     * @ToDo: Support Token Authentication
     * - Request Token during init of layer:
     * result = GET http[s]://hostname/ArcGIS/tokens?request=getToken&username=myusername&password=mypassword
     * - Append ?token=result to the URL
     */
    var addArcRESTLayer = function(map, layer) {

        var name = layer.name,
            url = [layer.url],
            layers,
            dir,
            isBaseLayer,
            format,
            transparent,
            visibility;

        if (undefined !== layer.layers) {
            layers = layer.layers.join();
        } else {
            // Default layer
            layers = 0;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.base) {
            isBaseLayer = layer.base;
        } else {
            isBaseLayer = false;
        }
        if (undefined !== layer.format) {
            format = layer.format;
        } else {
            format = 'png';
        }
        if (undefined !== layer.transparent) {
            transparent = layer.transparent;
        } else {
            transparent = true;
        }
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            // Default to visible
            visibility = true;
        }

        var arcRESTLayer = new OpenLayers.Layer.ArcGIS93Rest(
            name, url, {
                // There are other possible options, but this should be sufficient for our needs
                layers: 'show:' + layers,
                isBaseLayer: isBaseLayer,
                transparent: transparent,
                format: format,
                dir: dir,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'arcrest'
            }
        );

        arcRESTLayer.setVisibility(visibility);

        map.addLayer(arcRESTLayer);
        if (layer._base) {
            map.setBaseLayer(arcRESTLayer);
        }
    };

    // Bing
    var addBingLayers = function(map) {

        var bing = map.s3.options.Bing,
            ApiKey = bing.ApiKey,
            layer;

        if (bing.Aerial) {
            layer = new OpenLayers.Layer.Bing({
                key: ApiKey,
                type: 'Aerial',
                name: bing.Aerial.name,
                // This is used to Save State
                s3_layer_id: bing.Aerial.id,
                s3_layer_type: 'bing'
            });
            map.addLayer(layer);
            if (bing.Base == 'aerial') {
                map.setBaseLayer(layer);
            }
        }
        if (bing.Road) {
            layer = new OpenLayers.Layer.Bing({
                key: ApiKey,
                type: 'Road',
                name: bing.Road.name,
                // This is used to Save State
                s3_layer_id: bing.Road.id,
                s3_layer_type: 'bing'
            });
            map.addLayer(layer);
            if (bing.Base == 'road') {
                map.setBaseLayer(layer);
            }
        }
        if (bing.Hybrid) {
            layer = new OpenLayers.Layer.Bing({
                key: ApiKey,
                type: 'AerialWithLabels',
                name: bing.Hybrid.name,
                // This is used to Save State
                s3_layer_id: bing.Hybrid.id,
                s3_layer_type: 'bing'
            });
            map.addLayer(layer);
            if (bing.Base == 'hybrid') {
                map.setBaseLayer(layer);
            }
        }
    };

    // CoordinateGrid
    var addCoordinateGrid = function(map) {

        var CoordinateGrid = map.s3.options.CoordinateGrid;

        var graticule = new OpenLayers.Control.Graticule({
            //labelFormat: 'dm',
            layerName: CoordinateGrid.name,
            visible: CoordinateGrid.visibility
        });
        map.addControl(graticule);
    };

    // DraftLayer
    // Used for drawing Points/Polygons & for HTML5 GeoLocation
    var addDraftLayer = function(map) {

        // Styling
        var marker,
            style,
            options = map.s3.options;

        if (options.draw_feature) {
            // Marker for Points
            marker = options.marker_default;
        }
        if (options.draft_style) {
            // Custom Style for Draft Layer (e.g. LocationSelectorWidget2)
            style = options.draft_style;
        }
        var layer = {
            'marker': marker,
            'style': style,
            'opacity': 0.9 // Trigger the select renderIntent -> Opaque
            };

        var response = createStyleMap(map, layer),
            featureStyleMap = response[0],
            marker_url = response[1];

        var draftLayer = new OpenLayers.Layer.Vector(
            i18n.gis_draft_layer, {
                displayInLayerSwitcher: false,
                // This gets picked up after mapPanel instantiates & copied to it's layerRecords
                legendURL: marker_url,
                styleMap: featureStyleMap
            }
        );
        draftLayer.setVisibility(true);
        map.addLayer(draftLayer);
        // Pass to global scope
        map.s3.draftLayer = draftLayer;
        return draftLayer;
    };

    // GeoJSON
    // Used also by internal Feature Layers, Feature Queries, Feature Resources
    // & GeoRSS feeds
    var addGeoJSONLayer = function(map, layer) {

        var s3 = map.s3,
            name = layer.name;
        if (layer.no_popups) {
            s3.layers_nopopups.push(name);
        }

        var url = layer.url,
            readWithPOST,
            refresh,
            dir,
            visibility,
            cluster_attribute,
            cluster_distance,
            cluster_threshold,
            projection,
            layer_type;

        if (url.indexOf('$search') !== -1) {
            // Use POSTs to retrieve data allowing arbitrary l
            // ength of filter options as well as TLS encryption of filters
            readWithPOST = true;
        } else {
            readWithPOST = false;
        }
        if (undefined !== layer.refresh) {
            refresh = layer.refresh;
        } else {
            refresh = 900; // seconds (so 15 mins)
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, s3.dirs) == -1) {
                // Add this folder to the list of folders
                s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            // Default to visible
            visibility = true;
        }

        if (undefined !== layer.cluster_attribute) {
            cluster_attribute = layer.cluster_attribute;
        } else {
            // Default to global settings
            //var cluster_attribute = cluster_attribute_default;
            cluster_attribute = 'colour';
        }
        if (undefined !== layer.cluster_distance) {
            cluster_distance = layer.cluster_distance;
        } else {
            // Default to global settings
            cluster_distance = cluster_distance_default;
        }
        if (undefined !== layer.cluster_threshold) {
            cluster_threshold = layer.cluster_threshold;
        } else {
            // Default to global settings
            cluster_threshold = cluster_threshold_default;
        }

        if (undefined !== layer.projection) {
            projection = layer.projection;
        } else {
            // Feature Layers, GeoRSS & KML are always in 4326
            projection = 4326;
        }
        if (4326 == projection) {
            projection = proj4326;
        } else {
            projection = new OpenLayers.Projection('EPSG:' + projection);
        }
        if (undefined !== layer.type) {
            layer_type = layer.type;
        } else {
            // Feature Layers
            layer_type = 'feature';
        }
        var legendTitle = '<div class="gis_layer_legend"><div class="gis_legend_title">' + name + '</div>';
        if (undefined !== layer.desc) {
            legendTitle += '<div class="gis_legend_desc">' + layer.desc + '</div>';
        }
        if ((undefined !== layer.src) || (undefined !== layer.src_url)) {
            var source = '<div class="gis_legend_src">';
            if (undefined !== layer.src_url) {
                source += '<a href="' + layer.src_url + '" target="_blank">';
                if (undefined !== layer.src) {
                    source += layer.src;
                } else {
                    source += layer.src_url;
                }
                source += '</a>';
            } else {
                source += layer.src;
            }
            source += '</div>';
            legendTitle += source;
        }
        legendTitle += '</div>';

        // Styling
        var response = createStyleMap(map, layer),
            featureStyleMap = response[0],
            marker_url = response[1];

        // Strategies
        var strategies = [
            // Need to be uniquely instantiated
            new OpenLayers.Strategy.ZoomBBOX({
            //new OpenLayers.Strategy.BBOX({
                // load features for a wider area than the visible extent to reduce calls
                ratio: 1.5
                // don't fetch features after every resolution change
                //resFactor: 1
            })
        ];
        if (refresh) {
            strategies.push(new OpenLayers.Strategy.Refresh({
                force: true,
                interval: refresh * 1000 // milliseconds
                // Close any open Popups to prevent them getting orphaned
                // - annoying to have this happen automatically, so we handle it in onPopupClose() instead
                //refresh: function() {
                //    if (this.layer && this.layer.refresh) {
                //        while (this.layer.map.popups.length) {
                //            this.layer.map.removePopup(this.layer.map.popups[0]);
                //        }
                //    this.layer.refresh({force: this.force});
                //    }
                //}
            }));
        }
        if (cluster_threshold || layer.cluster) {
            // Common Cluster Strategy for all layers
            //s3.common_cluster_strategy
            strategies.push(new OpenLayers.Strategy.AttributeCluster({
                attribute: cluster_attribute,
                distance: cluster_distance,
                threshold: cluster_threshold
            }));
        }

        // Instantiate Layer
        var geojsonLayer = new OpenLayers.Layer.Vector(
            name, {
                dir: dir,
                projection: projection,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: url,
                    format: format_geojson,
                    readWithPOST: readWithPOST
                }),
                // This gets picked up after mapPanel instantiates & copied to it's layerRecords
                legendURL: marker_url,
                // Variable zIndexing within a layer?
                //rendererOptions: { zIndexing: true },
                strategies: strategies,
                styleMap: featureStyleMap,
                // Used to Save State & locate Layer to Activate/Refresh
                s3_layer_id: layer.id,
                s3_layer_type: layer_type,
                s3_style: layer.style,
                s3_url_format: layer.url_format
            }
        );
        // This gets picked up after mapPanel instantiates & copied to it's layerRecords
        geojsonLayer.legendTitle = legendTitle;
        // Set the popup_format, even if empty
        // - leave if not set (e.g. Feature Queries)
        if (undefined !== layer.popup_format) {
            geojsonLayer.s3_popup_format = layer.popup_format;
        }
        geojsonLayer.setVisibility(visibility);
        geojsonLayer.events.on({
            // We use featureclick.js on Map instead
            //'featureselected': onFeatureSelect,
            //'featureunselected': onFeatureUnselect,
            'loadstart': layer_loadstart,
            'loadend': layer_loadend,
            'visibilitychanged': layer_visibilitychanged
        });
        map.addLayer(geojsonLayer);
        // Ensure marker layers are rendered over other layers
        //map.setLayerIndex(geojsonLayer, 99);
    };

    // Google
    var addGoogleLayers = function(map) {

        var google = map.s3.options.Google,
            layer;

        if (google.MapMaker || google.MapMakerHybrid) {
            // v2 API
            if (google.Satellite) {
                layer = new OpenLayers.Layer.Google(
                    google.Satellite.name, {
                        type: G_SATELLITE_MAP,
                        sphericalMercator: true,
                        // This is used to Save State
                        s3_layer_id: google.Satellite.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'satellite') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.Maps) {
                layer = new OpenLayers.Layer.Google(
                    google.Maps.name, {
                        type: G_NORMAL_MAP,
                        sphericalMercator: true,
                        // This is used to Save State
                        s3_layer_id: google.Maps.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'maps') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.Hybrid) {
                layer = new OpenLayers.Layer.Google(
                    google.Hybrid.name, {
                        type: G_HYBRID_MAP,
                        sphericalMercator: true,
                        // This is used to Save State
                        s3_layer_id: google.Hybrid.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'maps') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.Terrain) {
                layer = new OpenLayers.Layer.Google(
                    google.Terrain.name, {
                        type: G_PHYSICAL_MAP,
                        sphericalMercator: true,
                        // This is used to Save State
                        s3_layer_id: google.Terrain.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'terrain') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.MapMaker) {
                layer = new OpenLayers.Layer.Google(
                    google.MapMaker.name, {
                        type: G_MAPMAKER_NORMAL_MAP,
                        sphericalMercator: true,
                        // This is used to Save State
                        s3_layer_id: layer.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'mapmaker') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.MapMakerHybrid) {
                layer = new OpenLayers.Layer.Google(
                    google.MapMakerHybrid.name, {
                        type: G_MAPMAKER_HYBRID_MAP,
                        sphericalMercator: true,
                        // This is used to Save State
                        s3_layer_id: layer.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'mapmakerhybrid') {
                    map.setBaseLayer(layer);
                }
            }
        } else {
            // v3 API
            if (google.Satellite) {
                layer = new OpenLayers.Layer.Google(
                    google.Satellite.name, {
                        type: 'satellite',
                        numZoomLevels: 22,
                        // This is used to Save State
                        s3_layer_id: google.Satellite.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'satellite') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.Maps) {
                layer = new OpenLayers.Layer.Google(
                    google.Maps.name, {
                        numZoomLevels: 20,
                        // This is used to Save State
                        s3_layer_id: google.Maps.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'maps') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.Hybrid) {
                layer = new OpenLayers.Layer.Google(
                    google.Hybrid.name, {
                        type: 'hybrid',
                        numZoomLevels: 20,
                        // This is used to Save State
                        s3_layer_id: google.Hybrid.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'hybrid') {
                    map.setBaseLayer(layer);
                }
            }
            if (google.Terrain) {
                layer = new OpenLayers.Layer.Google(
                    google.Terrain.name, {
                        type: 'terrain',
                        // This is used to Save State
                        s3_layer_id: google.Terrain.id,
                        s3_layer_type: 'google'
                    }
                );
                map.addLayer(layer);
                if (google.Base == 'terrain') {
                    map.setBaseLayer(layer);
                }
            }
        }
    };

    // GPX
    var addGPXLayer = function(map, layer) {

        var cluster_distance,
            cluster_threshold,
            dir,
            marker = layer.marker,
            name = layer.name,
            opacity,
            routes,
            tracks,
            url = layer.url,
            visibility,
            waypoints,
            marker_height = marker.h,
            marker_url = marker_url_path + marker.i,
            marker_width = marker.w;

        if (undefined !== layer.waypoints) {
            waypoints = layer.waypoints;
        } else {
            waypoints = true;
        }
        if (undefined !== layer.tracks) {
            tracks = layer.tracks;
        } else {
            tracks = true;
        }
        if (undefined !== layer.routes) {
            routes = layer.routes;
        } else {
            routes = true;
        }
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            visibility = true;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.opacity) {
            opacity = layer.opacity;
        } else {
            opacity = 1;
        }
        if (undefined !== layer.cluster_distance) {
            cluster_distance = layer.cluster_distance;
        } else {
            cluster_distance = cluster_distance_default;
        }
        if (undefined !== layer.cluster_threshold) {
            cluster_threshold = layer.cluster_threshold;
        } else {
            cluster_threshold = cluster_threshold_default;
        }

        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        if (waypoints) {
            style_marker.graphicOpacity = opacity;
            style_marker.graphicWidth = marker_width;
            style_marker.graphicHeight = marker_height;
            style_marker.graphicXOffset = -(marker_width / 2);
            style_marker.graphicYOffset = -marker_height;
            style_marker.externalGraphic = marker_url;
        } else {
            style_marker.externalGraphic = '';
        }
        style_marker.strokeColor = 'blue';
        style_marker.strokeWidth = 6;
        style_marker.strokeOpacity = opacity;

        var gpxLayer = new OpenLayers.Layer.Vector(
            name, {
                dir: dir,
                projection: proj4326,
                strategies: [
                    // Need to be uniquely instantiated
                    new OpenLayers.Strategy.Fixed(),
                    new OpenLayers.Strategy.Cluster({
                        distance: cluster_distance,
                        threshold: cluster_threshold
                    })
                ],
                // This gets picked up after mapPanel instantiates & copied to it's layerRecords
                legendURL: marker_url,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'gpx',
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: url,
                    format: new OpenLayers.Format.GPX({
                        extractAttributes: true,
                        extractWaypoints: waypoints,
                        extractTracks: tracks,
                        extractRoutes: routes
                    })
                })
            }
        );
        gpxLayer.setVisibility(visibility);
        gpxLayer.events.on({
            // We use featureclick.js on Map instead
            //'featureselected': onFeatureSelect,
            //'featureunselected': onFeatureUnselect,
            'loadstart': layer_loadstart,
            'loadend': layer_loadend,
            'visibilitychanged': layer_visibilitychanged
        });
        map.addLayer(gpxLayer);
    };

    // KML
    var addKMLLayer = function(map, layer) {

        var body,
            cluster_distance,
            cluster_threshold,
            dir,
            name = layer.name,
            refresh,
            s3 = map.s3,
            title,
            url = layer.url,
            visibility;

        if (undefined !== layer.title) {
            title = layer.title;
        } else {
            title = 'name';
        }
        if (undefined !== layer.body) {
            body = layer.body;
        } else {
            body = 'description';
        }
        if (undefined !== layer.refresh) {
            refresh = layer.refresh;
        } else {
            refresh = 900; // seconds (so 15 mins)
        }
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            // Default to visible
            visibility = true;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, s3.dirs) == -1) {
                // Add this folder to the list of folders
                s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.cluster_distance) {
            cluster_distance = layer.cluster_distance;
        } else {
            cluster_distance = cluster_distance_default;
        }
        if (undefined !== layer.cluster_threshold) {
            cluster_threshold = layer.cluster_threshold;
        } else {
            cluster_threshold = cluster_threshold_default;
        }

        // Styling: Base
        var response = createStyleMap(map, layer),
            featureStyleMap = response[0];
        //var marker_url = response[1];

        // Needs to be uniquely instantiated
        var format = new OpenLayers.Format.KML({
            extractStyles: true,
            extractAttributes: true,
            maxDepth: 2
        });

        // Strategies
        // Need to be uniquely instantiated
        var strategies = [
            new OpenLayers.Strategy.Fixed()
        ];
        if (refresh) {
            strategies.push(new OpenLayers.Strategy.Refresh({
                force: true,
                interval: refresh * 1000 // milliseconds
                // Close any open Popups to prevent them getting orphaned
                // - annoying to have this happen automatically, so we handle it in onPopupClose() instead
                //refresh: function() {
                //    if (this.layer && this.layer.refresh) {
                //        while (this.layer.map.popups.length) {
                //            this.layer.map.removePopup(this.layer.map.popups[0]);
                //        }
                //    this.layer.refresh({force: this.force});
                //    }
                //}
            }));
        }
        if (cluster_threshold) {
            // Common Cluster Strategy for all layers
            //map.s3.common_cluster_strategy
            //strategies.push(new OpenLayers.Strategy.AttributeCluster({
            strategies.push(new OpenLayers.Strategy.Cluster({
                //attribute: cluster_attribute,
                distance: cluster_distance,
                threshold: cluster_threshold
            }));
        }

        var kmlLayer = new OpenLayers.Layer.Vector(
            name, {
                dir: dir,
                projection: proj4326,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: url,
                    format: format
                }),
                strategies: strategies,
                // This gets picked up after mapPanel instantiates & copied to it's layerRecords
                // This is just fallback style, so use VectorLegend.js instead
                // @ToDo: Get that working with KML's dynamic styles
                //legendURL: marker_url,
                styleMap: featureStyleMap,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'kml',
                s3_style: layer.style
            }
        );
        kmlLayer.title = title;
        kmlLayer.body = body;

        kmlLayer.setVisibility(visibility);
        kmlLayer.events.on({
            // We use featureclick.js on Map instead
            //'featureselected': onFeatureSelect,
            //'featureunselected': onFeatureUnselect,
            'loadstart': layer_loadstart,
            'loadend': layer_loadend,
            'visibilitychanged': layer_visibilitychanged
        });
        map.addLayer(kmlLayer);
    };

    // OpenStreetMap
    var addOSMLayer = function(map, layer) {

        var dir,
            isBaseLayer,
            name = layer.name,
            numZoomLevels,
            url = [layer.url1],
            visibility;

        if (undefined !== layer.url2) {
            url.push(layer.url2);
        }
        if (undefined !== layer.url3) {
            url.push(layer.url3);
        }
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            // Default to visible
            visibility = true;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.base) {
            isBaseLayer = layer.base;
        } else {
            isBaseLayer = true;
        }
        if (undefined !== layer.zoomLevels) {
            numZoomLevels = layer.zoomLevels;
        } else {
            numZoomLevels = 19;
        }

        var osmLayer = new OpenLayers.Layer.TMS(
            name,
            url, {
                dir: dir,
                type: 'png',
                getURL: osm_getTileURL,
                displayOutsideMaxExtent: true,
                numZoomLevels: numZoomLevels,
                isBaseLayer: isBaseLayer,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'openstreetmap'
            }
        );
        if (undefined !== layer.attribution) {
            osmLayer.attribution = layer.attribution;
        }
        osmLayer.setVisibility(visibility);
        osmLayer.events.on({
            'loadstart': layer_loadstart,
            'loadend': layer_loadend
        });
        map.addLayer(osmLayer);
        if (layer._base) {
            map.setBaseLayer(osmLayer);
        }
    };

    // Supports OpenStreetMap TMS Layers
    var osm_getTileURL = function(bounds) {

        var res = this.map.getResolution(),
            x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w)),
            y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h)),
            z = this.map.getZoom(),
            limit = Math.pow(2, z);

        if (y < 0 || y >= limit) {
            return OpenLayers.Util.getImagesLocation() + '404.png';
        } else {
            x = ((x % limit) + limit) % limit;
            var path = z + '/' + x + '/' + y + '.' + this.type,
                url = this.url;

            if (url instanceof Array) {
                url = this.selectUrl(path, url);
            }
            return url + path;
        }
    };

    // OpenWeatherMap
    var addOWMLayers = function(map) {

        var apikey = S3.gis.openweathermap,
            layer,
            layers = map.s3.options.layers_openweathermap;

        for (var l in layers){
            layer = new OpenLayers.Layer.XYZ(
                layers[l].name,
                'https://tile.openweathermap.org/map/' + l + '/${z}/${x}/${y}.png?appid=' + apikey,
                {dir: layers[l].dir,
                 isBaseLayer: false,
                 // This is used to Save State
                 s3_layer_id: layers[l].id,
                 s3_layer_type: 'openweathermap',
                 type: 'png'
                 }
            );
            layer.setVisibility(layers[l].visibility);
            layer.events.on({
                'loadstart': layer_loadstart,
                'loadend': layer_loadend
            });
            map.addLayer(layer);
        }
    };

    // TMS
    var addTMSLayer = function(map, layer) {

        var dir,
            format,
            name = layer.name,
            numZoomLevels,
            url = [layer.url];

        if (undefined !== layer.url2) {
            url.push(layer.url2);
        }
        if (undefined !== layer.url3) {
            url.push(layer.url3);
        }
        var layername = layer.layername;
        if (undefined !== layer.zoomLevels) {
            numZoomLevels = layer.zoomLevels;
        } else {
            numZoomLevels = 19;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.format) {
            format = layer.format;
        } else {
            format = 'png';
        }

        var tmsLayer = new OpenLayers.Layer.TMS(
            name, url, {
                dir: dir,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'tms',
                layername: layername,
                type: format,
                numZoomLevels: numZoomLevels
            }
        );

        if (undefined !== layer.attribution) {
            tmsLayer.attribution = layer.attribution;
        }
        tmsLayer.events.on({
            'loadstart': layer_loadstart,
            'loadend': layer_loadend
        });
        map.addLayer(tmsLayer);
        if (layer._base) {
            map.setBaseLayer(tmsLayer);
        }
    };

    // WFS
    // @ToDo: WFS-T Editing: http://www.gistutor.com/openlayers/22-advanced-openlayers-tutorials/47-openlayers-wfs-t-using-a-geoserver-hosted-postgis-layer.html
    var addWFSLayer = function(map, layer) {

        var cluster_attribute,
            cluster_distance,
            cluster_threshold,
            dir,
            //editable = layer.editable,
            featureNS,
            featureType = layer.featureType,
            format,
            geometryName,
            name = layer.name,
            projection,
            refresh,
            schema,
            srsName,
            title = layer.title,
            url = layer.url,
            version,
            visibility;

        if ((undefined !== layer.username) && (undefined !== layer.password)) {
            var username = layer.username,
                password = layer.password;
            url = url.replace('://', '://' + username + ':' + password + '@');
        }
        if (undefined !== layer.featureNS) {
            featureNS = layer.featureNS;
        } else {
            featureNS = null;
        }
        if (undefined !== layer.schema) {
            schema = layer.schema;
        }
        if (undefined !== layer.version) {
            version = layer.version;
        } else {
            version = '1.1.0';
        }
        if (undefined !== layer.geometryName) {
            geometryName = layer.geometryName;
        } else {
            geometryName = 'the_geom';
        }
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            // Default to visible
            visibility = true;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.cluster_attribute) {
            cluster_attribute = layer.cluster_attribute;
        } else {
            // Default to global settings
            //cluster_attribute = cluster_attribute_default;
            cluster_attribute = 'colour';
        }
        if (undefined !== layer.cluster_distance) {
            cluster_distance = layer.cluster_distance;
        } else {
            cluster_distance = cluster_distance_default;
        }
        if (undefined !== layer.cluster_threshold) {
            cluster_threshold = layer.cluster_threshold;
        } else {
            cluster_threshold = cluster_threshold_default;
        }
        if (undefined !== layer.refresh) {
            refresh = layer.refresh;
        } else {
            // Default to Off as 'External Source' which is uneditable
            refresh = false;
        }
        // Strategies
        var strategies = [
            // Need to be uniquely instantiated
            new OpenLayers.Strategy.BBOX({
                // load features for a wider area than the visible extent to reduce calls
                ratio: 1.5
                // don't fetch features after every resolution change
                //resFactor: 1
            })
        ];
        if (refresh) {
            strategies.push(new OpenLayers.Strategy.Refresh({
                force: true,
                interval: refresh * 1000 // milliseconds
                // Close any open Popups to prevent them getting orphaned
                // - annoying to have this happen automatically, so we handle it in onPopupClose() instead
                //refresh: function() {
                //    if (this.layer && this.layer.refresh) {
                //        while (this.layer.map.popups.length) {
                //            this.layer.map.removePopup(this.layer.map.popups[0]);
                //        }
                //    this.layer.refresh({force: this.force});
                //    }
                //}
            }));
        }
        if (cluster_threshold) {
            // Common Cluster Strategy for all layers
            //map.s3.common_cluster_strategy
            strategies.push(new OpenLayers.Strategy.AttributeCluster({
                attribute: cluster_attribute,
                distance: cluster_distance,
                threshold: cluster_threshold
            }));
        }
        // @ToDo: if Editable
        //strategies.push(saveStrategy);

        if (undefined !== layer.projection) {
            projection = layer.projection;
        } else {
            projection = 4326;
        }
        if (version == '1.0.0') {
            srsName = 'EPSG:' + projection;
        } else {
            srsName = 'urn:ogc:def:crs:EPSG::' + projection;
            if (S3.gis.yx.includes(projection)) {
                // Reverse the Axis order
                format = new OpenLayers.Format.WFST({
                    version: version,
                    featureType: featureType,
                    featureNS: featureNS,
                    featurePrefix: 'feature',
                    geometryName: geometryName,
                    srsName: srsName,
                    schema: schema,
                    xy: false
                });
            }
        }
        var protocol = new OpenLayers.Protocol.WFS({
            url: url,
            version: version,
            featureType: featureType,
            featureNS: featureNS,
            format: format,
            geometryName: geometryName,
            srsName: srsName,
            // Needed for WFS-T
            schema: schema
        });

        var legendTitle = '<div class="gis_layer_legend"><div class="gis_legend_title">' + name + '</div>';
        if (undefined !== layer.desc) {
            legendTitle += '<div class="gis_legend_desc">' + layer.desc + '</div>';
        }
        if ((undefined !== layer.src) || (undefined !== layer.src_url)) {
            var source = '<div class="gis_legend_src">';
            if (undefined !== layer.src_url) {
                source += '<a href="' + layer.src_url + '" target="_blank">';
                if (undefined !== layer.src) {
                    source += layer.src;
                } else {
                    source += layer.src_url;
                }
                source += '</a>';
            } else {
                source += layer.src;
            }
            source += '</div>';
            legendTitle += source;
        }
        legendTitle += '</div>';

        // Styling
        var response = createStyleMap(map, layer),
            featureStyleMap = response[0],
            marker_url = response[1];

        if (4326 == projection) {
            projection = proj4326;
        } else {
            projection = new OpenLayers.Projection('EPSG:' + projection);
        }

        // Put these in Global Scope & i18n the messages
        //function showSuccessMsg(){
        //    showMsg('Transaction successfully completed');
        //}
        //function showFailureMsg(){
        //    showMsg('An error occured while operating the transaction');
        //}
        // if Editable
        // Set up a save strategy
        //var saveStrategy = new OpenLayers.Strategy.Save();
        //saveStrategy.events.register('success', '', showSuccessMsg);
        //saveStrategy.events.register('failure', '', showFailureMsg);

        var wfsLayer = new OpenLayers.Layer.Vector(
            name, {
            // limit the number of features to avoid browser freezes
            maxFeatures: 1000,
            strategies: strategies,
            dir: dir,
            // This gets picked up after mapPanel instantiates & copied to it's layerRecords
            legendURL: marker_url,
            projection: projection,
            //outputFormat: "json",
            //readFormat: new OpenLayers.Format.GeoJSON(),
            protocol: protocol,
            styleMap: featureStyleMap,
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'wfs',
            s3_style: layer.style
        });

        // This gets picked up after mapPanel instantiates & copied to it's layerRecords
        wfsLayer.legendTitle = legendTitle;
        wfsLayer.title = title;
        wfsLayer.setVisibility(visibility);
        wfsLayer.events.on({
            // We use featureclick.js on Map instead
            //'featureselected': onFeatureSelect,
            //'featureunselected': onFeatureUnselect,
            'loadstart': layer_loadstart,
            'loadend': layer_loadend,
            'visibilitychanged': layer_visibilitychanged
        });
        map.addLayer(wfsLayer);
    };

    // WMS
    var addWMSLayer = function(map, layer) {

        var bgcolor,
            buffer,
            dir,
            isBaseLayer,
            format,
            name = layer.name,
            opacity,
            queryable,
            legendURL,
            singleTile,
            style,
            tiled,
            transparent,
            url = layer.url,
            version,
            visibility,
            wms_map;

        if (layer.username && layer.password) {
            var username = layer.username,
                password = layer.password;
            url = url.replace('://', '://' + username + ':' + password + '@');
        }
        var layers = layer.layers;
        if (undefined !== layer.visibility) {
            visibility = layer.visibility;
        } else {
            visibility = true;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.base) {
            isBaseLayer = layer.base;
        } else {
            isBaseLayer = false;
        }
        if (undefined !== layer.transparent) {
            transparent = layer.transparent;
        } else {
            transparent = true;
        }
        if (undefined !== layer.format) {
            format = layer.format;
        } else {
            format = 'image/png';
        }
        if (undefined !== layer.version) {
            version = layer.version;
        } else {
            version = '1.1.1';
        }
        if (layer.map) {
            wms_map = layer.map;
        } else {
            wms_map = '';
        }
        // Server-side style NOT an internal JSON one
        if (layer.style) {
            style = layer.style;
        } else {
            style = '';
        }
        if (undefined !== layer.bgcolor) {
            bgcolor = '0x' + layer.bgcolor;
        } else {
            bgcolor = '';
        }
        if (undefined !== layer.buffer) {
            buffer = layer.buffer;
        } else {
            buffer = 0;
        }
        if (undefined !== layer.tiled) {
            tiled = layer.tiled;
        } else {
            tiled = false;
        }
        if (undefined !== layer.singleTile) {
            singleTile = layer.singleTile;
        } else {
            singleTile = false;
        }
        if (undefined !== layer.opacity) {
            opacity = layer.opacity;
        } else {
            opacity = 1;
        }
        if (undefined !== layer.queryable) {
            queryable = layer.queryable;
        } else {
            queryable = 1;
        }
        var legendTitle = '<div class="gis_layer_legend"><div class="gis_legend_title">' + name + '</div>';
        if (undefined !== layer.desc) {
            legendTitle += '<div class="gis_legend_desc">' + layer.desc + '</div>';
        }
        var source,
            label;
        if (map.s3.options.metadata) {
            // Use CMS to display Metadata
            var murl;
            if (undefined !== layer.post_id) {
                // Link to the existing page
                if (i18n.gis_metadata) {
                    // Read-only view for end-users
                    label = i18n.gis_metadata;
                    murl = S3.Ap.concat('/cms/page/' + layer.post_id);
                } else {
                    // Edit view for Map Admins
                    label = i18n.gis_metadata_edit;
                    murl = S3.Ap.concat('/cms/post/' + layer.post_id + '/update?layer_id=' + layer.id);
                }
            } else if (i18n.gis_metadata_create) {
                // Link to create new page
                label = i18n.gis_metadata_create;
                murl = S3.Ap.concat('/cms/post/create?layer_id=' + layer.id);
            }
            if (label) {
                source = '<div class="gis_legend_src"><a href="' + murl + '" target="_blank">' + label + '</a></div>';
                legendTitle += source;
            }
        } else if ((undefined !== layer.src) || (undefined !== layer.src_url)) {
            // Link to external source direct
            source = '<div class="gis_legend_src">';
            if (undefined !== layer.src_url) {
                source += '<a href="' + layer.src_url + '" target="_blank">';
                if (undefined !== layer.src) {
                    source += layer.src;
                } else {
                    source += layer.src_url;
                }
                source += '</a>';
            } else {
                source += layer.src;
            }
            source += '</div>';
            legendTitle += source;
        }
        legendTitle += '</div>';
        if (undefined !== layer.legendURL) {
            legendURL = layer.legendURL;
        }

        var wmsLayer = new OpenLayers.Layer.WMS(
            name, url, {
                layers: layers,
                transparent: transparent
            },
            {
                dir: dir,
                isBaseLayer: isBaseLayer,
                singleTile: singleTile,
                wrapDateLine: true,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'wms',
                // This gets picked up after mapPanel instantiates & copied to it's layerRecords
                queryable: queryable,
                visibility: visibility
            }
        );
        if (wms_map) {
            wmsLayer.params.MAP = wms_map;
        }
        if (format) {
            wmsLayer.params.FORMAT = format;
        }
        if (version) {
            wmsLayer.params.VERSION = version;
        }
        if (style) {
            wmsLayer.params.STYLES = style;
        }
        if (bgcolor) {
            wmsLayer.params.BGCOLOR = bgcolor;
        }
        if (tiled) {
            wmsLayer.params.TILESORIGIN = [map.maxExtent.left, map.maxExtent.bottom];
        }
        if (!isBaseLayer) {
            wmsLayer.opacity = opacity;
            if (buffer) {
                wmsLayer.buffer = buffer;
            } else {
                wmsLayer.buffer = 0;
            }
        }
        // This gets picked up after mapPanel instantiates & copied to it's layerRecords
        wmsLayer.legendTitle = legendTitle;
        if (legendURL) {
            // This gets picked up after mapPanel instantiates & copied to it's layerRecords
            wmsLayer.legendURL = legendURL;
        }
        wmsLayer.events.on({
            'loadstart': layer_loadstart,
            'loadend': layer_loadend,
            'visibilitychanged': layer_visibilitychanged
        });
        map.addLayer(wmsLayer);
        if (layer._base) {
            map.setBaseLayer(wmsLayer);
        }
    };

    // XYZ
    var addXYZLayer = function(map, layer) {

        var dir,
            format,
            name = layer.name,
            numZoomLevels,
            url = [layer.url];

        if (undefined !== layer.url2) {
            url.push(layer.url2);
        }
        if (undefined !== layer.url3) {
            url.push(layer.url3);
        }
        var layername = layer.layername;
        if (undefined !== layer.zoomLevels) {
            numZoomLevels = layer.zoomLevels;
        } else {
            numZoomLevels = 19;
        }
        if (undefined !== layer.dir) {
            dir = layer.dir;
            if ($.inArray(dir, map.s3.dirs) == -1) {
                // Add this folder to the list of folders
                map.s3.dirs.push(dir);
            }
        } else {
            // Default folder
            dir = '';
        }
        if (undefined !== layer.format) {
            format = layer.format;
        } else {
            format = 'png';
        }

        var xyzLayer = new OpenLayers.Layer.XYZ(
            name, url, {
                dir: dir,
                // This is used to Save State
                s3_layer_id: layer.id,
                s3_layer_type: 'xyz',
                layername: layername,
                type: format,
                numZoomLevels: numZoomLevels
            }
        );

        if (undefined !== layer.attribution) {
            xyzLayer.attribution = layer.attribution;
        }
        xyzLayer.events.on({
            'loadstart': layer_loadstart,
            'loadend': layer_loadend
        });
        map.addLayer(xyzLayer);
        if (layer._base) {
            map.setBaseLayer(xyzLayer);
        }
    };

    /**
     * Add Controls to the OpenLayers map
     * - private function called from addMap()
     * - to be called after the layers are added
     *
     * Parameters:
     * map - {OpenLayers.Map}
     *
     * Returns:
     * {null}
     */
    var addControls = function(map) {

        var options = map.s3.options;

        // The default controls (normally added in OpenLayers.Map, but brought here for greater control)
        // Navigation or TouchNavigation depending on what is in build
        //if (OpenLayers.Control.Navigation) {
            var navControl = new OpenLayers.Control.Navigation();
            if (options.no_zoom_wheel) {
                navControl.zoomWheelEnabled = false;
            }
            map.addControl(navControl);
        //} else if (OpenLayers.Control.TouchNavigation) {
        //    map.addControl(new OpenLayers.Control.TouchNavigation());
        //}
        if (options.zoomcontrol === undefined) {
            //if (OpenLayers.Control.Zoom) {
                map.addControl(new OpenLayers.Control.Zoom());
            //} else if (OpenLayers.Control.PanZoom) {
            //    map.addControl(new OpenLayers.Control.PanZoom());
            //}
        }
        //if (OpenLayers.Control.ArgParser) {
            map.addControl(new OpenLayers.Control.ArgParser());
        //}
        //if (OpenLayers.Control.Attribution) {
            map.addControl(new OpenLayers.Control.Attribution());
        //}

        // Additional Controls
        // (since the default is enabled, we provide no config in the enabled case)
        if (options.scaleline === undefined) {
            map.addControl(new OpenLayers.Control.ScaleLine());
        }
        if (options.mouse_position == 'mgrs') {
            map.addControl(new OpenLayers.Control.MGRSMousePosition());
        } else if (options.mouse_position) {
            map.addControl(new OpenLayers.Control.MousePosition());
        }
        if (options.permalink === undefined) {
            map.addControl(new OpenLayers.Control.Permalink());
        }
        if (options.overview === undefined) {
            // Copy all map options to the overview map, other than the controls
            var ov_options = {},
                map_options = map.options,
                prop;

            for (prop in map_options) {
                if (prop != 'controls') {
                    ov_options[prop] = map_options[prop];
                }
            }
            map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: ov_options}));
        }

        // Popup Controls
        addPopupControls(map);
    };

    /**
     * Popups
     */
    var addPopupControls = function(map) {

        map.events.register('featureover', this, tooltipSelect);
        map.events.register('featureout', this, tooltipUnselect);
        map.events.register('featureclick', this, onFeatureSelect);
    };

    /**
     * A Feature has been hovered over
     */
    var tooltipSelect = function(event) {

        var feature = event.feature,
            layer = feature.layer,
            j;

        // Style the feature as highlighted
        feature.renderIntent = 'select';
        layer.drawFeature(feature);
        if (['OpenLayers.Handler.PointS3',
             'OpenLayers.Handler.Path',
             'OpenLayers.Handler.Polygon',
             'OpenLayers.Handler.RegularPolygon'
             ].indexOf(layer.name) != -1) {
            // Don't do anything more when drawing features
            return;
        }
        var map = layer.map;
        if (map.s3.layers_nopopups.indexOf(layer.name) != -1) {
            // Don't do anything more here when there aren't popups to show
            return;
        }
        // Show a Tooltip (after a pause)
        S3.gis.timeouts[feature.id] = setTimeout(function() {
            if (feature.cluster) {
                // Cluster: no tooltip
            } else {
                // Single Feature: show tooltip
                if (!feature.geometry) {
                    // Bail
                    return;
                }
                var attributes = feature.attributes,
                    centerPoint = feature.geometry.getBounds().getCenterLonLat(),
                    tooltip;

                if (undefined !== layer.s3_popup_format) {
                    // GeoJSON Feature Layers
                    _.templateSettings = {interpolate: /\{(.+?)\}/g};
                    var s3_popup_format = layer.s3_popup_format,
                        template = _.template(s3_popup_format);

                    // Ensure we have all keys (we don't transmit empty attr)
                    var defaults = {},
                        key,
                        keys = s3_popup_format.split('{');

                    for (j = 0; j < keys.length; j++) {
                        key = keys[j].split('}')[0];
                        defaults[key] = '';
                    }
                    _.defaults(attributes, defaults);
                    tooltip = template(attributes);
                } else if (undefined !== attributes.popup) {
                    // Feature Queries or Theme Layers
                    tooltip = attributes.popup;
                } else if (undefined !== attributes.name) {
                    // GeoJSON, GeoRSS or Legacy Features
                    tooltip = attributes.name;
                } else if (undefined !== layer.title) {
                    // KML or WFS
                    var a = attributes[layer.title],
                        type = typeof a;

                    if ('object' == type) {
                        tooltip = a.value;
                    } else {
                        tooltip = a;
                    }
                }
                if (tooltip) {
                    OpenLayers.Popup.Tooltip = OpenLayers.Class(OpenLayers.Popup, {
                        displayClass: 'gis_tooltip',
                        contentDisplayClass: 'gis_tooltip_content',
                        CLASS_NAME: 'OpenLayers.Popup.Tooltip'
                    });
                    var tooltipPopup = new OpenLayers.Popup.Tooltip(
                        feature.id + '_tooltip',
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        tooltip
                    );
                    /* moved to CSS
                    tooltipPopup.contentDiv.style.backgroundColor = 'ffffcb';
                    tooltipPopup.contentDiv.style.overflow = 'hidden';
                    tooltipPopup.contentDiv.style.padding = '3px';
                    tooltipPopup.contentDiv.style.margin = '10px';
                    tooltipPopup.opacity = 0.7;*/
                    //tooltipPopup.closeOnMove = true;
                    tooltipPopup.autoSize = true;
                    feature.popup = tooltipPopup;
                    map.addPopup(tooltipPopup);
                }
            }
        }, 500);
    };

    /**
     * Similar to onFeatureUnselect
     */
    var tooltipUnselect = function(event) {

        var feature = event.feature,
            layer = feature.layer,
            map = layer.map;

        if (feature) {
            // Style the feature normally
            feature.renderIntent = 'default';
            layer.drawFeature(feature);
        }
        if (['OpenLayers.Handler.PointS3',
             'OpenLayers.Handler.Path',
             'OpenLayers.Handler.Polygon',
             'OpenLayers.Handler.RegularPolygon'
             ].indexOf(layer.name) != -1) {
            // Don't do anything more when drawing features
            return;
        }
        if (map.s3.layers_nopopups.indexOf(layer.name) != -1) {
            // Don't do anything more when there aren't popups to show
            return;
        }
        if (feature) {
            // Prevent any pending tooltip for this feature from loading
            clearTimeout(S3.gis.timeouts[feature.id]);
            if ((feature.popup) && (feature.popup.CLASS_NAME == 'OpenLayers.Popup.Tooltip')) {
                // Destroy any tooltip for this feature
                if (feature.popup) {
                    map.removePopup(feature.popup);
                    feature.popup.destroy();
                }
                delete feature.popup;
            //} else {
                // Must have been a cluster
            }
            $('#' + feature.id + '_tooltip').remove();
        }
    };

    /**
     * Add a Popup to map
     */
    var addPopup = function(feature, url, contents, iframe) {

        var id = feature.id + '_popup';
        if (iframe && url) {
            if (url.indexOf('http://') === 0 ) {
                // Use Proxy for remote popups
                url = OpenLayers.ProxyHost + encodeURIComponent(url);
            }
            contents = '<iframe src="' + url + '" onload="S3.gis.popupLoaded(\'' + id + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>';
        } else if (undefined === contents) {
            contents = i18n.gis_loading + '...<div class="throbber"></div>';
        }
        var centerPoint = feature.geometry.getBounds().getCenterLonLat();

        var popup = new OpenLayers.Popup.FramedCloud(
            id,
            centerPoint,
            new OpenLayers.Size(400, 400),
            contents,
            null,        // anchor
            true,        // closeBox
            onPopupClose // closeBoxCallback
        );
        //popup.disableFirefoxOverflowHack = true; // Still needed
        //popup.keepInMap = false; // Not working
        feature.popup = popup; // Link to be able to delete popup onClose
        popup.feature = feature; // Link to be able to delete popup onClose
        // @ToDo: deployment_setting (default OL is 1200 x 660)
        popup.maxSize = new OpenLayers.Size(750, 660);
        var map = feature.layer.map;
        feature.map = map; // Link to be able to delete all popups as a failsafe
        map.addPopup(popup);
        if (!iframe && undefined !== url) {
            // use AJAX to get the contentHTML
            loadDetails(url, id + '_contentDiv', popup);
        }
        return popup;
    };
    // Pass to global scope to access from external scripts (e.g. s3.gis.pois.js)
    S3.gis.addPopup = addPopup;

    // In Global scope as called from HTML (iframe onLoad)
    S3.gis.popupLoaded = function(id) {

        // Display the hidden contents
        $('#' + id + '_contentDiv iframe').contents().find('#popup').show();

        // Iterate through all Maps (usually just 1)
        var maps = S3.gis.maps,
            map_id,
            map,
            popup,
            popups,
            i,
            len;

        for (map_id in maps) {
            map = maps[map_id];
            // Iterate through all Popups (usually just 1)
            popups = map.popups;
            for (i=0, len=popups.length; i < len; i++) {
                popup = popups[i];
                if (popup.id == id) {
                    // Update the Popup size
                    popup.updateSize(true);
                }
            }
        }
    };

    /**
     * Used by addPopup and onFeatureSelect
     */
    var loadDetails = function(url, id, popup) {

        // Load the Popup Details via AJAX
        if (url.indexOf('http://') === 0) {
            // Use Proxy for remote popups
            url = OpenLayers.ProxyHost + encodeURIComponent(url);
        }
        // @ToDo: Support option to load just a section of the page
        // e.g. USGS would just load '#main'
        /*
        url_parts = url.split('?', 1);
        url = url_parts[0];
        url = url + ' #main';
        $('#' + id).load(url, url_parts[1], function() {
            popup.updateSize();
        });*/
        $.ajaxS3({
            url: url,
            dataType: 'html',
            // gets moved to 'done' inside AjaxS3
            success: function(data) {

                try {
                    // Load response into div
                    $('#' + id).html(data);
                    popup.updateSize();
                    // Resize when images are loaded
                    //popup.registerImageListeners();
                    // Check for links to load in iframe
                    $('#' + id + ' a.btn.iframe').click(function() {

                        var url = $(this).attr('href');
                        if (url.indexOf('http://') === 0) {
                            // Use Proxy for remote popups
                            url = OpenLayers.ProxyHost + encodeURIComponent(url);
                        }
                        // Strip the '_contentDiv'
                        var popup_id = id.slice(0, -11),
                            contents = '<iframe src="' + url + '" onload="S3.gis.popupLoaded(\'' + popup_id + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>';
                        $('#' + id).html(contents);

                        // Prevent default
                        return false;
                    });
                } catch(e) {
                    // Page is probably trying to load 'local' resources from us
                    // @ToDo: Load in iframe instead...
                }
            },
            // gets moved to 'fail' inside AjaxS3
            error: function(jqXHR, textStatus, errorThrown) {

                var msg;
                if (errorThrown == 'UNAUTHORIZED') {
                    msg = i18n.gis_requires_login;
                } else {
                    msg = jqXHR.responseText;
                }
                $('#' + id + '_contentDiv').html(msg);
                popup.updateSize();
            }
        });
    };

    /**
     * A Feature has been clicked
     */
    var onFeatureSelect = function(event) {

        var feature = event.feature,
            layer = feature.layer,
            map = layer.map,
            s3 = map.s3,
            popup,
            data_link,
            data_id;

        if ((['OpenLayers.Handler.PointS3',
              'OpenLayers.Handler.Path',
              'OpenLayers.Handler.Polygon',
              'OpenLayers.Handler.RegularPolygon'
              ].indexOf(layer.name) != -1) || (s3.layers_nopopups.indexOf(layer.name) != -1)) {
            // Don't do anything here when drawing Features or there aren't popups to show
            return;
        } else if (layer.s3_layer_type == 'openweathermap') {
            // Use std onSelect instead of the custom one
            //layer.options.onSelect(event);
            var html = layer.options.getPopupHtml(feature.attributes.station);
            popup = new OpenLayers.Popup('Popup',
                                         feature.geometry.getBounds().getCenterLonLat(),
                                         new OpenLayers.Size(layer.options.popupX, layer.options.popupY),
                                         html,
                                         'Station',
                                         false);
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup, true);
            return;
        }
        /*
        if (feature.popup) {
            // Close instead
            onFeatureUnselect(event);
            return;
        }*/
        var geometry = feature.geometry,
            i,
            len;
        if (geometry.CLASS_NAME != 'OpenLayers.Geometry.Point') {
            // If there is a Point feature also-firing then we shouldn't
            for (i=0, len=s3.clicking.length; i<len; ++i) {
                if (s3.clicking[i].geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                    return;
                }
            }
        }
        // Close the tooltip
        tooltipUnselect(event);
        // Style the feature as highlighted
        feature.renderIntent = 'select';
        layer.drawFeature(feature);
        var centerPoint = geometry.getBounds().getCenterLonLat();
        //var popup_id = S3.uid();
        var popup_id = feature.id + '_popup',
            titleField;
        if (undefined !== layer.title) {
            // KML, WFS
            titleField = layer.title;
        } else {
            titleField = 'name';
        }
        var contents,
            name,
            popup_url,
            attributes,
            row,
            value,
            title,
            template,
            j;

        if (feature.cluster) {
            // Cluster
            var cluster = feature.cluster;
            contents = i18n.gis_cluster_multiple + ':<ul>';
            // Only display 1st 9 records
            //var length = Math.min(cluster.length, 9);
            var length = cluster.length,
                map_id = s3.id;
            for (i = 0; i < length; i++) {
                attributes = cluster[i].attributes;
                if (undefined !== layer.s3_popup_format) {
                    // GeoJSON Feature Layers
                    _.templateSettings = {interpolate: /\{(.+?)\}/g};
                    var s3_popup_format = layer.s3_popup_format;
                    template = _.template(s3_popup_format);
                    // Ensure we have all keys (we don't transmit empty attr)
                    var defaults = {},
                        key,
                        keys = s3_popup_format.split('{');
                    for (j = 0; j < keys.length; j++) {
                        key = keys[j].split('}')[0];
                        defaults[key] = '';
                    }
                    _.defaults(attributes, defaults);
                    // Only display the 1st line of the hover popup
                    name = template(attributes).split('<br/>', 1)[0];
                } else if (undefined !== attributes.popup) {
                    // Only display the 1st line of the hover popup
                    name = attributes.popup.split('<br/>', 1)[0];
                } else {
                    name = attributes[titleField];
                }
                if (undefined !== attributes.url) {
                    contents += "<li><a href='javascript:S3.gis.loadClusterPopup(" + "\"" + map_id + "\", \"" + attributes.url + "\", \"" + popup_id + "\"" + ")'>" + name + "</a></li>";
                } else if (undefined !== layer.s3_url_format) {
                    // Feature Layer or Feature Resource
                    // Popup contents are pulled via AJAX
                    _.templateSettings = {interpolate: /\{(.+?)\}/g};
                    //var s3_url_format = layer.s3_url_format;
                    template = _.template(layer.s3_url_format);
                    // Ensure we have all keys (we don't transmit empty attr)
                    /* Only needed once we start getting non-id formats
                    var defaults = {},
                        key,
                        keys = s3_popup_format.split('{');
                    for (var j = 0; j < keys.length; j++) {
                        key = keys[j].split('}')[0];
                        defaults[key] = '';
                    }
                    _.defaults(attributes, defaults);*/
                    // Since this is single feature case, feature should have single id
                    if (attributes.id.constructor === Array) {
                        attributes.id = attributes.id[0];
                    }
                    popup_url = template(attributes);
                    contents += "<li><a href='javascript:S3.gis.loadClusterPopup(" + "\"" + map_id + "\", \"" + popup_url + "\", \"" + popup_id + "\"" + ")'>" + name + "</a></li>";
                } else {
                    // @ToDo: Provide a way to load non-URL based popups
                    contents += '<li>' + name + '</li>';
                }
            }
            popup_url = null;
            contents += '</ul>';
            contents += "<div align='center'><a href='javascript:S3.gis.zoomToSelectedFeature(" + "\"" + map_id + "\", " + centerPoint.lon + "," + centerPoint.lat + ", 3)'>" + i18n.gis_zoomin + '</a></div>';
        } else {
            // Single Feature
            var layerType = layer.s3_layer_type;
            if (layerType == 'kml') {
                attributes = feature.attributes;
                if (undefined !== feature.style.balloonStyle) {
                    // Use the provided BalloonStyle
                    var balloonStyle = feature.style.balloonStyle;
                    // "<strong>{name}</strong><br /><br />{description}"
                    contents = balloonStyle.replace(/{([^{}]*)}/g,
                        function (a, b) {
                            var r = attributes[b];
                            return typeof r === 'string' || typeof r === 'number' ? r : a;
                        }
                    );
                } else {
                    // Build the Popup contents manually
                    var type = typeof attributes[titleField];
                    if ('object' == type) {
                        title = attributes[titleField].value;
                    } else {
                        title = attributes[titleField];
                    }
                    contents = '<h3>' + title + '</h3>';
                    var body = layer.body.split(' ');
                    for (j = 0; j < body.length; j++) {
                        type = typeof attributes[body[j]];
                        if ('object' == type) {
                            // Geocommons style
                            var label = attributes[body[j]].displayName;
                            if (label === '') {
                                label = body[j];
                            }
                            value = attributes[body[j]].value;
                            row = '<div class="gis_popup_row"><div class="gis_popup_label">' + label +
                                  ':</div><div class="gis_popup_cell">' + value + '</div></div>';
                        } else if (undefined !== attributes[body[j]]) {
                            row = '<div class="gis_popup_row">' + attributes[body[j]] + '</div>';
                        } else {
                            // How would we get here?
                            row = '';
                        }
                        contents += row;
                    }
                }
                // Protect the content against JavaScript attacks
                if (contents.search('<script') != -1) {
                    contents = 'Content contained Javascript! Escaped content below.<br />' + contents.replace(/</g, '<');
                }
            } else if (layerType == 'gpx') {
                // @ToDo: display as many attributes as we can: Description (Points), Date, Author?, Lat, Lon
            } else if ((layerType == 'shapefile') || (layerType == 'geojson')) {
                // We don't have control of attributes, so simply display all
                // @ToDo: have an optional style.popup (like KML's balloonStyle)
                attributes = feature.attributes;
                contents = '<div>';
                $.each(attributes, function(label, value) {
                    if (label == 'id_orig') {
                        label = 'id';
                    }
                    row = '<div class="gis_popup_row"><div class="gis_popup_label">' + label +
                          ':</div><div class="gis_popup_cell">' + value + '</div></div>';
                    contents += row;
                });
                contents += '</div>';
            } else if (layerType == 'wfs') {
                attributes = feature.attributes;
                title = attributes[titleField];
                contents = '<h3>' + title + '</h3>';
                $.each(attributes, function(label, value) {
                    row = '<div class="gis_popup_row"><div class="gis_popup_label">' + label +
                          ':</div><div class="gis_popup_val">' + value + '</div></div>';
                    contents += row;
                });
            } else {
                // @ToDo: disambiguate these by type
                if (undefined !== feature.attributes.url) {
                    // Feature Query with Popup contents pulled via AJAX
                    popup_url = feature.attributes.url;
                    // Defaulted within addPopup()
                    //contents = i18n.gis_loading + "...<div class='throbber'></div>";
                } else if (undefined !== layer.s3_url_format) {
                    // Feature Layer or Feature Resource
                    // Popup contents are pulled via AJAX
                    _.templateSettings = {interpolate: /\{(.+?)\}/g};
                    //var attributes = feature.attributes;
                    //var s3_url_format = layer.s3_url_format;
                    template = _.template(layer.s3_url_format);
                    // Ensure we have all keys (we don't transmit empty attr)
                    /* Only needed once we start getting non-id formats
                    var defaults = {},
                        key,
                        keys = s3_popup_format.split('{');
                    for (var j = 0; j < keys.length; j++) {
                        key = keys[j].split('}')[0];
                        defaults[key] = '';
                    }
                    _.defaults(attributes, defaults);*/
                    // Since this is single feature case, feature should have single id
                    if (feature.attributes.id.constructor === Array) {
                        feature.attributes.id = feature.attributes.id[0];
                    }
                    popup_url = template(feature.attributes);
                } else {
                    // Popup contents are built from the attributes
                    attributes = feature.attributes;
                    if (undefined === attributes.name) {
                        name = '';
                    } else {
                        name = '<h3>' + attributes.name + '</h3>';
                    }
                    var description;
                    if (undefined === attributes.description) {
                        description = '';
                    } else {
                        description = '<p>' + attributes.description + '</p>';
                    }
                    var link;
                    if (undefined === attributes.link) {
                        link = '';
                    } else {
                        link = '<a href="' + attributes.link + '" target="_blank">' + attributes.link + '</a>';
                    }
                    var data;
                    if (undefined === attributes.data) {
                        data = '';
                    } else if (attributes.data.indexOf('http://') === 0) {
                        data_link = true;
                        data_id = S3.uid();
                        data = '<div id="' + data_id + '">' + i18n.gis_loading + "...<div class='throbber'></div>" + '</div>';
                    } else {
                        data = '<p>' + attributes.data + '</p>';
                    }
                    var image;
                    if (undefined === attributes.image) {
                        image = '';
                    } else if (attributes.image.indexOf('http://') === 0) {
                        image = '<img src="' + attributes.image + '" height=300 width=300>';
                    } else {
                        image = '';
                    }
                    contents = name + description + link + data + image;
                }
            }
        }
        popup = addPopup(feature, popup_url, contents);
        if (data_link) {
            // call AJAX to get the linked data
            loadDetails(feature.attributes.data, data_id, popup);
        }
    };

    /**
     * Similar to tooltipUnselect
     */
    var onFeatureUnselect = function(event) {

        var feature = event.feature;

        if (feature) {
            var layer = feature.layer;
            /*
            if (layer.s3_layer_type == 'openweathermap') {
                // Use std onUnselect instead of the custom one
                layer.options.onUnselect(event);
                return;
            }*/
            // Style the feature normally
            feature.renderIntent = 'default';
            if (layer) {
                layer.drawFeature(feature);
            }
            // Destroy any popup for this feature
            if (feature.popup) {
                if (layer) {
                    layer.map.removePopup(feature.popup);
                }
                feature.popup.destroy();
                delete feature.popup;
            }
            if (feature.id) {
                $('#' + feature.id + '_popup').remove();
            } else {
                // Somehow the feature has lost it's references - better to delete all popups than leave it hanging
                var map = feature.map;
                if (map) {
                    var popups = map.popups;
                    var len = popups.length;
                    for (var i = len - 1; i > -1; i--) {
                        map.removePopup(popups[i]);
                    }
                }
            }
            if (layer && layer.name == i18n.gis_draft_layer) {
                // Also destroy the feature
                feature.destroy();
            }
        }
    };

    /**
     * Unselect the associated feature when popup closes
     */
    var onPopupClose = function(/* event */) {

        onFeatureUnselect(this);
    };

    /**
     * Replace Cluster Popup contents with selected Feature Popup
     */
    var loadClusterPopup = function(map_id, url, id) {

        // Show Throbber whilst waiting for Popup to show
        var selector = '#' + id + '_contentDiv',
            div = $(selector),
            contents = i18n.gis_loading + "...<div class='throbber'></div>";

        div.html(contents);

        // Load data into Popup
        var map = S3.gis.maps[map_id];
        $.getS3(
            url,
            function(data) {
                div.html(data);
                // @ToDo: Don't assume we're the only popup on this map
                map.popups[0].updateSize();
                var dropdowns = $(selector + ' .dropdown-toggle');
                if (dropdowns.length) {
                    // We have Bootstrap dropdowns
                    // Modify Overflow of containers
                    div.parent()
                       .css('overflow', 'visible')
                       .parent()
                       .css('overflow', 'visible');
                    // Enable the Bootstrap dropdowns in the popups
                    dropdowns.dropdown();
                }
            },
            'html'
        );
    };
    // Pass to global scope to access from HTML
    S3.gis.loadClusterPopup = loadClusterPopup;

    /**
     * Zoom to Selected Feature from within Cluster Popup
     */
    var zoomToSelectedFeature = function(map_id, lon, lat, zoomfactor) {

        var map = S3.gis.maps[map_id],
            lonlat = new OpenLayers.LonLat(lon, lat);

        // Get Current Zoom
        var currZoom = map.getZoom();

        // New Zoom
        var newZoom = currZoom + zoomfactor;

        // Center and Zoom
        map.setCenter(lonlat, newZoom);

        // Remove Popups
        for (var i = 0; i < map.popups.length; i++) {
            map.removePopup(map.popups[i]);
        }
    };
    // Pass to global scope to access from HTML
    S3.gis.zoomToSelectedFeature = zoomToSelectedFeature;

    /**
     * Toolbar Buttons
     */
    var addToolbar = function(map) {

        var s3 = map.s3,
            options = s3.options;

        //var toolbar = map.s3.mapPanelContainer.getTopToolbar();
        var toolbar = new Ext.Toolbar({
            //cls: 'gis_toolbar',
            // Height needed for the Throbber
            height: 34
        });
        toolbar.map = map;
        // Allow WMSGetFeatureInfo to find the toolbar
        s3.portal.toolbar = toolbar;

        OpenLayers.Control.ZoomToMaxExtentS3 = OpenLayers.Class(OpenLayers.Control.Button, {
            /**
             * Method: trigger
             *
             * Called whenever this control is being rendered inside of a panel and a
             *     click occurs on this controls element. Actually zooms to the maximum
             *     extent of this controls map.
             */
            trigger: function() {
                var restrictedExtent = new OpenLayers.Bounds.fromArray(options.restrictedExtent);
                restrictedExtent.transform(proj4326, map.getProjectionObject());
                map.zoomToExtent(restrictedExtent);
            },

            CLASS_NAME: "OpenLayers.Control.ZoomToMaxExtentS3"
        });

        var zoomfull = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomToMaxExtentS3(),
            map: map,
            iconCls: 'zoomfull',
            // button options
            tooltip: i18n.gis_zoomfull
        });

        var line_pressed = false,
            pan_pressed = false,
            point_pressed = false,
            polygon_pressed = false,
            circle_pressed = false;

        if (options.draw_polygon == 'active') {
            polygon_pressed = true;
        } else if (options.draw_line == 'active') {
            line_pressed = true;
        } else if (options.draw_feature == 'active') {
            point_pressed = true;
        } else if (options.draw_circle == 'active') {
            circle_pressed = true;
        }else {
            pan_pressed = true;
        }

        // Controls for Draft Features (unused)

        // var draftLayer = map.s3.draftLayer;
        //var selectControl = new OpenLayers.Control.SelectFeature(draftLayer, {
        //    onSelect: onFeatureSelect,
        //    onUnselect: onFeatureUnselect,
        //    multiple: false,
        //    clickout: true,
        //    isDefault: true
        //});

        //var removeControl = new OpenLayers.Control.RemoveFeature(draftLayer, {
        //    onDone: function(feature) {
        //        console.log(feature);
        //    }
        //});

        //var selectButton = new GeoExt.Action({
            //control: selectControl,
        //    map: map,
        //    iconCls: 'searchclick',
            // button options
        //    tooltip: 'T("Query Feature")',
        //    toggleGroup: 'controls',
        //    enableToggle: true
        //});

        //var lineButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Path),
        //    map: map,
        //    iconCls: 'drawline-off',
        //    tooltip: 'T("Add Line")',
        //    toggleGroup: 'controls'
        //});

        //var dragButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DragFeature(draftLayer),
        //    map: map,
        //    iconCls: 'movefeature',
        //    tooltip: 'T("Move Feature: Drag feature to desired location")',
        //    toggleGroup: 'controls'
        //});

        //var resizeButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer, { mode: OpenLayers.Control.ModifyFeature.RESIZE }),
        //    map: map,
        //    iconCls: 'resizefeature',
        //    tooltip: 'T("Resize Feature: Select the feature you wish to resize & then Drag the associated dot to your desired size")',
        //    toggleGroup: 'controls'
        //});

        //var rotateButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer, { mode: OpenLayers.Control.ModifyFeature.ROTATE }),
        //    map: map,
        //    iconCls: 'rotatefeature',
        //    tooltip: 'T("Rotate Feature: Select the feature you wish to rotate & then Drag the associated dot to rotate to your desired location")',
        //    toggleGroup: 'controls'
        //});

        //var modifyButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer),
        //    map: map,
        //    iconCls: 'modifyfeature',
        //    tooltip: 'T("Modify Feature: Select the feature you wish to deform & then Drag one of the dots to deform the feature in your chosen manner")',
        //    toggleGroup: 'controls'
        //});

        //var removeButton = new GeoExt.Action({
        //    control: removeControl,
        //    map: map,
        //    iconCls: 'removefeature',
        //    tooltip: 'T("Remove Feature: Select the feature you wish to remove & press the delete key")',
        //    toggleGroup: 'controls'
        //});

        /* Add controls to Map & buttons to Toolbar */

        toolbar.add(zoomfull);

        if (i18n.gis_geoLocate && navigator.geolocation) {
            // HTML5 geolocation is available :)
            addGeolocateControl(toolbar);
        }

        // Nav Controls
        if (undefined === options.nav) {
            var zoomout = new GeoExt.Action({
                control: new OpenLayers.Control.ZoomBox({ out: true }),
                map: map,
                iconCls: 'zoomout',
                // button options
                tooltip: i18n.gis_zoomout,
                toggleGroup: 'controls'
            });

            var zoomin = new GeoExt.Action({
                control: new OpenLayers.Control.ZoomBox(),
                map: map,
                iconCls: 'zoomin',
                // button options
                tooltip: i18n.gis_zoominbutton,
                toggleGroup: 'controls'
            });

            var panButton = new GeoExt.Action({
                control: new OpenLayers.Control.Navigation(),
                map: map,
                iconCls: 'pan-off',
                // button options
                tooltip: i18n.gis_pan,
                allowDepress: true,
                toggleGroup: 'controls',
                pressed: pan_pressed
            });

            toolbar.add(zoomout);
            toolbar.add(zoomin);
            toolbar.add(panButton);
            toolbar.addSeparator();

            addNavigationControl(toolbar);
        }

        // Print
        if (options.print) {
            toolbar.addSeparator();
            addPrintButton(toolbar);
        }

        // Save Viewport
        if (options.save && options.save != 'float') {
            toolbar.addSeparator();
            addSaveButton(toolbar);
        }
        toolbar.addSeparator();

        // Measure Tools
        // @ToDo: Make these optional
        addMeasureControls(toolbar);

        if (options.clear_layers == 'toolbar') {
            addClearLayersButton(map, toolbar);
        }

        // MGRS Grid PDFs
        if (options.mgrs_url) {
            addPdfControl(toolbar);
        }

        if (options.draw_feature || options.draw_line || options.draw_polygon || options.draw_circle) {
            // Draw Controls
            toolbar.addSeparator();
            //toolbar.add(selectButton);
            /* @ToDo: Get Menus/Popups working
            if (S3.gis.poi_resources) {
                //var is_popup_enabled;
                var menu_items = [];
                var resource_array = S3.gis.poi_resources;
                for (var i=0; i < resource_array.length ; i++) {
                    addCustomPointControl(map, toolbar, point_pressed, resource_array[i], menu_items);
                    if (resource_array[i]['location'] == 'popup') {
                        is_popup_enabled = true;
                    }
                }
                if (menu_items.length > 0) {
                    toolbar.add({
                        text: i18n.gis_add_resources, // @ToDo: Add this to s3gis.py
                        menu: new Ext.menu.Menu({ items: menu_items })
                    });
                }
                 Popup for selecting resources
                if (is_popup_enabled) {
                    addResourcePopupButton(map, toolbar, point_pressed, resource_array);
                }
            } else if (options.draw_feature) {
            */
            var poi_resources = S3.gis.poi_resources,
                len;
            if (poi_resources) {
                len = poi_resources.length;
            }
            var i,
                resource;
            if (options.draw_feature) {
                if (poi_resources) {
                    // Add a button per point resource
                    for (i = 0; i < len; i++) {
                        resource = poi_resources[i];
                        if (resource.t == 'point') {
                            addPointControl(map, toolbar, point_pressed, resource);
                        }
                    }
                } else {
                    // Add a generic button
                    addPointControl(map, toolbar, point_pressed);
                }
            }
            if (options.draw_line) {
                if (poi_resources) {
                    // Add a button per line resource
                    for (i = 0; i < len; i++) {
                        resource = poi_resources[i];
                        if (resource.t == 'line') {
                            addLineControl(map, toolbar, line_pressed, resource);
                        }
                    }
                } else {
                    // Add a generic button
                    addLineControl(map, toolbar, line_pressed);
                }
            }
            if (options.draw_polygon) {
                if (poi_resources) {
                    // Add a button per line resource
                    for (i = 0; i < len; i++) {
                        resource = poi_resources[i];
                        if (resource.t == 'line') {
                            addPolygonControl(map, toolbar, polygon_pressed, true, resource);
                        }
                    }
                } else {
                    // Add a generic button
                    addPolygonControl(map, toolbar, polygon_pressed, true);
                }
            }
            if (options.draw_circle) {
                if (poi_resources) {
                    // Add a button per circle resource
                    for (i = 0; i < len; i++) {
                        resource = poi_resources[i];
                        if (resource.t == 'circle') {
                            addCircleControl(map, toolbar, circle_pressed, resource);
                        }
                    }
                } else {
                    // Add a generic button
                    addCircleControl(map, toolbar, circle_pressed);
                }
            }
            if (options.color_picker) {
                addColorPickerControl(map, toolbar);
            }
            //toolbar.add(dragButton);
            //toolbar.add(resizeButton);
            //toolbar.add(rotateButton);
            //toolbar.add(modifyButton);
            //toolbar.add(removeButton);
        }

        // WMS GetFeatureInfo
        // @ToDo: Add control if we add appropriate layers dynamically...
        if (i18n.gis_get_feature_info) {
            addWMSGetFeatureInfoControl(map);
        }

        // OpenStreetMap Editor
        if (i18n.gis_potlatch) {
            addPotlatchButton(toolbar);
        }

        // Google Streetview
        if (options.Google && options.Google.StreetviewButton) {
            addGoogleStreetviewControl(toolbar);
        }

        /* Google Earth
        // NB Google Earth Panel limited to 1/page due to callback needing global scope (unless we can pass a map_id in somehow)
        try {
            // Only load Google layers if GoogleAPI downloaded ok
            // - allow rest of map to work offline
            if (options.Google.Earth && google) {
                addGoogleEarthControl(toolbar);
            }
        } catch(e) {} */

        // Search box
        if (options.geonames) {
            var max_width;
            if (false === options.nav) {
                // LocationSelector has fewer toolbar buttons, so can handle a greater width
                // & this functionality is very useful here
                max_width = options.map_width - 500;
            } else {
                // Leave space for the Layer Throbber
                max_width = options.map_width - 680;
            }
            var width = Math.min(350, max_width);
            var mapSearch = new GeoExt.ux.GeoNamesSearchCombo({
                map: map,
                width: width,
                listWidth: width,
                minChars: 2,
                // @ToDo: Restrict to the Country if using a Country config
                //countryString: ,
                emptyText: i18n.gis_search,
                username: options.geonames
            });
            toolbar.addSeparator();
            toolbar.add(mapSearch);
        }

        // Throbber
        var throbber = new Ext.BoxComponent({
            cls: 'layer_throbber hide'
        });
        toolbar.add(throbber);

        return toolbar;
    };

    /* Toolbar Buttons */

    /**
     * Geolocate control
     * - HTML5 GeoLocation: http://dev.w3.org/geo/api/spec-source.html
     */
    var addGeolocateControl = function(toolbar) {

        var map = toolbar.map;

        // Use the Draft Features layer
        var draftLayer = map.s3.draftLayer;

        var style = {
            fillColor: '#000',
            fillOpacity: 0.1,
            strokeWidth: 0
        };

        var geolocateControl = new OpenLayers.Control.Geolocate({
            geolocationOptions: {
                enableHighAccuracy: false,
                maximumAge: 0,
                timeout: 7000
            }
        });
        map.addControl(geolocateControl);

        geolocateControl.events.register('locationupdated', this, function(e) {
            draftLayer.removeAllFeatures();
            var circle = new OpenLayers.Feature.Vector(
                OpenLayers.Geometry.Polygon.createRegularPolygon(
                    new OpenLayers.Geometry.Point(e.point.x, e.point.y),
                    e.position.coords.accuracy / 2,
                    40,
                    0
                ),
                {},
                style
            );
            draftLayer.addFeatures([
                new OpenLayers.Feature.Vector(
                    e.point,
                    {},
                    {graphicName: 'cross',
                     strokeColor: '#f00',
                     strokeWidth: 2,
                     fillOpacity: 0,
                     pointRadius: 10
                    }
                ),
                circle
            ]);
            map.zoomToExtent(draftLayer.getDataExtent());
            pulsate(map, circle);
        });

        geolocateControl.events.register('locationfailed', this, function() {
            OpenLayers.Console.log('Location detection failed');
        });

        // Toolbar Button
        var geoLocateButton = new Ext.Button({
            iconCls: 'geolocation',
            tooltip: i18n.gis_geoLocate,
            handler: function() {
                draftLayer.removeAllFeatures();
                //geolocateControl.deactivate();
                //geolocateControl.watch = false;
                geolocateControl.activate();
            }
        });
        toolbar.addButton(geoLocateButton);
    };

    /**
     * Supports GeoLocate control
     */
    var pulsate = function(map, feature) {

        var point = feature.geometry.getCentroid(),
            bounds = feature.geometry.getBounds(),
            radius = Math.abs((bounds.right - bounds.left) / 2),
            count = 0,
            grow = 'up';

        var resize = function(){
            if (count > 16) {
                clearInterval(window.resizeInterval);
            }
            var interval = radius * 0.03;
            var ratio = interval / radius;
            switch(count) {
                case 4:
                case 12:
                    grow = 'down'; break;
                case 8:
                    grow = 'up'; break;
            }
            if (grow !== 'up') {
                ratio = - Math.abs(ratio);
            }
            feature.geometry.resize(1 + ratio, point);
            map.s3.draftLayer.drawFeature(feature);
            count++;
        };
        window.resizeInterval = window.setInterval(resize, 50, point, radius);
    };

    /* Google Earth control
    var addGoogleEarthControl = function(toolbar) {
        var map = toolbar.map;
        var s3 = map.s3;
        // Toolbar Button
        var googleEarthButton = new Ext.Button({
            iconCls: 'googleearth',
            tooltip: s3.options.Google.Earth,
            enableToggle: true,
            toggleHandler: function(button, state) {
                if (state === true) {
                    s3.mapPanelContainer.getLayout().setActiveItem(1);
                    // Since the LayerTree isn't useful, collapse it
                    s3.mapWin.items.items[0].collapse();
                    s3.googleEarthPanel.on('pluginready', function() {
                        addGoogleEarthKmlLayers(map);
                    });
                } else {
                    s3.mapPanelContainer.getLayout().setActiveItem(0);
                    s3.mapWin.items.items[0].expand();
                }
            }
        });
        toolbar.addSeparator();
        toolbar.addButton(googleEarthButton);
    }; */

    /* Supports GE Control
    var addGoogleEarthKmlLayers = function(map) {
        var layers_feature = map.s3.options.layers_feature;
        if (layers_feature) {
            for (var i = 0; i < layers_feature.length; i++) {
                var layer = layers_feature[i];
                var visibility;
                if (undefined !== layer.visibility) {
                    visibility = layer.visibility;
                } else {
                    // Default to visible
                    visibility = true;
                }
                if (visibility) {
                    // @ToDo: Add Authentication when-required
                    var url = S3.public_url + layer.url.replace('geojson', 'kml');
                    google.earth.fetchKml(map.s3.googleEarthPanel.earth, url, googleEarthKmlLoaded);
                }
            }
        }
    };

    var googleEarthKmlLoaded = function(object) {
        if (!object) {
            return;
        }
        S3.gis.googleEarthPanel.earth.getFeatures().appendChild(object);
    }; */

    /**
     * Google Streetview control
     */
    var addGoogleStreetviewControl = function(toolbar) {

        var map = toolbar.map;
        var Clicker = OpenLayers.Class(OpenLayers.Control, {
            defaults: {
                pixelTolerance: 1,
                stopSingle: true
            },
            initialize: function(/* options */) {
                this.handlerOptions = OpenLayers.Util.extend(
                    {}, this.defaults
                );
                OpenLayers.Control.prototype.initialize.apply(this, arguments);
                this.handler = new OpenLayers.Handler.Click(
                    this, {click: this.trigger}, this.handlerOptions
                );
            },
            trigger: function(event) {
                openStreetviewPopup(map, map.getLonLatFromViewPortPx(event.xy));
            }
        });
        var StreetviewClicker = new Clicker({autoactivate: false});
        map.addControl(StreetviewClicker);

        // Toolbar Button
        var googleStreetviewButton = new Ext.Button({
            iconCls: 'streetview',
            tooltip: map.s3.options.Google.StreetviewButton,
            allowDepress: true,
            enableToggle: true,
            toggleGroup: 'controls',
            toggleHandler: function(button, state) {
                if (state === true) {
                    StreetviewClicker.activate();
                } else {
                    StreetviewClicker.deactivate();
                }
            }
        });
        toolbar.addSeparator();
        toolbar.addButton(googleStreetviewButton);
    };

    /**
     * Supports Streetview Control
     */
    var openStreetviewPopup = function(map, location) {

        if (!location) {
            location = map.getCenter();
        }
        // Only allow 1 SV Popup/map
        if (map.s3.sv_popup && map.s3.sv_popup.anc) {
            map.s3.sv_popup.close();
        }
        map.s3.sv_popup = new GeoExt.Popup({
            title: map.s3.options.Google.StreetviewTitle,
            location: location,
            width: 300,
            height: 300,
            collapsible: true,
            map: map.s3.mapPanel,
            items: [new gxp.GoogleStreetViewPanel()]
        });
        map.s3.sv_popup.show();
    };

    /**
     * Measure Controls
     */
    var addMeasureControls = function(toolbar) {

        var map = toolbar.map;
        // Common components
        var measureSymbolizers = {
            'Point': {
                pointRadius: 5,
                graphicName: 'circle',
                fillColor: 'white',
                fillOpacity: 1,
                strokeWidth: 1,
                strokeOpacity: 1,
                strokeColor: '#f5902e'
            },
            'Line': {
                strokeWidth: 3,
                strokeOpacity: 1,
                strokeColor: '#f5902e',
                strokeDashstyle: 'dash'
            },
            'Polygon': {
                strokeWidth: 2,
                strokeOpacity: 1,
                strokeColor: '#f5902e',
                fillColor: 'white',
                fillOpacity: 0.5
            }
        };
        var styleMeasure = new OpenLayers.Style();
        styleMeasure.addRules([
            new OpenLayers.Rule({symbolizer: measureSymbolizers})
        ]);
        var styleMapMeasure = new OpenLayers.StyleMap({'default': styleMeasure});

        // Length Button
        var length = new OpenLayers.Control.Measure(
            OpenLayers.Handler.Path, {
                geodesic: true,
                persist: true,
                handlerOptions: {
                    layerOptions: {styleMap: styleMapMeasure}
                }
            }
        );
        length.events.on({
            'measure': function(evt) {
                alert(i18n.gis_length_message + ' ' + evt.measure.toFixed(2) + ' ' + evt.units);
            }
        });

        // Toolbar Buttons
        // 1st of these 2 to get activated cannot be deselected!
        var lengthButton = new GeoExt.Action({
            control: length,
            map: map,
            iconCls: 'measure-off',
            // button options
            tooltip: i18n.gis_length_tooltip,
            allowDepress: true,
            enableToggle: true,
            toggleGroup: 'controls'
        });

        toolbar.add(lengthButton);

        // Don't include the Area button in the Location Selector
        if (false === map.s3.options.area) {
            // Area Button
            var area = new OpenLayers.Control.Measure(
                OpenLayers.Handler.Polygon, {
                    geodesic: true,
                    persist: true,
                    handlerOptions: {
                        layerOptions: {styleMap: styleMapMeasure}
                    }
                }
            );
            area.events.on({
                'measure': function(evt) {
                    alert(i18n.gis_area_message + ' ' + evt.measure.toFixed(2) + ' ' + evt.units + '2');
                }
            });

            var areaButton = new GeoExt.Action({
                control: area,
                map: map,
                iconCls: 'measure-area',
                // button options
                tooltip: i18n.gis_area_tooltip,
                allowDepress: true,
                enableToggle: true,
                toggleGroup: 'controls'
            });

            toolbar.add(areaButton);
        }
    };

    /**
     * Legend Panel as floating DIV
     */
    var addLegendPanel = function(map) {

        var map_id = map.s3.id;
        var div = '<div class="map_legend_div"><div class="map_legend_tab right"></div><div class="map_legend_panel"></div></div>';
        $('#' + map_id).append(div);
        var legendPanel = new GeoExt.LegendPanel({
            title: i18n.gis_legend,
            // Ext 4.x option
            //maxHeight: 600,
            autoScroll: true,
            border: false
        });
        var jquery_obj = $('#' + map_id + ' .map_legend_panel');
        var el = Ext.get(jquery_obj[0]);
        legendPanel.render(el);

        // Show/Hide Legend when clicking on Tab
        $('#' + map_id + ' .map_legend_tab').click(function() {
            if ($(this).hasClass('right')) {
                hideLegend(map);
            } else {
                showLegend(map);
            }
        });

        return legendPanel;
    };

    /**
     * Hide the legend
     */
    var hideLegend = function(map) {

        var map_id = map.s3.id;
        var outerWidth = $('#' + map_id + ' .map_legend_panel').outerWidth();
        $('#' + map_id + ' .map_legend_div').animate({
            marginRight: '-' + outerWidth + 'px'
        });
        $('#' + map_id + ' .map_legend_tab').removeClass('right')
                                            .addClass('left');
    };

    /**
     * Show the legend
     */
    var showLegend = function(map) {

        var map_id = map.s3.id;
        $('#' + map_id + ' .map_legend_div').animate({
            marginRight: 0
        });
        $('#' + map_id + ' .map_legend_tab').removeClass('left')
                                            .addClass('right');
    };

    /**
     * Navigation History
     */
    var addNavigationControl = function(toolbar) {

        var nav = new OpenLayers.Control.NavigationHistory();
        toolbar.map.addControl(nav);
        nav.activate();
        // Toolbar Buttons
        var navPreviousButton = new Ext.Button({
            iconCls: 'back',
            tooltip: i18n.gis_navPrevious,
            handler: nav.previous.trigger
        });
        var navNextButton = new Ext.Button({
            iconCls: 'next',
            tooltip: i18n.gis_navNext,
            handler: nav.next.trigger
        });
        toolbar.addButton(navPreviousButton);
        toolbar.addButton(navNextButton);
    };

    /**
     * Point Control to add new Markers to the Map
     */
    var addPointControl = function(map, toolbar, active, config) {

        OpenLayers.Handler.PointS3 = OpenLayers.Class(OpenLayers.Handler.Point, {
            // Ensure that we propagate Double Clicks (so we can still Zoom)
            dblclick: function(/* evt */) {
                //OpenLayers.Event.stop(evt);
                return true;
            },
            CLASS_NAME: 'OpenLayers.Handler.PointS3'
        });

        var draftLayer = map.s3.draftLayer;
        var control = new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.PointS3, {
            // custom Callback
            'featureAdded': function(feature) {
                // Remove previous point
                if (map.s3.lastDraftFeature) {
                    map.s3.lastDraftFeature.destroy();
                } else if (draftLayer.features.length > 1) {
                    // Clear the one from the Current Location in S3LocationSelector
                    draftLayer.features[0].destroy();
                }
                // Destroy all popups
                while (map.popups.length > 0) {
                    map.removePopup(map.popups[0]);
                }
                if (undefined !== map.s3.pointPlaced) {
                    // Call Custom Call-back
                    map.s3.pointPlaced(feature, config);
                }
                // Prepare in case user selects a new point
                map.s3.lastDraftFeature = feature;
            }
        });

        if (toolbar) {
            // Toolbar Button
            var tooltip;
            if (config && config.l) {
                tooltip = config.l;
            } else {
                tooltip = i18n.gis_draw_feature;
            }
            var map_id = map.s3.id;
            var pointButton = new GeoExt.Action({
                control: control,
                handler: function() {
                    if (pointButton.items[0].pressed) {
                        $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');
                        var colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('disable');
                        }
                    } else {
                        $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
                    }
                },
                map: map,
                iconCls: 'drawpoint-off',
                tooltip: tooltip,
                allowDepress: true,
                enableToggle: true,
                toggleGroup: 'controls',
                pressed: active
            });
            toolbar.add(pointButton);
            if (active) {
                $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');
                var colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                if (colorpicker.length) {
                    colorpicker.spectrum('disable');
                }
            }
            // Pass to Global scope for LocationSelectorWidget
            map.s3.pointButton = pointButton;
        } else {
            // Simply add straight to the map
            map.addControl(control);
            if (active) {
                control.activate();
                $('#' + map.s3.id + '_panel .olMapViewport').addClass('crosshair');
            }
        }
    };

    /**
     * Line Control to draw Lines on the Map
     */
    var addLineControl = function(map, toolbar, active, config) {

        var draftLayer = map.s3.draftLayer;
        var control = new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Path, {
            // custom Callback
            'featureAdded': function(feature) {
                // Remove previous line
                if (map.s3.lastDraftFeature) {
                    map.s3.lastDraftFeature.destroy();
                } else if (draftLayer.features.length > 1) {
                    // Clear the one from the Current Location in S3LocationSelector
                    draftLayer.features[0].destroy();
                }
                // Destroy all popups
                while (map.popups.length > 0) {
                    map.removePopup(map.popups[0]);
                }
                if (undefined !== map.s3.pointPlaced) {
                    // Call Custom Call-back
                    map.s3.pointPlaced(feature, config);
                }
                // Prepare in case user draws a new line
                map.s3.lastDraftFeature = feature;
            }
        });

        if (toolbar) {
            // Toolbar Button
            var tooltip;
            if (config && config.l) {
                tooltip = config.l;
            } else {
                tooltip = i18n.gis_draw_line;
            }
            var map_id = map.s3.id,
                colorpicker;
            var lineButton = new GeoExt.Action({
                control: control,
                handler: function() {
                    if (lineButton.items[0].pressed) {
                        $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');
                        colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('enable');
                        }
                    } else {
                        $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
                        colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('disable');
                        }
                    }
                },
                map: map,
                iconCls: 'drawline-off',
                tooltip: tooltip,
                allowDepress: true,
                enableToggle: true,
                toggleGroup: 'controls',
                pressed: active,
                activateOnEnable: true,
                deactivateOnDisable: true
            });
            toolbar.add(lineButton);
            // Pass to Global scope for LocationSelectorWidget
            map.s3.lineButton = lineButton;
        } else {
            // Simply add straight to the map
            map.addControl(control);
            if (active) {
                control.activate();
                $('#' + map.s3.id + '_panel .olMapViewport').addClass('crosshair');
            }
        }
    };

    /**
     * Polygon Control to select Areas on the Map
     */
    var addPolygonControl = function(map, toolbar, active, not_regular, config) {

        var s3 = map.s3,
            draftLayer = s3.draftLayer;
        var control = new OpenLayers.Control.DrawFeature(draftLayer,
            not_regular ? OpenLayers.Handler.Polygon :
                          OpenLayers.Handler.RegularPolygon, {
            handlerOptions: not_regular ? {
                sides: 4,
                snapAngle: 90
            } : {},
            // custom Callback
            'featureAdded': function(feature) {
                // Remove previous polygon
                if (s3.lastDraftFeature) {
                    s3.lastDraftFeature.destroy();
                } else if (draftLayer.features.length > 1) {
                    // Clear the one from the Current Location in S3LocationSelector
                    draftLayer.features[0].destroy();
                }
                var wkt_field = $('#gis_location_wkt');
                if (wkt_field.length) {
                    // Update form fields in S3LocationSelectorWidget
                    // (S3LocationSelector uses the map.s3.pointPlaced hook in s3.ui.locationselector.js, which is a better design)
                    var WKT = feature.geometry.transform(map.getProjectionObject(), proj4326).toString();
                    wkt_field.val(WKT);
                    $('#gis_location_lat').val('');
                    $('#gis_location_lon').val('');
                }
                /* Old S3Search
                else {
                    // See if we have a relevant Search Filter
                    var wkt_search_field = $('#gis_search_polygon_input');
                    if (wkt_search_field.length) {
                        var WKT = feature.geometry.transform(map.getProjectionObject(), proj4326).toString();
                        wkt_search_field.val(WKT).trigger('change');
                    }
                }*/
                // Destroy all popups
                while (map.popups.length > 0) {
                    map.removePopup(map.popups[0]);
                }
                if (undefined !== s3.pointPlaced) {
                    // Call Custom Call-back
                    s3.pointPlaced(feature, config);
                }
                // Prepare in case user draws a new polygon
                s3.lastDraftFeature = feature;
            }
        });

        var map_id = s3.id;
        if (toolbar) {
            // Toolbar Button
            var tooltip;
            if (config && config.l) {
                tooltip = config.l;
            } else {
                tooltip = i18n.gis_draw_polygon;
            }
            var polygonButton = new GeoExt.Action({
                control: control,
                handler: function() {
                    var btn = polygonButton.items[0],
                        colorpicker;
                    if (btn.pressed) {
                        polygonButton.setIconClass('drawpolygonclear-off');
                        btn.tooltip = i18n.gis_draw_polygon_clear;
                        btn.setTooltip(i18n.gis_draw_polygon_clear);
                        $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');
                        colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('enable');
                        }
                    } else {
                        polygonButton.setIconClass('drawpolygon-off');
                        btn.tooltip = tooltip;
                        btn.setTooltip(tooltip);
                        $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
                        colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('disable');
                        }
                        if (s3.lastDraftFeature) {
                            s3.lastDraftFeature.destroy();
                        } else if (draftLayer.features.length > 1) {
                            // Clear the one from the Current Location in S3LocationSelector
                            draftLayer.features[0].destroy();
                        }
                        if (undefined !== s3.polygonButtonOff) {
                            // Call Custom Call-back (used by S3MapFilter)
                            s3.polygonButtonOff();
                        }
                    }
                },
                map: map,
                iconCls: 'drawpolygon-off',
                tooltip: tooltip,
                allowDepress: true,
                enableToggle: true,
                toggleGroup: 'controls',
                pressed: active,
                activateOnEnable: true,
                deactivateOnDisable: true
            });
            toolbar.add(polygonButton);
            // Pass to Global scope for LocationSelectorWidget & S3MapFilter
            s3.polygonButton = polygonButton;
        } else {
            // Simply add straight to the map
            map.addControl(control);
            if (active) {
                control.activate();
                $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');
                addPolygonPanel(map_id, control);
            }
        }
    };

    /**
     * Floating DIV to explain & control
     */
    var addPolygonPanel = function(map_id, control) {

        if (undefined === control) {
            var i,
                len,
                controls = S3.gis.maps[map_id].controls;
            for (i=0, len=controls.length; i < len; i++) {
                control = controls[i];
                if (control.CLASS_NAME == 'OpenLayers.Control.DrawFeature') {
                    break;
                }
            }
        }
        // @ToDo: i18n
        var msg = 'Click anywhere on the map to begin drawing. Double click to complete the area or click the Finish button below.';
        var div = '<div class="map_polygon_panel">' + msg + '<div class="map_polygon_buttons"><a class="button small map_polygon_finish">' + 'Finish' + '</a><a class="button small map_polygon_clear">' + 'Clear' + '</a></div></div>';
        $('#' + map_id).append(div);

        // Click Handlers
        var s3 = S3.gis.maps[map_id].s3;
        $('#' + map_id + ' .map_polygon_finish').click(function() {
            // Complete the Polygon (which in-turn will call pointPlaced)
            control.finishSketch();

            if (undefined !== s3.polygonPanelFinish) {
                // Call Custom Call-back (used by S3MapFilter in WACOP)
                s3.polygonPanelFinish();
            } else {
                if (s3.lastDraftFeature) {
                    s3.lastDraftFeature.destroy();
                } else if (s3.draftLayer.features.length > 1) {
                    // Clear the one from the Current Location in S3LocationSelector
                    s3.draftLayer.features[0].destroy();
                }
                control.deactivate();
                $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
            }
        });

        $('#' + map_id + ' .map_polygon_clear').click(function() {
            if (s3.lastDraftFeature) {
                s3.lastDraftFeature.destroy();
            } else if (s3.draftLayer.features.length > 1) {
                // Clear the one from the Current Location in S3LocationSelector
                s3.draftLayer.features[0].destroy();
            }
            control.deactivate();
            $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
            if (undefined !== s3.polygonPanelClear) {
                // Call Custom Call-back (used by S3MapFilter in WACOP)
                s3.polygonPanelClear();
            }
        });

        return control;
    };
    // Pass to global scope so that it can be called from custom S3MapFilter buttons
    S3.gis.addPolygonPanel = addPolygonPanel;

    // Enable this once CIRCULARSTRING is fully supported
    // Get the points on the circumference of the circle
    /*var getCircumferencePoints = function(lat_center, lon_center, radius) {
        var angles = [0, 90, 180, 270]
        var lon = []
        var lat = []
        for (var i = 0; i < angles.length; i++) {
            var lon_ = radius*Math.cos(angles[i]) + lon_center;
            lon[i] = lon_;
            var lat_ = radius*Math.sin(angles[i]) + lat_center;
            lat[i] = lat_;
        }
        return [lon, lat];
    };*/

    /**
     * Circle Control to draw circles on the Map
     */
    var addCircleControl = function(map, toolbar, active, config) {

        var draftLayer = map.s3.draftLayer;
        var control = new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.RegularPolygon, {
                handlerOptions: {
                     sides: 1000
                },
            // custom Callback
            'featureAdded': function(feature) {
                // Remove previous circle
                if (map.s3.lastDraftFeature) {
                    map.s3.lastDraftFeature.destroy();
                } else if (draftLayer.features.length > 1) {
                    // Clear the one from the Current Location in S3LocationSelector
                    draftLayer.features[0].destroy();
                }
                // Enable this if adding Circle tool support to S3LocationSelectorWidget
                // NB For S3LocationSelector we use a POINT with a radius instead
                /*var wkt_field = $('#gis_location_wkt');
                if (wkt_field.length) {
                    // Update form fields in S3LocationSelectorWidget
                    // (S3LocationSelector does this in s3.ui.locationselector.js, which is a better design)
                    var WKT = feature.geometry.transform(map.getProjectionObject(), proj4326).toString();
                    var linearRing = new OpenLayers.Geometry.LinearRing(feature.geometry.components[0].components);
                    var polygon = new OpenLayers.Geometry.Polygon([linearRing]);
                    var polygonFeature = new OpenLayers.Feature.Vector(polygon, null);
                    var polygonBounds = polygonFeature.geometry.getBounds();
                    var minX = polygonBounds.left;
                    var minY = polygonBounds.bottom;
                    var maxX = polygonBounds.right;
                    var maxY = polygonBounds.top;

                    // Calculate the center coordinates
                    var startX = (minX + maxX) / 2;
                    var startY = (minY + maxY) / 2;

                    // Calculate Radius
                    var startPoint = new OpenLayers.Geometry.Point(startX, startY);
                    var endPoint = new OpenLayers.Geometry.Point(maxX, startY);
                    var radius = new OpenLayers.Geometry.LineString([startPoint, endPoint]);
                    var length = Math.round(radius.getLength()).toString();
                    var lengthMeter = Math.round(radius.getGeodesicLength()).toString();

                    // Get the circumference points on the circle
                    var circumferencePoints = getCircumferencePoints(startX, startY, length);

                    // Prepare the circular string
                    // Enable this once CIRCULARSTRING is fully supported
                    var circularstring = '';
                    for (var i = 0; i < circumferencePoints[0].length; i++) {
                        var lon = circumferencePoints[0][i].toString();
                        var lat = circumferencePoints[1][i].toString();
                        if (i == circumferencePoints[0].length-1) {
                            var point = lon.concat(" ", lat);
                        } else {
                            var point = lon.concat(" ", lat, ",");
                        }
                        circularstring = circularstring.concat(point);
                    }
                    var comment = ''.concat('CIRCULARSTRING(', circularstring, ')');

                    // Data mapped to db field
                    // Note the POLYGON wkt is stored in wkt field
                    // we can use once CIRCULARSTRING is fully supported
                    wkt_field.val(WKT);
                    $('#gis_location_lat').val(startY);
                    $('#gis_location_lon').val(startX);
                    $('#gis_location_radius').val(parseFloat(lengthMeter));
                    $('#gis_location_comments').val(comment);
                }*/
                // Destroy all popups
                while (map.popups.length > 0) {
                    map.removePopup(map.popups[0]);
                }
                if (undefined !== map.s3.pointPlaced) {
                    // Call Custom Call-back
                    map.s3.pointPlaced(feature, config);
                }
                // Prepare in case user draws a new circle
                map.s3.lastDraftFeature = feature;
            }
        });

        if (toolbar) {
            // Toolbar Button
            var tooltip;
            if (config && config.l) {
                tooltip = config.l;
            } else {
                tooltip = i18n.gis_draw_circle;
            }
            var map_id = map.s3.id,
                colorpicker;
            var circleButton = new GeoExt.Action({
                control: control,
                handler: function() {
                    if (circleButton.items[0].pressed) {
                        $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');
                        colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('enable');
                        }
                    } else {
                        $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
                        colorpicker = $('#' + map_id + '_panel .gis_colorpicker');
                        if (colorpicker.length) {
                            colorpicker.spectrum('disable');
                        }
                    }
                },
                map: map,
                iconCls: 'drawcircle-on',
                tooltip: tooltip,
                allowDepress: true,
                enableToggle: true,
                toggleGroup: 'controls',
                pressed: active,
                activateOnEnable: true,
                deactivateOnDisable: true
            });
            toolbar.add(circleButton);
            // Pass to Global scope for LocationSelectorWidget
            map.s3.circleButton = circleButton;
        } else {
            // Simply add straight to the map
            map.addControl(control);
            if (active) {
                control.activate();
                $('#' + map.s3.id + '_panel .olMapViewport').addClass('crosshair');
            }
        }
    };

    /**
     * Check that Map UI is Loaded
     */
    var uiLoaded = function(map_id) {

        var dfd = new jQuery.Deferred();
        var s3 = S3.gis.maps[map_id].s3;

        // Test every half-second
        setTimeout(function working() {
            if (s3.mapWin !== undefined) {
                dfd.resolve('loaded');
            } else if (dfd.state() === 'pending') {
                // Notify progress
                dfd.notify('waiting for JS to load...');
                // Loop
                setTimeout(working, 500);
            } else {
                // Failed!?
            }
        }, 1);

        // Return the Promise so caller can't change the Deferred
        return dfd.promise();
    };

    /**
     * Convert hex color into RGB tuple
     */
    var hex2rgb = function(hex) {

        var bigint = parseInt(hex, 16),
            r = (bigint >> 16) & 255,
            g = (bigint >> 8) & 255,
            b = bigint & 255;

        return [r, g, b].join();
    };

    /**
     * Convert RGB tuple into hex color
     */
    var rgb2hex = function(r, g, b) {

        return Number(0x1000000 + Math.round(r)*0x10000 + Math.round(g)*0x100 + Math.round(b)).toString(16).substring(1);
    };

    /**
     * ColorPicker to style Features
     * - currently used just by S3LocationSelector
     * - need to pickup in postprocess
     */
    var addColorPickerControl = function(map, toolbar) {

        var s3 = map.s3,
            map_id = s3.id,
            draft_style = s3.options.draft_style,
            value;

        if (draft_style) {
            if (draft_style.fillOpacity) {
                value = 'rgba(' + hex2rgb(draft_style.fill) + ',' + draft_style.fillOpacity + ')';
            } else {
                value = 'rgb(' + hex2rgb(draft_style.fill) + ')';
            }
        } else {
            value = '';
        }
        var colorPickerButton = new Ext.Toolbar.Item({
            html: '<input class="gis_colorpicker" name="colour" value="' + value + '"/>'
        });
        toolbar.add(colorPickerButton);
        $.when(uiLoaded(map_id)).then(
            function(/* status */) {
                // Success: Load Colorpicker
                $('#' + map_id + '_panel .gis_colorpicker').spectrum({
                    showInput: true,
                    showInitial: true,
                    preferredFormat: 'rgb', // needed for Alpha
                    showPaletteOnly: true,
                    togglePaletteOnly: true,
                    palette: ['rgba(255, 0, 0, .5)',    // red
                              'rgba(255, 165, 0, .5)',  // orange
                              'rgba(255, 255, 0, .5)',  // yellow
                              'rgba(0, 255, 0, .5)',    // green
                              'rgba(0, 0, 255, .5)',    // blue
                              'rgba(255, 255, 255, .5)',// white
                              'rgba(0, 0, 0, .5)'       // black
                              ],
                    showAlpha: true,
                    cancelText: i18n.gis_cancelText,
                    chooseText: i18n.gis_chooseText,
                    togglePaletteMoreText: i18n.gis_togglePaletteMoreText,
                    togglePaletteLessText: i18n.gis_togglePaletteLessText,
                    clearText: i18n.gis_clearText,
                    noColorSelectedText: i18n.gis_noColorSelectedText,
                    change: function(colour) {
                        // Modify the Style of the Draft Layer
                        var style = {fill: rgb2hex(colour._r, colour._g, colour._b)};
                        if (colour._a != 1) {
                            style.fillOpacity = colour._a;
                        }
                        var layer = {
                            'style': style,
                            'opacity': 0.9 // trigger the 'select' renderIntent -> Opaque
                        };
                        var response = createStyleMap(map, layer);
                        var featureStyleMap = response[0];
                        var draftLayer = s3.draftLayer;
                        draftLayer.styleMap = featureStyleMap;
                        draftLayer.redraw();
                    }
                });
            },
            function(status) {
                // Failed
                s3_debug(status);
            },
            function(status) {
                // Progress
                s3_debug(status);
            }
        );
    };

    /**
     * Potlatch button for editing OpenStreetMap
     * @ToDo: Select a Polygon for editing rather than the whole Viewport
     */
    var addPotlatchButton = function(toolbar) {

        var map = toolbar.map;
        // Toolbar Button
        var potlatchButton = new Ext.Button({
            iconCls: 'potlatch',
            tooltip: i18n.gis_potlatch,
            handler: function() {
                // Read current settings from map
                var zoom_current = map.getZoom();
                if (zoom_current < 14) {
                    alert(i18n.gis_osm_zoom_closer);
                } else {
                    var lonlat = map.getCenter();
                    // Convert back to LonLat for saving
                    lonlat.transform(map.getProjectionObject(), proj4326);
                    var url = S3.Ap.concat('/gis/potlatch2/potlatch2.html') + '?lat=' + lonlat.lat + '&lon=' + lonlat.lon + '&zoom=' + zoom_current;
                    window.open(url);
                }
            }
        });
        toolbar.addSeparator();
        toolbar.addButton(potlatchButton);
    };

    /**
     * Print button on Toolbar to save a screenshot
     */
    var addPrintButton = function(toolbar) {

        var map = toolbar.map,
            map_id = map.s3.id;

        // Toolbar Button
        var printButton = new Ext.Button({
            iconCls: 'print',
            tooltip: i18n.gis_print_tip,
            menu: {
                xtype: 'menu',
                plain: true,
                items: [{
                    xtype: 'form',
                    bodyPadding: 5,
                    items: [{
                        xtype: 'combo',
                        allowBlank: false,
                        displayField: 'label',
                        fieldLabel: i18n.gis_paper_size,
                        getListParent: function() {
                            return this.el.up('.x-menu');
                        },
                        hiddenName: 'size',
                        id: map_id + '_paper_size',
                        lazyInit: false,
                        mode: 'local',
                        selectOnFocus: true,
                        store: new Ext.data.ArrayStore({
                            id: 0,
                            fields: [
                                'size',
                                'label'
                            ],
                            // @ToDo: Make configurable
                            data: [
                                   ['Letter', 'Letter (2550 x 3300)'], // 612 x 792 @ 72ppi
                                   ['A4', 'A4 (2480 x 3508)'],         // 595 x 842 @ 72ppi
                                   ['A3', 'A3 (3508 x 4962)'],         // 842 x 1191 @ 72ppi
                                   ['A2', 'A2 (4962 x 7017)'],         // 1191 x 1684 @ 72ppi
                                   ['A1', 'A1 (7017 x 9933)'],         // 1684 x 2384 @ 72ppi
                                   ['A0', 'A0 (9933 x 14061)']         // 2384 x 3375 @ 72ppi
                                   ]
                        }),
                        triggerAction: 'all',
                        typeAhead: true,
                        // @ToDo: Make configurable
                        value: 'Letter',
                        valueField: 'size'
                    }, {
                        xtype: 'button',
                        text: i18n.gis_print,
                        handler: function() {
                            // Save the configuration to a temporary config
                            // Modify the zoom so that the viewport covers the same area
                            var size = $('#x-form-el-' + map_id + '_paper_size input[name="size"]').val(),
                                height,
                                width;
                            if (size == 'Letter') {
                                height = 2550; // 612 for 72ppi
                                width = 3300;  // 792 for 72ppi
                            } else if (size == 'A4') {
                                height = 2480; // 595 for 72ppi
                                width = 3508;  // 842 for 72ppi
                            } else if (size == 'A3') {
                                height = 3508; // 842 for 72ppi
                                width = 4962;  // 1191 for 72ppi
                            } else if (size == 'A2') {
                                height = 4962; // 1191 for 72ppi
                                width = 7017;  // 1684 for 72ppi
                            } else if (size == 'A1') {
                                height = 7017; // 1684 for 72ppi
                                width = 9933;  // 2384 for 72ppi
                            } else if (size == 'A0') {
                                height = 9933; // 2384 for 72ppi
                                width = 14061; // 3375 for 72ppi
                            }
                            var extent = map.getExtent();
                            var viewSize = new OpenLayers.Size(width, height);
                            var idealResolution = Math.max( extent.getWidth()  / viewSize.w,
                                                            extent.getHeight() / viewSize.h );
                            var zoom = map.baseLayer.getZoomForResolution(idealResolution);
                            var config_id = saveConfig(map, true, zoom);
                            // Take the screenshot
                            var url = S3.Ap.concat('/gis/screenshot/' + config_id + '?size=' + size);
                            window.open(url);
                        }
                    }]
                }]
            }

        });
        toolbar.addButton(printButton);
    };

    /**
     * Save button on Toolbar to save the Viewport settings
     */
    var addSaveButton = function(toolbar) {
        // Toolbar Button
        var saveButton = new Ext.Button({
            iconCls: 'save',
            tooltip: i18n.gis_save,
            handler: function() {
                saveConfig(toolbar.map);
            }
        });
        toolbar.addButton(saveButton);
    };

    /**
     * Save button as floating DIV to save the Viewport settings
     */
    var addSavePanel = function(map) {

        var s3 = map.s3,
            map_id = s3.id;

        if ($('#' + map_id + ' .map_save_panel').length) {
            // We already have a Panel
            // (this happens when switching between full-screen & embedded)
            return;
        }
        var name_display = '<div class="fleft"><div class="map_save_name">';
        var config_name = s3.options.config_name;
        // Don't show if this is the default map
        if (config_name) {
            name_display += config_name;
        }
        name_display += '</div></div>';
        var div = '<div class="map_save_panel off">' + name_display + '<div class="btn map_save_button"><div class="map_save_label">' + i18n.gis_save_map + '</div></div></div>';
        $('#' + map_id).append(div);
        if (config_name) {
            $('#' + map_id + ' .map_save_panel').removeClass('off');
        }
        // Click Handler
        $('#' + map_id + ' .map_save_button').click(function() {
            saveClickHandler(map);
        });
    };

    /**
     * Save Click Handler for floating DIV
     */
    var saveClickHandler = function(map) {

        var map_id = map.s3.id;
        $('#' + map_id + ' .map_save_panel').removeClass('off');
        // Remove any 'saved' notification
        $('#' + map_id + ' .map_save_panel .saved').remove();
        // Show the Input
        $('#' + map_id + ' .map_save_panel .fleft').show();
        // Rename the Save button
        $('#' + map_id + ' .map_save_label').html(i18n.save);
        nameConfig(map);
    };

    /**
     * Name the Config for floating DIV
     */
    var nameConfig = function(map) {

        var s3 = map.s3,
            map_id = s3.id,
            options = s3.options,
            config_id = options.config_id,
            name;

        if (options.config_name) {
            name = options.config_name;
        } else {
            name = '';
        }
        var save_button = $('#' + map_id + ' .map_save_button');

        // Prompt user for the name
        var input_id = map_id + '_save',
            name_input = $('#' + input_id);

        if (!name_input.length) {
            //name_input = '<input id="' + input_id + '" value="' + name + '">';
            var hint = '<label for="' + input_id + '">' + i18n.gis_name_map + '</label>';
            name_input = '<div class="hint">' + hint + name_input + '</div>';
            var disabled;
            if (config_id) {
                disabled = '';
            } else {
                disabled = ' disabled="disabled" checked="checked"';
            }
            var checkbox = '<div class="new_map"><input type="checkbox" class="checkbox"' + disabled + '>' + i18n.gis_new_map + '</div>';
            $('#' + map_id + ' .map_save_panel .fleft').html(name_input + checkbox);
            $('#' + map_id + ' .map_save_panel label').labelOver('over');
        }
        // Click Handler
        save_button.unbind('click')
                   .click(function() {
            saveConfig(map);
            //save_button.hide();
            // Update Map name
            var name = $('#' + map_id + '_save').val();
            $('#' + map_id + ' .map_save_name').html(name);
            options.config_name = name;
            var pe_url;
            if (options.pe_id) {
                // Normal user
                pe_url = '?~.pe_id__belongs=' + options.pe_id;
            } else {
                // Map Admin
                pe_url = '';
            }
            var div = '<div class="saved"><p><i>' + i18n.saved + '</i></p><p><a href="' + S3.Ap.concat('/gis/config') + pe_url + '">' + i18n.gis_my_maps + '</a></p></div>';
            $('#' + map_id + ' .map_save_panel .fleft').hide()
                                                       .before(div);
            // Enable the 'Save as New Map' checkbox
            $('#' + map_id + ' .map_save_panel .checkbox').prop('checked', false)
                                                          .prop('disabled', false);
            // Restore original click handler
            save_button.unbind('click')
                       .click(function() {
                saveClickHandler(map);
            });
        });
        // Cancel Handler
        var savePanel = $('#' + map_id + ' .map_save_panel');
        $('html').unbind('click.cancelSave')
                 .bind('click.cancelSave', function() {
            savePanel.addClass('off');
            // Restore original click handler
            save_button.unbind('click')
                       .click(function() {
                savePanel.removeClass('off')
                         .unbind('click');
                nameConfig(map);
            });
        });
        savePanel.click(function(event) {
            // Don't activate if clicking inside
            event.stopPropagation();
        });
    };

    /**
     * Save the Config (used by both Toolbar & Floating DIV)
     */
    var saveConfig = function(map, temp, zoom) {

        var s3 = map.s3;
        var map_id = s3.id;
        // Show Throbber
        showThrobber(map_id);
        // Read current settings from map
        var state = getState(map);
        // IE8+ https://en.wikipedia.org/wiki/JavaScript_Object_Notation#Native_encoding_and_decoding_in_browsers
        //var encode = Ext.util.JSON.encode;
        var encode = JSON.stringify;
        var layersStr = encode(state.layers);
        var pluginsStr = encode(state.plugins);
        var json_data = {
            lat: state.lat,
            lon: state.lon,
            zoom: zoom || state.zoom,
            layers: layersStr,
            plugins: pluginsStr
        };
        var options = s3.options;
        if (options.pe_id) {
            json_data.pe_id = options.pe_id;
        }
        var config_id,
            update;
        if (temp) {
            update = false;
            json_data.temp = 1;
        } else {
            var name_input = $('#' + map_id + '_save');
            config_id = options.config_id;
            if (name_input.length) {
                // Floating Save Panel
                json_data.hide = 1;
                json_data.name = name_input.val();
                if (config_id) {
                    // Is this a new one or are we updating?
                    update = !$('#' + map_id + ' .map_save_panel input[type="checkbox"]').prop('checked');
                } else {
                    update = false;
                }
            } else if (config_id) {
                update = true;
            } else {
                update = false;
            }
        }
        // Use AJAX to send back
        var url;
        if (update) {
            url = S3.Ap.concat('/gis/config/' + config_id + '.url/update');
        } else {
            url = S3.Ap.concat('/gis/config.url/create');
        }
        $.ajaxS3({
            async: false, // @ToDo: Rewrite to allow this to be async
            url: url,
            type: 'POST',
            data: json_data,
            dataType : 'json',
            success: function(data /*, status */) {
                config_id = data.id;
                if (!temp && config_id) {

                    var url;
                    // Ensure that future saves are updates, not creates
                    options.config_id = config_id;
                    // Change the browser URL (if-applicable)
                    if (history.pushState) {
                        // Browser supports URL changing without page refresh
                        if (document.location.search) {
                            // We have vars
                            var pairs = document.location.search.split('?')[1].split('&');
                            var pair = [];
                            for (var i=0; i < pairs.length; i++) {
                                pair = pairs[i].split('=');
                                if ((decodeURIComponent(pair[0]) == 'config') && decodeURIComponent(pair[1]) != config_id) {
                                    pairs[i] = 'config=' + config_id;
                                    url = document.location.pathname + '?' + pairs.join('&');
                                    window.history.pushState({}, document.title, url);
                                    break;
                                }
                            }
                        } else if ((document.location.pathname == S3.Ap.concat('/gis/index')) || (document.location.pathname == S3.Ap.concat('/gis/map_viewing_client'))) {
                            // Main map
                            url = document.location.pathname + '?config=' + config_id;
                            window.history.pushState({}, document.title, url);
                        }
                    }
                    // Change the Menu link (if-applicable)
                    url = S3.Ap.concat('/gis/config/', config_id, '/layer_entity');
                    $('#gis_menu_config').attr('href', url);
                }
                // Hide the Throbber
                hideThrobber(null, map);
            }
        });
        // Pass the created config_id back (e.g. for loading the screenshot)
        return config_id;
    };

    /**
     * Get the State of the Map
     * - so that it can be Saved & Reloaded later e.g. for Printing
     */
    var getState = function(map) {

        // State stored a a JSON array
        var state = {};

        // Viewport
        var lonlat = map.getCenter();
        // Convert back to LonLat for saving
        lonlat.transform(map.getProjectionObject(), proj4326);
        state.lon = lonlat.lon;
        state.lat = lonlat.lat;
        state.zoom = map.getZoom();

        // Layers
        // - Visible
        // @ToDo: Popups
        // @ToDo: Filters
        // @ToDo: WMS Browser
        var layers = [];
        var id, layer_config;
        var base_id = map.baseLayer.s3_layer_id;
        Ext.iterate(map.layers, function(key /*, val, obj */) {
            id = key.s3_layer_id;
            layer_config = {
                id: id
            };
            // Only return non-default options
            if (key.visibility) {
                layer_config.visible = key.visibility;
            }
            if (id == base_id) {
                layer_config.base = true;
            }
            if (key.s3_style) {
                layer_config.style = key.s3_style;
            }
            if (key.dir) {
                layer_config.dir = key.dir;
            }
            layers.push(layer_config);
        });
        state.layers = layers;

        // Plugins
        var plugins = [];
        Ext.iterate(map.s3.plugins, function(key /*, val, obj */) {
            if (key.getState) {
                plugins.push(key.getState());
            }
        });
        state.plugins = plugins;

        return state;
    };

    /**
     * Throbber as floating DIV to see when map layers are loading
     */
    var addThrobber = function(map) {

        var s3 = map.s3,
            map_id = s3.id;

        if ($('#' + map_id + ' .layer_throbber').length) {
            // We already have a Throbber
            // (this happens when switching between full-screen & embedded)
            return;
        }

        var div = '<div class="layer_throbber float hide';
        if (s3.options.save) {
            // Add save class so that we know to push throbber down below save button
            div += ' save';
        }
        div += '"></div>';
        $('#' + map_id).append(div);
    };

    /**
     * MGRS Grid PDF Control
     * - select an area on the map to download the grid's PDF to print off
     */
    var addPdfControl = function(toolbar) {

        var map = toolbar.map,
            options = map.s3.options;

        var selectPdfControl = new OpenLayers.Control();
        OpenLayers.Util.extend(selectPdfControl, {
            draw: function() {
                this.box = new OpenLayers.Handler.Box(this, {
                        'done': this.getPdf
                    });
                this.box.activate();
                },
            response: function(req) {
                this.w.destroy();
                var gml = new OpenLayers.Format.GML();
                var features = gml.read(req.responseText);
                var html = features.length + ' pdfs. <br /><ul>';
                if (features.length) {
                    for (var i = 0; i < features.length; i++) {
                        var f = features[i];
                        var text = f.attributes.utm_zone + f.attributes.grid_zone + f.attributes.grid_square + f.attributes.easting + f.attributes.northing;
                        html += "<li><a href='" + features[i].attributes.url + "'>" + text + '</a></li>';
                    }
                }
                html += '</ul>';
                this.w = new Ext.Window({
                    'html': html,
                    width: 300,
                    'title': 'Results',
                    height: 200
                });
                this.w.show();
            },
            getPdf: function(bounds) {
                var current_projection = map.getProjectionObject();
                var ll = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.left, bounds.bottom)).transform(current_projection, proj4326);
                var ur = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top)).transform(current_projection, proj4326);
                var boundsgeog = new OpenLayers.Bounds(ll.lon, ll.lat, ur.lon, ur.lat);
                var bbox = boundsgeog.toBBOX();
                OpenLayers.Request.GET({
                    url: options.mgrs_url + '&bbox=' + bbox,
                    callback: OpenLayers.Function.bind(this.response, this)
                });
                this.w = new Ext.Window({
                    // @ToDo: i18n
                    'html':'Searching ' + options.mgrs_name + ', please wait.',
                    width: 200,
                    // @ToDo: i18n
                    'title': 'Please Wait.'
                    });
                this.w.show();
            }
        });

        // @ToDo: i18n
        var tooltip = 'Select ' + options.mgrs_name;
        // Toolbar Button
        var mgrsButton = new GeoExt.Action({
            text: tooltip,
            control: selectPdfControl,
            map: map,
            allowDepress: false,
            toggleGroup: 'controls',
            tooltip: tooltip
            // check item options group: 'draw'
        });
        toolbar.addSeparator();
        toolbar.add(mgrsButton);
    };

    /**
     * WMS GetFeatureInfo control
     */
    var addWMSGetFeatureInfoControl = function(map) {

        var wmsGetFeatureInfo = new gxp.plugins.WMSGetFeatureInfo({
            actionTarget: 'toolbar',
            outputTarget: 'map',
            outputConfig: {
                width: 400,
                height: 200
            },
            toggleGroup: 'controls',
            // html wasn't permitted by Proxy
            //format: 'grid',
            infoActionTip: i18n.gis_get_feature_info,
            popupTitle: i18n.gis_feature_info
        });
        // Set up shortcut to allow GXP Plugin to work (needs to find portal)
        wmsGetFeatureInfo.target = map.s3;
        // @ToDo: Why do we need to toggle the Measure control before this works?
        //wmsGetFeatureInfo.activate();
        wmsGetFeatureInfo.addActions();
    };

    /**
     * Add/Remove Layers control
     */
    var addRemoveLayersControl = function(map, layerTree) {

        var addLayersControl = new gxp.plugins.AddLayers({
            actionTarget: 'treepanel.tbar',
            // @ToDo: i18n
            addActionTip: 'Add layers',
            addActionMenuText: 'Add layers',
            addServerText: 'Add a New Server',
            doneText: 'Done',
            // @ToDo: CSW
            //search: true,
            upload: {
                // @ToDo
                url: null
            },
            uploadText: i18n.gis_uploadlayer,
            relativeUploadOnly: false
        });

        // @ToDo: Populate this from disabled Catalogue Layers (to which the user has access)
        // Use WMStore for the GeoServer which we can write to?
        // Use current layerStore for Removelayer()?
        //var store = map.s3.mapPanel.layers;
        var store = new GeoExt.data.LayerStore();

        // Set up shortcuts to allow GXP Plugin to work
        addLayersControl.target = layerTree;
        layerTree.proxy = OpenLayers.ProxyHost; // Required for 'Add a New Server'
        layerTree.layerSources = {};
        layerTree.layerSources.local = new gxp.plugins.LayerSource({
            title: 'local',
            store: store
        });
        var actions = addLayersControl.addActions();
        actions[0].enable();

        // @ToDo: Ensure that this picks up when a layer is highlighted
        var removeLayerControl = new gxp.plugins.RemoveLayer({
            actionTarget: 'treepanel.tbar',
            // @ToDo: i18n
            removeActionTip: 'Remove layer'
        });
        // Set up shortcuts to allow GXP Plugin to work
        removeLayerControl.target = layerTree;
        layerTree.mapPanel = map.s3.mapPanel;
        removeLayerControl.addActions();
    };

    /**
     * Layer Properties control
     */
    var addLayerPropertiesButton = function(map, layerTree) {

        // Ensure just 1 propertiesWindow per map
        var propertiesWindow = map.s3.propertiesWindow;
        var layerPropertiesButton = new Ext.Button({
            iconCls: 'gxp-icon-layerproperties',
            tooltip: i18n.gis_properties,
            handler: function() {
                // Find the Selected Node
                function isSelected(node) {
                    var selected = node.isSelected();
                    if (selected) {
                        if (!node.leaf) {
                            // Don't try & open Properties for a Folder
                            return false;
                        } else {
                            return true;
                        }
                    } else {
                        return false;
                    }
                }
                var node = layerTree.root.findChildBy(isSelected, null, true);
                if (node) {
                    var layer_type = node.layer.s3_layer_type;
                    var url = S3.Ap.concat('/gis/layer_' + layer_type + '.plain?layer_' + layer_type + '.layer_id=' + node.layer.s3_layer_id + '&update=1');
                    Ext.Ajax.request({
                        url: url,
                        method: 'GET',
                        success: function(response /* , opts */) {
                            // Close any existing window on this map
                            if (propertiesWindow) {
                                propertiesWindow.close();
                            }
                            var tabPanel;
                            if (layer_type == 'feature') {
                                tabPanel = new Ext.TabPanel({
                                    activeTab: 0,
                                    items: [
                                        {
                                            // Tab to View/Edit Basic Details
                                            // @ToDo: i18n
                                            title: 'Layer Properties',
                                            html: response.responseText
                                        }, {
                                            // Tab for Search Widget
                                            // @ToDo: i18n
                                            title: 'Filter',
                                            id: 's3_gis_layer_filter_tab',
                                            html: ''
                                        }
                                        // @ToDo: Tab for Styling (esp. Thematic Mapping)
                                        ]
                                });
                                tabPanel.items.items[1].on('activate', function() {
                                    // Find which search form to load
                                    // @ToDo: Migrate to S3Filter!
                                    // @ToDo: Look for overrides (e.g. Warehouses/Staff/Volunteers)
                                    // @ToDo: Read current filter settings to default widgets to
                                    var search_url;
                                    Ext.iterate(map.s3.layers_feature, function(key /*, val, obj*/) {
                                        if (key.id == node.layer.s3_layer_id) {
                                            //search_url = S3.Ap.concat('/' + module + '/' + resource + '/search.plain');
                                            search_url = key.url.replace(/.geojson.+/, '/search.plain');
                                        }
                                    });
                                    // @ToDo: Support more than 1/page
                                    Ext.get('s3_gis_layer_filter_tab').load({
                                        url: search_url,
                                        discardUrl: false,
                                        callback: function() {
                                            // Activate Help Tooltips, etc
                                            S3.redraw();
                                            // Handle Options Widgets with collapsed options
                                            //S3.search.select_letter_label();
                                        },
                                        // @ToDo: i18n
                                        text: 'Loading...',
                                        timeout: 30,
                                        scripts: false
                                    });
                                });
                            } else {
                                tabPanel = new Ext.Panel({
                                    // View/Edit Basic Details
                                    // @ToDo: i18n
                                    title: 'Layer Properties',
                                    html: response.responseText
                                });
                            }
                            propertiesWindow = new Ext.Window({
                                width: 400,
                                layout: 'fit',
                                items: [ tabPanel ]
                            });
                            propertiesWindow.show();
                            // Set the form to use AJAX submission
                            $('#plain form').submit(function() {
                                var id = $('#plain input[name="id"]').val();
                                var update_url = S3.Ap.concat('/gis/layer_' + layer_type + '/' + id + '.plain/update');
                                var fields = $('#plain input');
                                var ids = [];
                                Ext.iterate(fields, function(key, val /*, obj */) {
                                    if (val.id && (val.id.indexOf('gis_layer_') != -1)) {
                                        ids.push(val.id);
                                    }
                                });
                                var pcs = [],
                                    q;
                                for (var i=0; i < ids.length; i++) {
                                    q = $('#' + ids[i]).serialize();
                                    if (q) {
                                        pcs.push(q);
                                    }
                                }
                                q = $('#plain input[name="id"]').serialize();
                                if (q) {
                                    pcs.push(q);
                                }
                                q = $('#plain input[name="_formkey"]').serialize();
                                if (q) {
                                    pcs.push(q);
                                }
                                q = $('#plain input[name="_formname"]').serialize();
                                if (q) {
                                    pcs.push(q);
                                }
                                if (pcs.length > 0) {
                                    var query = pcs.join("&");
                                    $.ajaxS3({
                                        type: 'POST',
                                        url: update_url,
                                        data: query,
                                        // gets moved to 'done' inside AjaxS3
                                        success: function(msg) {
                                            $('#plain').html(msg);
                                        }
                                    });
                                }
                                return false;
                            });
                            // Activate Help Tooltips
                            S3.addTooltips();
                            // Activate RoleRequired autocomplete
                            S3.autocomplete.normal('role', 'admin', 'group', 'gis_layer_' + layer_type + '_role_required');
                        }
                    });
                }
            }
        });
        var toolbar = layerTree.getTopToolbar();
        toolbar.add(layerPropertiesButton);
    };

    /**
     * Clear Layers control
     */
    var addClearLayersButton = function(map, toolbar) {

        var clearLayersButton = new Ext.Button({
            iconCls: 'icon-clearlayers',
            tooltip: i18n.gis_clearlayers,
            handler: function() {
                var layers = map.layers;
                for (var i=0, len=layers.length; i < len; i++) {
                    var layer = layers[i];
                    if (!layer.isBaseLayer) {
                        layer.setVisibility(false);
                    }
                }
            }
        });
        toolbar.add(clearLayersButton);
    };

    /**
     * Create a StyleMap
     * - called by addGeoJSONLayer, addKMLLayer & addWFSLayer
     *
     * Parameters:
     * map - {OpenLayers.Map}
     * layer - {Array} (not an OpenLayers.Layer!)
     *
     * Returns:
     * {OpenLayers.StyleMap}
     */
    var createStyleMap = function(map, layer) {

        // Read Options
        var marker_url;
        if (undefined !== layer.marker) {
            // per-Layer Marker
            var marker = layer.marker;
            marker_url = marker_url_path + marker.i;
            var marker_height = marker.h;
            var marker_width = marker.w;
        } else {
            // per-Feature Marker or Shape
            marker_url = '';
        }
        // Default to opaque if undefined
        var opacity = layer.opacity || 1;
        var style = layer.style,
            style_array;
        // If there is a style, is this common to all features or variable?
        if (Object.prototype.toString.call(style) === '[object Array]') {
            style_array = true;
        } else {
            style_array = false;
        }

        // Scale Marker Images if they are too large for this map
        // - especially useful if they are loaded from remote servers (e.g. KML)
        var options = map.s3.options;

        /* Disabled as causing problems with variable markers
        var scaleImage = function() {
            var image = this;
            // Keep these in sync with MAP._setup() in s3gis.py
            var max_h = options.max_h || 35;
            var max_w = options.max_w || 30;
            var scaleRatio = image.height / image.width;
            var w = Math.min(image.width, max_w);
            var h = w * scaleRatio;
            if (h > max_h) {
                h = max_h;
                scaleRatio = w / h;
                w = w * scaleRatio;
            }
            image.height = h;
            image.width = w;
        };

        if (marker_url) {
            // Pre-cache this image
            var image = new Image();
            image.onload = scaleImage;
            image.src = marker_url;
        }*/

        // Feature Styles based on either a common JSON style or per-Feature attributes (Queries)
        // - also used as fallback (e.g. Cluster) for Rules-based Styles
        var styleArray = {
            label: '${label}',
            labelAlign: 'cm',
            pointRadius: '${radius}',
            fillColor: '${fill}',
            fillOpacity: '${fillOpacity}',
            strokeColor: '${stroke}',
            strokeDashstyle: '${strokeDashstyle}',
            // @ToDo:
            //strokeLinecap: '${strokeLinecap}',
            strokeWidth: '${strokeWidth}',
            strokeOpacity: '${strokeOpacity}',
            graphicHeight: '${graphicHeight}',
            graphicWidth: '${graphicWidth}',
            graphicName: '${graphicName}',
            graphicOpacity: opacity,
            graphicXOffset: '${graphicXOffset}',
            graphicYOffset: '${graphicYOffset}',
            graphicZIndex: '${graphicZIndex}',
            externalGraphic: '${externalGraphic}',
            zIndex: '${zIndex}'
        };
        var styleOptions = {
            context: {
                graphicWidth: function(feature) {
                    // We get JS errors if we don't return a number
                    var pix = 1;
                    if (feature.cluster) {
                        // Clustered Point
                        // Doesn't usually use a Graphic
                    } else if (feature.attributes.marker_width) {
                        // Use marker_width from feature
                        pix = feature.attributes.marker_width;
                    } else if (style && !style_array && undefined === style.externalGraphic && undefined === marker_width && feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        // Use Default Marker
                        pix =  options.marker_default.w;
                    } else if (undefined !== marker_width) {
                            // per-Layer Marker for Unclustered Point
                            pix = marker_width;
                    }
                    return pix;
                },
                graphicHeight: function(feature) {
                    // We get JS errors if we don't return a number
                    var pix = 1;
                    if (feature.cluster) {
                        // Clustered Point
                        // Doesn't usually use a Graphic
                    } else if (feature.attributes.marker_height) {
                        // Use marker_height from feature (Query)
                        pix = feature.attributes.marker_height;
                    } else if (style && !style_array && undefined === style.externalGraphic && undefined === marker_height && feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        // Use Default Marker
                        pix =  options.marker_default.h;
                    } else if (undefined !== marker_height) {
                        // per-Layer Marker for Unclustered Point
                        pix = marker_height;
                    }
                    return pix;
                },
                graphicXOffset: function(feature) {
                    // We get JS errors if we don't return a number
                    var pix = -1;
                    if (feature.cluster) {
                        // Clustered Point
                        // Doesn't usually use a Graphic
                    } else if (feature.attributes.marker_width) {
                        // Use marker_width from feature (e.g. FeatureQuery)
                        pix = -(feature.attributes.marker_width / 2);
                    } else if (style && !style_array && undefined === style.externalGraphic && undefined === marker_width && feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        // Use Default Marker
                        pix =  -(options.marker_default.w / 2);
                    } else if (undefined !== marker_width) {
                        // per-Layer Marker for Unclustered Point
                        pix = -(marker_width / 2);
                    }
                    return pix;
                },
                graphicYOffset: function(feature) {
                    // We get JS errors if we don't return a number
                    var pix = -1;
                    if (feature.cluster) {
                        // Clustered Point
                        // Doesn't usually use a Graphic
                    } else if (feature.attributes.marker_height) {
                        // Use marker_height from feature (e.g. FeatureQuery)
                        pix = -feature.attributes.marker_height;
                    } else if (style && !style_array && undefined === style.externalGraphic && undefined === marker_height && feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        // Use Default Marker
                        pix =  -options.marker_default.h;
                    } else if (undefined !== marker_height) {
                        // per-Layer Marker for Unclustered Point
                        pix = -marker_height;
                    }
                    return pix;
                },
                graphicName: function(feature) {
                    // default to a Circle
                    var graphic = 'circle';
                    if (feature.cluster) {
                        // Clustered Point
                        // use default circle
                    } else if (feature.attributes.shape) {
                        // Use graphic from feature (e.g. FeatureQuery)
                        graphic = feature.attributes.shape;
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            if (undefined !== style.graphic) {
                                graphic = style.graphic;
                            }
                        }// else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        //}
                    }
                    return graphic;
                },
                externalGraphic: function(feature) {
                    var url = '';
                    if (feature.cluster) {
                        // Clustered Point
                        // Just show shape not marker
                        // @ToDo: Make this configurable per-Layer & within-Layer as to which gets shown
                        // e.g. http://openflights.org/blog/2009/10/21/customized-openlayers-cluster-strategies/
                    } else if (feature.attributes.marker_url) {
                        // Use marker from feature (Query)
                        url = feature.attributes.marker_url;
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            if (undefined !== style.externalGraphic) {
                                url = S3.Ap.concat('/static/' + style.externalGraphic);
                            } else if (feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                                if (marker_url) {
                                    // Use Layer Marker
                                    return marker_url;
                                } else {
                                    // Use Default Marker
                                    url = marker_url_path + options.marker_default.i;
                                }
                            }
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    } else {
                        if (feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                            // Use Layer Marker
                            return marker_url;
                        }
                    }
                    return url;
                },
                radius: function(feature) {
                    // default Size for Unclustered Point
                    var pix = 10;
                    if (feature.cluster) {
                        // Size for Clustered Point
                        pix = Math.min(feature.attributes.count / 2, 8) + 10;
                    } else if (feature.attributes.size) {
                        // Use size from feature (e.g. FeatureQuery)
                        pix = feature.attributes.size;
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            pix = style.size;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    }
                    return pix;
                },
                fill: function(feature) {
                    var color;
                    if (feature.cluster) {
                        if (feature.cluster[0].attributes.colour) {
                            // Use colour from features (e.g. FeatureQuery)
                            color = feature.cluster[0].attributes.colour;
                        } else {
                            // default fillColor for Clustered Point
                            color = '#' + (options.cluster_fill || cluster_fill_default);
                        }
                    } else if (feature.attributes.colour) {
                        // Feature Query: Use colour from feature (e.g. FeatureQuery)
                        color = feature.attributes.colour;
                    } else if (feature.attributes.style) {
                        // Feature Layer with per-feature Style
                        color = feature.attributes.style.fill;
                        if (undefined !== color) {
                            color = '#' + color;
                        } else {
                            // default fillColor
                            color = '#000000';
                        }
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            color = style.fill;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                        if (undefined !== color) {
                            color = '#' + color;
                        } else {
                            // default fillColor
                            color = '#000000';
                        }
                    } else {
                        // default fillColor for Unclustered Point
                        color = fill_default;
                    }
                    return color;
                },
                fillOpacity: function(feature) {
                    var fillOpacity;
                    if (feature.cluster) {
                        if (feature.cluster[0].attributes.opacity) {
                            // Use opacity from features (e.g. FeatureQuery)
                            fillOpacity = feature.cluster[0].attributes.opacity;
                        } else {
                            // default fillOpacity for Clustered Point
                            fillOpacity = opacity;
                        }
                    } else if (feature.attributes.opacity) {
                        // Use opacity from feature (e.g. FeatureQuery)
                        fillOpacity = feature.attributes.opacity;
                    } else if (feature.attributes.style) {
                        // Feature Layer with per-feature Style
                        fillOpacity = feature.attributes.style.fillOpacity;
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            fillOpacity = style.fillOpacity;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    }
                    // default to layer's opacity
                    return fillOpacity || opacity;
                },
                stroke: function(feature) {
                    var color;
                    if (feature.cluster) {
                        if (feature.cluster[0].attributes.colour) {
                            // Use colour from features (e.g. FeatureQuery)
                            color = feature.cluster[0].attributes.colour;
                        } else {
                            // default strokeColor for Clustered Point
                            color = '#' + (options.cluster_stroke || cluster_stroke_default);
                        }
                    } else if (feature.attributes.colour) {
                        // Use colour from feature (e.g. FeatureQuery)
                        color = feature.attributes.colour;
                    } else if (feature.attributes.style) {
                        // Feature Layer with per-feature Style
                        var fstyle = feature.attributes.style;
                        color = fstyle.stroke || fstyle.fill;
                        if (undefined !== color) {
                            color = '#' + color;
                        } else {
                            // default fillColor
                            color = '#000000';
                        }
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            color = style.stroke || style.fill;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                        if (undefined !== color) {
                            color = '#' + color;
                        } else {
                            // default fillColor
                            color = '#000000';
                        }
                    } else {
                        // default strokeColor for Unclustered Point
                        color = fill_default;
                    }
                    return color;
                },
                strokeOpacity: function(feature) {
                    var strokeOpacity;
                    if (feature.cluster) {
                        if (feature.cluster[0].attributes.opacity) {
                            // Use opacity from features (e.g. FeatureQuery)
                            strokeOpacity = feature.cluster[0].attributes.opacity;
                        } else {
                            // default fillOpacity for Clustered Point
                            strokeOpacity = opacity;
                        }
                    } else if (feature.attributes.opacity) {
                        // Use opacity from feature (e.g. FeatureQuery)
                        strokeOpacity = feature.attributes.opacity;
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            strokeOpacity = style.strokeOpacity;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    }
                    // default to layer's opacity
                    return strokeOpacity || opacity;
                },
                strokeDashstyle: function(/* feature */) {
                    var dashStyle;
                    // if (feature.attributes.strokeDashstyle) {
                    //    // Use strokeDashstyle from feature (e.g. FeatureQuery)
                    //    width = feature.attributes.strokeDashstyle;
                    //} else if (style) {
                    if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            dashStyle = style.strokeDashstyle;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    }
                    // Defalt dashStyle is 'solid'
                    return dashStyle || 'solid';
                },
                strokeWidth: function(feature) {
                    // default strokeWidth
                    var width = 2;
                    if (feature.cluster) {
                        if (feature.cluster[0].attributes.strokeWidth) {
                            // Use colour from features (e.g. FeatureQuery)
                            width = feature.cluster[0].attributes.strokeWidth;
                        }
                    //} else if (feature.attributes.strokeWidth) {
                    //    // Use strokeWidth from feature (e.g. FeatureQuery)
                    //    width = feature.attributes.strokeWidth;
                    } else if (style) {
                        if (!style_array) {
                            // Common Style for all features in layer
                            width = style.strokeWidth;
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    }
                    // Defalt width: 2
                    return width || 2;
                },
                label: function(feature) {
                    // Label for Unclustered Point
                    var label;
                    // Label for Clustered Point
                    if (feature.cluster) {
                        if (options.cluster_label && feature.attributes.count > 1) {
                            label = feature.attributes.count;
                        }
                    } else if (feature.layer && (undefined !== feature.layer.s3_style)) {
                        var style = feature.layer.s3_style;
                        if (!style_array) {
                            // Common Style for all features in layer
                            if (style.show_label) {
                                label = style.label;
                            }
                        } else {
                            // Lookup from rule
                            // - done within OpenLayers.Rule
                        }
                    }
                    return label || '';
                },
                zIndex: function(feature) {
                    // @ToDo: Allow setting within Style
                    if (feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        // Point
                        return 10;
                    } else if (feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Line') {
                        // Line
                        return 5;
                    } else {
                        // Polygon
                        return 0;
                    }
                },
                graphicZIndex: function(feature) {
                    // @ToDo: Allow setting within Style
                    if (feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        // Point
                        return 10;
                    } else if (feature.geometry.CLASS_NAME == 'OpenLayers.Geometry.Line') {
                        // Line
                        return 5;
                    } else {
                        // Polygon
                        return 0;
                    }
                }
            }
        };
        // Needs to be uniquely instantiated
        var featureStyle = new OpenLayers.Style(
            styleArray,
            styleOptions
        );

        if (style_array) {
            // Style Features according to rules in JSON style (currently Feature, Shapefile or Theme Layer)
            var rules = styleRules(layer);
            featureStyle.addRules(rules);
        }

        // @ToDo: Allow customisation of the Select Style
        var selectStyle;
        if (opacity != 1) {
            // Simply make ~opaque onSelect
            var selectOpacity = Math.min(opacity * 2, 0.8);
            selectStyle = {
                fillOpacity: selectOpacity,
                graphicOpacity: selectOpacity
            };
        } else {
            // Change colour onSelect
            selectStyle = {
                fillColor: '#' + (options.select_fill || select_fill_default),
                strokeColor: '#' + (options.select_stroke || select_stroke_default)
            };
        }
        var featureStyleMap = new OpenLayers.StyleMap({
            'default': featureStyle,
            'select': selectStyle
            // Can set this to something different if we have a need for a 3rd style
            //'temporary': tempStyle
        });
        return [featureStyleMap, marker_url];
    };

    /**
     * Create a set of Style Rules
     *
     * Parameters:
     * layer - {Array} (not an OpenLayers.Layer!)
     *
     * Returns:
     * rules - {Array of OpenLayers.Rule}
     */
    var styleRules = function(layer) {

        var style = layer.style,
            rules = [],
            prop,
            rule,
            value,
            elseFilter,
            fill,
            fillOpacity,
            point,
            externalGraphic,
            graphicHeight,
            graphicWidth,
            line,
            strokeOpacity,
            strokeWidth,
            symbolizer;

        $.each(style, function(index, elem) {

            var options = {};
            if (undefined !== elem.fallback) {
                // Fallback Rule
                options.title = elem.fallback;
                elseFilter = options.elseFilter = true;
            } else {
                if (undefined !== elem.prop) {
                    prop = elem.prop;
                } else {
                    // Default (e.g. for Stats/Theme Layers)
                    prop = 'value';
                }
                if (undefined !== elem.cat) {
                    // Category-based style
                    value = elem.cat;
                    options.title = elem.label || value;
                    options.filter = new OpenLayers.Filter.Comparison({
                        type: OpenLayers.Filter.Comparison.EQUAL_TO,
                        property: prop,
                        value: value
                    });
                } else {
                    // Range-based Style
                    options.title = elem.label || (elem.low + '-' + elem.high);
                    options.filter = new OpenLayers.Filter.Comparison({
                        type: OpenLayers.Filter.Comparison.BETWEEN,
                        property: prop,
                        lowerBoundary: elem.low,
                        upperBoundary: elem.high
                    });
                }
            }
            if (undefined !== elem.externalGraphic) {
                point = true;
                line = false;
            } else if (undefined !== elem.size) {
                point = true;
                line = false;
            } else {
                point = false;
            }
            if (undefined !== elem.fill) {
                // Polygon/Point
                line = false;
                fill = '#' + elem.fill;
            } else if (undefined !== elem.stroke) {
                // LineString
                line = true;
                fill = '#' + elem.stroke;
            }
            if (undefined !== elem.fillOpacity) {
                fillOpacity = elem.fillOpacity;
            } else {
                fillOpacity = layer.opacity || 1;
            }
            if (undefined !== elem.strokeOpacity) {
                strokeOpacity = elem.strokeOpacity;
            } else {
                strokeOpacity = 1;
            }
            var graphic;
            if (undefined !== elem.graphic) {
                graphic = elem.graphic;
            } else {
                // Square better for Legend with Polygons
                graphic = 'square';
            }
            if (undefined !== elem.strokeWidth) {
                strokeWidth = elem.strokeWidth;
            } else {
                strokeWidth = 2;
            }
            symbolizer = {
                fillColor: fill, // Used for Legend on LineStrings
                fillOpacity: fillOpacity,
                strokeColor: fill,
                strokeOpacity: strokeOpacity,
                strokeWidth: strokeWidth,
                graphicName: graphic
            };
            if (point) {
                if (undefined !== elem.externalGraphic) {
                    externalGraphic = S3.Ap.concat('/static/' + elem.externalGraphic);
                    var image = new Image();
                    //image.onload = scaleImage;
                    image.src = externalGraphic;
                    graphicHeight = image.height;
                    graphicWidth = image.width;
                    symbolizer.externalGraphic = externalGraphic;
                    symbolizer.graphicHeight = graphicHeight;
                    symbolizer.graphicWidth = graphicWidth;
                    symbolizer.graphicXOffset = -(graphicWidth / 2);
                    symbolizer.graphicYOffset = -graphicHeight;
                }
                symbolizer.pointRadius = elem.size || 10; // This size is used by the Renderer for the Legend
                // Ensure that Points are always above Polygons and Lines
                symbolizer.graphicZIndex = 10;
                symbolizer.zIndex = 10;
                // Hint to the Legend
                symbolizer.Point = symbolizer;
            } else if (line) {
                // Ensure that Lines are always above Polygons (but below Points)
                symbolizer.graphicZIndex = 5;
                symbolizer.zIndex = 5;
                // Hint to the Legend
                symbolizer.Line = symbolizer;
                if (undefined !== elem.strokeDashstyle) {
                    symbolizer.strokeDashstyle = elem.strokeDashstyle;
                }
                // @ToDo:
                //symbolizer.strokeLinecap
            } else {
                // Polygon: default
                //symbolizer.graphicZIndex = 0;
                //symbolizer.zIndex = 0;
                //symbolizer.Polygon = symbolizer;
            }
            options.symbolizer = symbolizer;

            rule = new OpenLayers.Rule(options);
            rules.push(rule);
        });
        if (!elseFilter && (layer.cluster_threshold != 0)) {
            // Default Rule (e.g. for Clusters)
            rule = new OpenLayers.Rule({
                elseFilter: true,
                title: ' '
            });
            rules.push(rule);
        }
        return rules;
    };

}());

// END ========================================================================
