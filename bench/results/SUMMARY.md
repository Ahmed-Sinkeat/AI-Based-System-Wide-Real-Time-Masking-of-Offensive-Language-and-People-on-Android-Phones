## Raw model latency (OpenVINO benchmark_app, batch 1, latency hint)

| model | input | GPU median ms | GPU FPS | CPU median ms | CPU FPS | GPU compile ms | contended |
|---|---|---|---|---|---|---|---|
| rfdetrsegmedium_fp16 | 1,3,432,432 | 144.85 | 6.79 | 388.36 | 2.5 | 1120.56 | False |
| rfdetrsegnano_fp16 | 1,3,312,312 | 80.66 | 11.85 | 216.97 | 4.48 | 1435.78 | False |
| rfdetrsegnano_int8 | 1,3,312,312 | 118.0 | 8.28 | 107.18 | 8.79 | 3538.25 | False |
| rfdetrsegsmall_fp16 | 1,3,384,384 | 138.35 | 6.98 | 300.67 | 3.15 | 1526.31 | False |
| rfdetrsegsmall_int8 | 1,3,384,384 | 173.9 | 5.7 | 145.33 | 6.78 | 5923.86 | False |
| yolo11n-seg_fp16 | 1,3,640,640 | 15.04 | 58.82 | 42.85 | 22.49 | 446.76 | False |
| yolo11n-seg_int8 | 1,3,640,640 | 11.59 | 73.46 | 18.23 | 50.25 | 731.99 | False |
| yolo11s-seg_fp16 | 1,3,640,640 | 30.73 | 30.87 | 127.9 | 7.71 | 2711.10 | False |
| yolo11s-seg_int8 | 1,3,640,640 | 25.79 | 37.5 | 44.89 | 21.56 | 3091.99 | False |
| yolo26n-seg_fp16 | 1,3,640,640 | 17.89 | 55.12 | 40.57 | 23.78 | 717.58 | False |
| yolo26n-seg_int8 | 1,3,640,640 | 14.0 | 61.72 | 18.23 | 48.47 | 5844.32 | False |
| yolo26s-seg_fp16 | 1,3,640,640 | 39.49 | 24.17 | 133.62 | 7.4 | 749.05 | False |
| yolo26s-seg_int8 | 1,3,640,640 | 28.5 | 34.62 | 47.12 | 20.48 | 5251.85 | False |

## Daemon loop (640x360 frame in, masks out, conf 0.25)

| model | p50 ms | p95 ms | p99 ms | FPS | CPU % (1 core=100) | RSS MB | GPU MHz | contended |
|---|---|---|---|---|---|---|---|---|
| rfdetrsegmedium_fp16 | 147.3 | 160.1 | 165.3 | 6.8 | 99.7 | 267 | 1300.0 | False |
| rfdetrsegnano_fp16 | 72.9 | 81.7 | 91.1 | 13.4 | 99.8 | 246 | 1300.0 | False |
| rfdetrsegnano_int8 (CPU) | 94.6 | 102.9 | 107.9 | 10.5 | 381.5 | 385 | 0.0 | False |
| rfdetrsegnano_int8 | 103.9 | 113.9 | 119.7 | 9.6 | 99.7 | 265 | 1300.0 | False |
| rfdetrsegsmall_fp16 | 115.6 | 127.8 | 164.3 | 8.5 | 99.7 | 242 | 1300.0 | False |
| rfdetrsegsmall_int8 | 156.5 | 168.0 | 171.9 | 6.4 | 99.7 | 267 | 1300.0 | False |
| yolo11n-seg_fp16 | 21.7 | 34.9 | 40.9 | 42.7 | 99.5 | 263 | 1200.0 | False |
| yolo11n-seg_int8 (CPU) | 25.0 | 38.3 | 45.7 | 37.1 | 299.7 | 252 | 0.0 | False |
| yolo11n-seg_int8 | 20.4 | 30.4 | 34.6 | 46.7 | 99.1 | 282 | 900.0 | False |
| yolo11s-seg_fp16 | 38.9 | 50.8 | 64.3 | 24.4 | 99.5 | 266 | 1300.0 | False |
| yolo11s-seg_int8 | 28.1 | 38.3 | 44.5 | 33.8 | 99.8 | 283 | 1300.0 | False |
| yolo26n-seg_fp16 | 22.2 | 34.2 | 38.6 | 41.9 | 99.6 | 268 | 1200.0 | False |
| yolo26n-seg_int8 (CPU) | 25.4 | 36.4 | 42.2 | 37.7 | 299.0 | 259 | 0.0 | False |
| yolo26n-seg_int8 | 20.7 | 29.7 | 36.3 | 46.1 | 99.5 | 291 | 1100.0 | False |
| yolo26s-seg_fp16 | 40.5 | 52.5 | 61.6 | 23.6 | 99.4 | 269 | 1300.0 | False |
| yolo26s-seg_int8 | 30.7 | 39.5 | 44.8 | 31.1 | 99.3 | 286 | 1175.0 | False |

