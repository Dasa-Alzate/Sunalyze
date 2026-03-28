CREATE TABLE
  `panels` (
    `nombre` varchar(100) NOT NULL,
    `y` float NOT NULL,
    `tcp` float NOT NULL,
    `tcv` float NOT NULL,
    `voc` float NOT NULL,
    `vmp` float NOT NULL,
    `imp` float NOT NULL,
    `power` float NOT NULL,
    `t_noct` float NOT NULL,
    `height` int NOT NULL,
    `width` int NOT NULL,
    `id` int NOT NULL AUTO_INCREMENT,
    `created_at` datetime DEFAULT NULL,
    `updated_at` datetime DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `nombre` (`nombre`)
  ) ENGINE = InnoDB AUTO_INCREMENT = 13 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
  
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 1954, 1, 13.21, 'AIKO-A500-MAH60Db', 500, 45, -0.26, -0.22, '2025-10-19 18:21:17', 37.9, 45.02, 1134, 22.6);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 1954, 2, 13.3, 'AIKO-A505-MAH60Db', 505, 45, -0.26, -0.22, '2025-10-19 18:21:17', 38, 45.12, 1134, 22.8);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 1954, 3, 13.39, 'AIKO-A510-MAH60Db', 510, 45, -0.26, -0.22, '2025-10-19 18:21:17', 38.1, 45.22, 1134, 23);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 1954, 4, 13.49, 'AIKO-A515-MAH60Db', 515, 45, -0.26, -0.22, '2025-10-19 18:21:17', 38.2, 45.32, 1134, 23.2);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 1954, 5, 13.58, 'AIKO-A520-MAH60Db', 520, 45, -0.26, -0.22, '2025-10-19 18:21:17', 38.3, 45.42, 1134, 23.5);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 2465, 6, 15.44, 'JASolar Bifacial 625W', 625, 45, -0.29, -0.25, '2025-10-19 18:21:17', 43.71, 52.27, 1134, 22.4);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 2465, 7, 15.5, 'JASolar Bifacial 630W', 630, 45, -0.29, -0.25, '2025-10-19 18:21:17', 43.9, 52.47, 1134, 22.5);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 2465, 8, 15.55, 'JASolar Bifacial 635W', 635, 45, -0.29, -0.25, '2025-10-19 18:21:17', 44.1, 52.67, 1134, 22.6);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 2465, 9, 15.61, 'JASolar Bifacial 640W', 640, 45, -0.29, -0.25, '2025-10-19 18:21:17', 44.29, 52.87, 1134, 22.7);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 2465, 10, 15.66, 'JASolar Bifacial 645W', 645, 45, -0.29, -0.25, '2025-10-19 18:21:17', 44.49, 53.07, 1134, 22.8);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 2465, 11, 15.71, 'JASolar Bifacial 650W', 650, 45, -0.29, -0.25, '2025-10-19 18:21:17', 44.67, 53.27, 1134, 22.9);
insert into `panels` (`created_at`, `height`, `id`, `imp`, `nombre`, `power`, `t_noct`, `tcp`, `tcv`, `updated_at`, `vmp`, `voc`, `width`, `y`) values ('2025-10-19 18:21:17', 1909, 12, 13.5, 'Tensite TOPCon 500W', 500, 45, -0.3, -0.24, '2025-10-19 18:21:17', 37.05, 44.4, 1134, 22.25);