## COCO val2017 person accuracy (2693 person images + 500 person-free)

Instance "hidden" = ≥90% of its pixels under the blur region. Region = dilated mask (~1% of long side).

### threshold 0.25

| model | mask AP | AP small | AP large | hidden small | hidden medium | hidden large | pixel recall | over-blur | false alarm on person-free imgs |
|---|---|---|---|---|---|---|---|---|---|
| rfdetrsegmedium_fp16 | 0.489 | 0.205 | 0.769 | 75.4 | 93.3 | 94.9 | 97.4 | 14.4 | 4.6 |
| rfdetrsegnano_fp16 | 0.429 | 0.119 | 0.759 | 61.4 | 90.6 | 94.5 | 97.0 | 14.2 | 4.2 |
| rfdetrsegsmall_fp16 | 0.469 | 0.173 | 0.765 | 70.2 | 92.5 | 94.9 | 97.3 | 14.3 | 5.6 |
| yolo11n-seg_fp16 | 0.398 | 0.149 | 0.662 | 43.5 | 79.8 | 86.6 | 92.6 | 15.6 | 2.8 |
| yolo11n-seg_int8 | 0.397 | 0.147 | 0.664 | 41.9 | 79.5 | 86.6 | 92.8 | 15.7 | 2.8 |
| yolo11s-seg_fp16 | 0.446 | 0.198 | 0.695 | 55.7 | 85.1 | 89.5 | 94.4 | 15.2 | 2.4 |
| yolo11s-seg_int8 | 0.444 | 0.196 | 0.695 | 54.5 | 84.8 | 90.2 | 94.6 | 15.3 | 3.0 |
| yolo26n-seg_fp16 | 0.416 | 0.162 | 0.677 | 42.9 | 78.8 | 88.0 | 93.0 | 15.2 | 2.6 |
| yolo26n-seg_int8 | 0.407 | 0.156 | 0.666 | 42.3 | 77.9 | 86.5 | 92.5 | 15.6 | 2.6 |
| yolo26s-seg_fp16 | 0.469 | 0.221 | 0.711 | 57.9 | 85.7 | 89.9 | 94.8 | 14.8 | 3.8 |
| yolo26s-seg_int8 | 0.458 | 0.217 | 0.697 | 56.5 | 85.2 | 88.1 | 94.0 | 15.2 | 3.6 |

### threshold 0.1

| model | mask AP | AP small | AP large | hidden small | hidden medium | hidden large | pixel recall | over-blur | false alarm on person-free imgs |
|---|---|---|---|---|---|---|---|---|---|
| rfdetrsegmedium_fp16 | 0.489 | 0.205 | 0.769 | 88.4 | 96.8 | 96.2 | 98.1 | 19.2 | 18.0 |
| rfdetrsegnano_fp16 | 0.429 | 0.119 | 0.759 | 69.1 | 94.6 | 96.1 | 97.8 | 18.9 | 19.4 |
| rfdetrsegsmall_fp16 | 0.469 | 0.173 | 0.765 | 80.3 | 95.9 | 96.1 | 98.0 | 18.8 | 17.6 |
| yolo11n-seg_fp16 | 0.398 | 0.149 | 0.662 | 65.0 | 87.3 | 89.7 | 94.7 | 17.8 | 6.0 |
| yolo11n-seg_int8 | 0.397 | 0.147 | 0.664 | 63.6 | 87.1 | 89.3 | 94.7 | 18.0 | 5.6 |
| yolo11s-seg_fp16 | 0.446 | 0.198 | 0.695 | 73.9 | 90.8 | 91.2 | 95.6 | 16.8 | 5.8 |
| yolo11s-seg_int8 | 0.444 | 0.196 | 0.695 | 73.0 | 90.7 | 91.7 | 95.8 | 17.0 | 5.2 |
| yolo26n-seg_fp16 | 0.416 | 0.162 | 0.677 | 63.8 | 87.3 | 90.4 | 95.0 | 17.4 | 6.0 |
| yolo26n-seg_int8 | 0.407 | 0.156 | 0.666 | 62.9 | 86.7 | 89.0 | 94.7 | 17.8 | 6.0 |
| yolo26s-seg_fp16 | 0.469 | 0.221 | 0.711 | 75.6 | 91.2 | 91.1 | 95.9 | 16.5 | 7.0 |
| yolo26s-seg_int8 | 0.458 | 0.217 | 0.697 | 74.4 | 90.9 | 89.8 | 95.3 | 17.3 | 8.6 |

### render mode comparison at threshold 0.25 (hidden %, small/medium/large, pixel recall, over-blur)

| model | raw mask | dilated mask | boxes |
|---|---|---|---|
| rfdetrsegmedium_fp16 | 28.2/71.7/86.3, px 94.4, over 8.3 | 75.4/93.3/94.9, px 97.4, over 14.4 | 72.7/96.5/98.5, px 99.0, over 43.8 |
| rfdetrsegnano_fp16 | 18.0/63.5/85.3, px 93.8, over 8.4 | 61.4/90.6/94.5, px 97.0, over 14.2 | 66.3/95.0/98.2, px 98.7, over 43.5 |
| rfdetrsegsmall_fp16 | 24.7/69.4/86.0, px 94.2, over 8.2 | 70.2/92.5/94.9, px 97.3, over 14.3 | 70.6/95.9/98.5, px 98.9, over 43.6 |
| yolo11n-seg_fp16 | 31.4/63.4/74.9, px 89.5, over 9.4 | 43.5/79.8/86.6, px 92.6, over 15.6 | 45.8/86.1/95.0, px 96.2, over 43.8 |
| yolo11n-seg_int8 | 30.1/63.0/75.1, px 89.5, over 9.6 | 41.9/79.5/86.6, px 92.8, over 15.7 | 44.5/86.1/95.1, px 96.3, over 44.1 |
| yolo11s-seg_fp16 | 43.1/70.4/78.6, px 91.3, over 8.8 | 55.7/85.1/89.5, px 94.4, over 15.2 | 57.2/91.2/96.6, px 97.5, over 43.5 |
| yolo11s-seg_int8 | 42.1/70.5/78.8, px 91.6, over 9.0 | 54.5/84.8/90.2, px 94.6, over 15.3 | 56.4/90.8/96.8, px 97.6, over 43.6 |
| yolo26n-seg_fp16 | 30.6/61.1/75.4, px 89.8, over 9.1 | 42.9/78.8/88.0, px 93.0, over 15.2 | 46.0/86.4/95.4, px 96.4, over 43.7 |
| yolo26n-seg_int8 | 30.5/60.1/74.4, px 89.3, over 9.5 | 42.3/77.9/86.5, px 92.5, over 15.6 | 45.8/86.1/95.3, px 96.2, over 44.6 |
| yolo26s-seg_fp16 | 44.5/69.8/79.1, px 91.7, over 8.4 | 57.9/85.7/89.9, px 94.8, over 14.8 | 59.2/91.1/97.1, px 97.8, over 43.8 |
| yolo26s-seg_int8 | 43.5/69.2/76.4, px 90.7, over 8.8 | 56.5/85.2/88.1, px 94.0, over 15.2 | 58.3/91.1/96.8, px 97.1, over 44.1 |

## Synthetic 1920x1080 feed window (6 COCO photos as tiles), threshold 0.25, dilated mask

| model | pass | hidden small | hidden medium | hidden large | pixel recall | over-blur | e2e ms (python, unoptimized) |
|---|---|---|---|---|---|---|---|
| rfdetrsegnano_fp16 | full | 16.4 (n=914) | 53.0 | 89.1 | 91.2 | 32.2 | 141.7 |
| rfdetrsegnano_fp16 | tiled2x2 | 56.3 (n=914) | 89.3 | 97.2 | 97.9 | 32.2 | 355.3 |
| rfdetrsegsmall_fp16 | full | 21.9 (n=914) | 62.8 | 92.3 | 93.8 | 32.1 | 181.1 |
| rfdetrsegsmall_fp16 | tiled2x2 | 68.8 (n=914) | 91.8 | 97.3 | 98.2 | 32.1 | 517.0 |
| yolo11n-seg_fp16 | full | 17.8 (n=914) | 54.3 | 86.0 | 89.1 | 33.2 | 151.3 |
| yolo11n-seg_fp16 | tiled2x2 | 35.2 (n=914) | 76.1 | 93.5 | 93.6 | 31.4 | 182.8 |
| yolo11s-seg_fp16 | full | 25.9 (n=914) | 67.3 | 91.8 | 93.5 | 31.7 | 135.5 |
| yolo11s-seg_fp16 | tiled2x2 | 48.0 (n=914) | 83.3 | 94.5 | 95.5 | 31.5 | 216.0 |
| yolo26n-seg_fp16 | full | 18.1 (n=914) | 54.2 | 86.1 | 87.6 | 32.7 | 165.8 |
| yolo26n-seg_fp16 | tiled2x2 | 35.6 (n=914) | 75.7 | 93.2 | 94.5 | 31.4 | 213.3 |

## Compositor-side GPU cost (headless EGL, Mesa iris)

| step | p50 ms | p95 ms | max ms |
|---|---|---|---|
| downscale_plus_sync_readback_ms | 3.00 | 3.90 | 12.03 |
| downscale_plus_pbo_async_readback_ms | 2.56 | 2.86 | 7.77 |
| mask_upload_plus_pixelate_pass_1080p_ms | 3.63 | 3.96 | 13.16 |

contended: False
