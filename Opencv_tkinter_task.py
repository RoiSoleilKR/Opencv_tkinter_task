import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import os


IMG_W = 360
IMG_H = 300

im1 = None
im2 = None

def load_img():
    global im1
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
    if not file_path:
        return
    im1 = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    show_image(im1, label2) # 처음엔 원본을 결과창에도 일단 띄워둠
    show_image(im1, label1)

def save_img():
    if im2 is None:
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG 파일", "*.png"), ("JPG 파일", "*.jpg")]
    )
    if file_path:
        ext = os.path.splitext(file_path)[1]          # ".png" 또는 ".jpg"
        cv2.imencode(ext, im2)[1].tofile(file_path)   # 한글 경로에서도 저장됨

def show_image(img, target_label):
    h, w = img.shape[:2]
    # 가로/세로 중 더 많이 넘치는 쪽에 맞춰 비율 계산 (1보다 크면 확대하지 않고 그대로 둠)
    scale = min(IMG_W / w, IMG_H / h, 1)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    im_tk = ImageTk.PhotoImage(Image.fromarray(img[:, :, ::-1]))
    target_label.config(image=im_tk)
    target_label.image = im_tk

# 확대/축소 전용 표시 함수: 원본(base)이 화면에 보이는 비율을 기준으로 보여줌
def show_image_zoom(img, base, target_label):
    bh, bw = base.shape[:2]
    s0 = min(IMG_W / bw, IMG_H / bh, 1)   # 원본이 화면에 보이는 비율

    h, w = img.shape[:2]
    if s0 < 1:
        img = cv2.resize(img, (max(1, int(w * s0)), max(1, int(h * s0))), interpolation=cv2.INTER_AREA)

    # 틀보다 크면 가운데 부분만 잘라서 보여줌
    dh, dw = img.shape[:2]
    if dw > IMG_W:
        x = (dw - IMG_W) // 2
        img = img[:, x:x + IMG_W]
    if dh > IMG_H:
        y = (dh - IMG_H) // 2
        img = img[y:y + IMG_H, :]

    im_tk = ImageTk.PhotoImage(Image.fromarray(img[:, :, ::-1]))
    target_label.config(image=im_tk)
    target_label.image = im_tk

# 기존 하단 슬라이더 프레임 초기화용 함수
def clear_control_frame():
    for widget in control_frame.winfo_children():
        widget.destroy()
    control_frame.config(text=" 조절 패널 ")

# 슬라이더 한 줄(이름 + 슬라이더)을 만들어주는 도우미 함수
def make_slider(text, from_, to, init, resolution=1, parent=None, label_width=14):
    if parent is None:
        parent = control_frame
    frame = tk.Frame(parent)
    frame.pack(side="top", fill="x", pady=1)
    tk.Label(frame, text=text, width=label_width).pack(side="left", padx=5)
    s = tk.Scale(frame, from_=from_, to=to, resolution=resolution, orient="horizontal")
    s.set(init)
    s.pack(side="left", fill="x", expand=True, padx=5)
    return s

# 변환 후 이미지가 잘리지 않도록 결과 크기를 자동 계산해서 warpAffine을 수행
def warp_affine_fit(img, M):
    h, w = img.shape[:2]
    corners = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    new_pts = corners @ M[:, :2].T + M[:, 2]    # 네 모서리가 이동한 위치
    min_x, min_y = new_pts.min(axis=0)
    max_x, max_y = new_pts.max(axis=0)

    M = M.copy()
    M[0, 2] -= min_x    # 화면 밖(음수)으로 나간 만큼 되돌리기
    M[1, 2] -= min_y
    new_w = max(1, int(np.ceil(max_x - min_x)))
    new_h = max(1, int(np.ceil(max_y - min_y)))
    return cv2.warpAffine(img, M, (new_w, new_h))

# --- [1] 화소단위처리: 밝기 & 대비 조절 기능 ---
def open_brightness_contrast_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 화소 단위 처리 (밝기 & 대비 조절) ")

    def apply_bc(val=None):
        global im1, im2
        b_val = b_slider.get()
        c_val = c_slider.get()
        im2 = cv2.convertScaleAbs(im1, alpha=c_val, beta=b_val)
        show_image(im2, label2)

    # 밝기 슬라이더
    tk.Label(control_frame, text="밝기").pack(side="left", padx=5)
    b_slider = tk.Scale(control_frame, from_=-100, to=100, orient="horizontal", command=apply_bc)
    b_slider.set(0)
    b_slider.pack(side="left", fill="x", expand=True, padx=5)

    # 대비 슬라이더
    tk.Label(control_frame, text="대비").pack(side="left", padx=5)
    c_slider = tk.Scale(control_frame, from_=0.1, to=3.0, resolution=0.1, orient="horizontal", command=apply_bc)
    c_slider.set(1.0)
    c_slider.pack(side="left", fill="x", expand=True, padx=5)
    
    # 최초 실행 시 적용
    apply_bc()

# --- [2] 영역처리: 블러링 기능 (알고리즘 선택 라디오버튼 + 강도 조절 슬라이더) ---
def open_blur_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 영역 처리 (블러링 알고리즘 & 강도 조절) ")

    # 선택된 블러 알고리즘을 저장하는 변수 (기본값: 'blur')
    blur_type = tk.StringVar(value="blur")

    def apply_blur(val=None):
        global im1, im2
        k_size = blur_slider.get()
        # 커널 사이즈는 홀수여야 함 (medianBlur, blur 등에서 에러 방지)
        if k_size % 2 == 0:
            k_size += 1
            
        selected_type = blur_type.get()
        
        # 선택된 알고리즘에 따른 OpenCV 연산 분기
        if selected_type == "blur":
            im2 = cv2.blur(im1, (k_size, k_size))
        elif selected_type == "GaussianBlur":
            im2 = cv2.GaussianBlur(im1, (k_size, k_size), 0)
        elif selected_type == "boxFilter":
            # boxFilter는 -1을 쓰면 원본과 같은 깊이(depth)로 적용됨
            im2 = cv2.boxFilter(im1, -1, (k_size, k_size))
        elif selected_type == "medianBlur":
            # medianBlur는 커널 크기가 1이면 에러가 나므로 최소 3 이상 홀수 보장
            if k_size < 3:
                k_size = 3
            im2 = cv2.medianBlur(im1, k_size)
            
        show_image(im2, label2)

    # 1. 알고리즘 선택용 라디오버튼 프레임
    radio_frame = tk.Frame(control_frame)
    radio_frame.pack(side="top", fill="x", pady=2)

    algorithms = [
        ("기본 블러 (blur)", "blur"),
        ("가우시안 (GaussianBlur)", "GaussianBlur"),
        ("박스 필터 (boxFilter)", "boxFilter"),
        ("메디안 (medianBlur)", "medianBlur")
    ]

    for text, mode in algorithms:
        rb = tk.Radiobutton(radio_frame, text=text, variable=blur_type, value=mode, command=apply_blur)
        rb.pack(side="left", padx=5)

    # 2. 강도 조절 슬라이더 프레임
    slider_frame = tk.Frame(control_frame)
    slider_frame.pack(side="top", fill="x", pady=2)

    tk.Label(slider_frame, text="커널 크기").pack(side="left", padx=5)
    blur_slider = tk.Scale(slider_frame, from_=1, to=31, resolution=2, orient="horizontal", command=apply_blur)
    blur_slider.set(9)
    blur_slider.pack(side="left", fill="x", expand=True, padx=5)

    # 최초 실행 시 적용
    apply_blur()

# --- [3] 영역처리: 샤프닝 기능 (알고리즘 선택 라디오버튼 포함) ---
def open_sharp_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 영역 처리 (샤프닝 알고리즘 선택) ")

    # 선택된 샤프닝 알고리즘을 저장하는 변수 (기본값: 'basic')
    sharp_type = tk.StringVar(value="basic")

    def apply_sharp(val=None):
        global im1, im2
        selected_type = sharp_type.get()
        
        if selected_type == "basic":
            # 기본 샤프닝 커널
            ker = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            im2 = cv2.filter2D(im1, -1, ker)
            
        elif selected_type == "strong":
            # 고강도 샤프닝 커널 (강한 샤프닝)
            ker = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            im2 = cv2.filter2D(im1, -1, ker)
            
        elif selected_type == "laplacian":
            # 라플라시안 필터 (경계선 검출 - 깔끔한 흑백 출력)
            gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            lap_abs = cv2.convertScaleAbs(lap)
            # 2차원 흑백 이미지를 3채널(BGR)로 변환하여 Index 에러 방지
            im2 = cv2.cvtColor(lap_abs, cv2.COLOR_GRAY2BGR)
            
        elif selected_type == "unsharp":
            # 언샤프 마스킹 (Gaussian Blur를 이용한 방식)
            blurred = cv2.GaussianBlur(im1, (9, 9), 2.0)
            im2 = cv2.addWeighted(im1, 1.5, blurred, -0.5, 0)
            
        show_image(im2, label2)

    # 알고리즘 선택용 라디오버튼 프레임
    radio_frame = tk.Frame(control_frame)
    radio_frame.pack(side="top", fill="x", pady=5)

    algorithms = [
        ("기본 샤프닝", "basic"),
        ("고강도 샤프닝", "strong"),
        ("라플라시안", "laplacian"),
        ("언샤프 마스킹", "unsharp")
    ]

    for text, mode in algorithms:
        rb = tk.Radiobutton(radio_frame, text=text, variable=sharp_type, value=mode, command=apply_sharp)
        rb.pack(side="left", padx=5)

    # 최초 실행 시 적용
    apply_sharp()

# --- [4] 화소처리: 히스토그램 평활화 (그레이스케일 변환 후 적용) ---
def open_hist_eq_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 화소 처리 (히스토그램 평활화 - Grayscale) ")

    # 그레이스케일 변환 후 히스토그램 평활화 수행
    gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
    eq_gray = cv2.equalizeHist(gray)

    # show_image(3채널 인덱싱) 및 저장 호환을 위해 3채널로 변환
    im2 = cv2.cvtColor(eq_gray, cv2.COLOR_GRAY2BGR)
    show_image(im2, label2)

    tk.Label(control_frame, text="그레이스케일 변환 후 히스토그램 평활화가 적용되었습니다.").pack(padx=5, pady=5)


# --- [5] 영역처리: 엣지 검출 (Canny / Sobel / Laplacian 선택 + 그레이스케일 기반) ---
def open_edge_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 영역 처리 (엣지 검출 - Grayscale) ")

    # 선택된 엣지 검출 알고리즘 저장 변수 (기본값: 'canny')
    edge_type = tk.StringVar(value="canny")

    # 그레이스케일 변환
    gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)

    def apply_edge(val=None):
        global im2
        selected = edge_type.get()

        if selected == "canny":
            t1 = low_slider.get()
            t2 = high_slider.get()
            # 낮은 임계값이 높은 임계값보다 커지지 않도록 보정
            if t1 > t2:
                t1, t2 = t2, t1
            edges = cv2.Canny(gray, t1, t2)

        elif selected == "sobel":
            # Sobel 커널 크기는 1, 3, 5, 7 등 홀수 사용
            ksize = ksize_slider.get()
            if ksize % 2 == 0:
                ksize += 1
            ksize = max(1, min(ksize, 7))
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
            abs_x = cv2.convertScaleAbs(sobel_x)
            abs_y = cv2.convertScaleAbs(sobel_y)
            edges = cv2.addWeighted(abs_x, 0.5, abs_y, 0.5, 0)

        elif selected == "laplacian":
            # Laplacian 커널 크기도 홀수(1, 3, 5, 7 등) 사용
            ksize = ksize_slider.get()
            if ksize % 2 == 0:
                ksize += 1
            ksize = max(1, min(ksize, 7))
            lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=ksize)
            edges = cv2.convertScaleAbs(lap)

        # show_image(3채널 인덱싱) 및 저장 호환을 위해 3채널로 변환
        im2 = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        show_image(im2, label2)

    # 1. 알고리즘 선택 라디오버튼 프레임
    radio_frame = tk.Frame(control_frame)
    radio_frame.pack(side="top", fill="x", pady=2)

    methods = [
        ("Canny", "canny"),
        ("Sobel", "sobel"),
        ("Laplacian", "laplacian"),
    ]

    for text, mode in methods:
        rb = tk.Radiobutton(
            radio_frame,
            text=text,
            variable=edge_type,
            value=mode,
            command=apply_edge,
        )
        rb.pack(side="left", padx=5)

    # 2. Canny용 임계값 슬라이더
    slider1_frame = tk.Frame(control_frame)
    slider1_frame.pack(side="top", fill="x", pady=2)
    tk.Label(slider1_frame, text="Canny 임계값 1 (Low)").pack(side="left", padx=5)
    low_slider = tk.Scale(
        slider1_frame, from_=0, to=255, orient="horizontal", command=apply_edge
    )
    low_slider.set(50)
    low_slider.pack(side="left", fill="x", expand=True, padx=5)

    slider2_frame = tk.Frame(control_frame)
    slider2_frame.pack(side="top", fill="x", pady=2)
    tk.Label(slider2_frame, text="Canny 임계값 2 (High)").pack(side="left", padx=5)
    high_slider = tk.Scale(
        slider2_frame, from_=0, to=255, orient="horizontal", command=apply_edge
    )
    high_slider.set(150)
    high_slider.pack(side="left", fill="x", expand=True, padx=5)

    # 3. Sobel / Laplacian용 커널 크기 슬라이더 (1~7 홀수)
    ksize_frame = tk.Frame(control_frame)
    ksize_frame.pack(side="top", fill="x", pady=2)
    tk.Label(ksize_frame, text="Sobel/Laplacian 커널 크기").pack(side="left", padx=5)
    ksize_slider = tk.Scale(
        ksize_frame, from_=1, to=7, resolution=2, orient="horizontal", command=apply_edge
    )
    ksize_slider.set(3)
    ksize_slider.pack(side="left", fill="x", expand=True, padx=5)

    # 최초 실행 시 적용
    apply_edge()

# --- [6] 화소처리: 그레이스케일 / 반전 / 이진화 ---
def open_pixel_convert_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 화소 처리 (그레이스케일 / 반전 / 이진화) ")

    # 선택된 변환 방식을 저장하는 변수 (기본값: 'gray')
    mode = tk.StringVar(value="gray")

    def apply_convert(val=None):
        global im2
        selected = mode.get()

        if selected == "gray":
            gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
            im2 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)   # 화면 출력용 3채널 변환

        elif selected == "invert":
            im2 = 255 - im1    # 모든 화소를 255에서 빼면 색이 반전됨

        elif selected == "binary":
            gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
            # 기준값(slider)보다 밝으면 255(흰색), 아니면 0(검정)
            _, bin_img = cv2.threshold(gray, th_slider.get(), 255, cv2.THRESH_BINARY)
            im2 = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2BGR)

        show_image(im2, label2)

    # 1. 변환 방식 선택 라디오버튼
    radio_frame = tk.Frame(control_frame)
    radio_frame.pack(side="top", fill="x", pady=2)

    options = [
        ("그레이스케일", "gray"),
        ("색 반전", "invert"),
        ("이진화", "binary"),
    ]
    for text, value in options:
        rb = tk.Radiobutton(radio_frame, text=text, variable=mode, value=value, command=apply_convert)
        rb.pack(side="left", padx=5)

    # 2. 이진화 기준값 슬라이더
    slider_frame = tk.Frame(control_frame)
    slider_frame.pack(side="top", fill="x", pady=2)
    tk.Label(slider_frame, text="이진화 기준값").pack(side="left", padx=5)
    th_slider = tk.Scale(slider_frame, from_=0, to=255, orient="horizontal", command=apply_convert)
    th_slider.set(127)
    th_slider.pack(side="left", fill="x", expand=True, padx=5)

    # 최초 실행 시 적용
    apply_convert()

# --- [7] 기하학적 처리: 확대/축소 & 보간법 선택 ---
def open_resize_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 기하학적 처리 (확대/축소 & 보간법) ")

    # 선택된 보간법을 저장하는 변수 (기본값: 'linear')
    interp_type = tk.StringVar(value="linear")

    def apply_resize(val=None):
        global im2
        scale = scale_slider.get()

        # 보간법 이름 -> OpenCV 상수 연결표
        interp_table = {
            "nearest": cv2.INTER_NEAREST,
            "linear": cv2.INTER_LINEAR,
            "cubic": cv2.INTER_CUBIC,
            "area": cv2.INTER_AREA,
        }
        interp = interp_table[interp_type.get()]

        # fx, fy: 가로/세로 배율
        im2 = cv2.resize(im1, None, fx=scale, fy=scale, interpolation=interp)
        show_image_zoom(im2, im1, label2)

        h, w = im2.shape[:2]
        info_label.config(text=f"결과 이미지 크기: {w} x {h}  (화면에는 틀에 들어오는 부분만 표시)")

    # 1. 보간법 선택 라디오버튼
    radio_frame = tk.Frame(control_frame)
    radio_frame.pack(side="top", fill="x", pady=2)

    options = [
        ("최근접 (nearest)", "nearest"),
        ("양선형 (linear)", "linear"),
        ("양3차 (cubic)", "cubic"),
        ("영역 (area)", "area"),
    ]
    for text, value in options:
        rb = tk.Radiobutton(radio_frame, text=text, variable=interp_type, value=value, command=apply_resize)
        rb.pack(side="left", padx=5)

    # 2. 결과 크기를 알려주는 안내 라벨 (슬라이더보다 먼저 만들어야 함!)
    info_label = tk.Label(control_frame, text="")
    info_label.pack(side="bottom", pady=2)

    # 3. 배율 슬라이더
    slider_frame = tk.Frame(control_frame)
    slider_frame.pack(side="top", fill="x", pady=2)
    tk.Label(slider_frame, text="배율").pack(side="left", padx=5)
    scale_slider = tk.Scale(slider_frame, from_=0.1, to=2.0, resolution=0.1, orient="horizontal", command=apply_resize)
    scale_slider.set(1.0)
    scale_slider.pack(side="left", fill="x", expand=True, padx=5)

    # 최초 실행 시 적용
    apply_resize()

# --- [8] 기하학적 처리: 회전(3가지 방식) & 평행이동 ---
def open_rotate_move_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 기하학적 처리 (회전 & 평행이동) ")

    # 선택된 회전 방식을 저장하는 변수 (기본값: 'matrix2d')
    rotate_type = tk.StringVar(value="matrix2d")

    def apply_rotate_move(val=None):
        global im2
        angle = angle_slider.get()
        mode = rotate_type.get()
        h, w = im1.shape[:2]

        if mode == "rotate":
            # cv2.rotate는 90도 단위만 가능 → 슬라이더 값을 가장 가까운 90의 배수로 맞춤
            k = int(round(angle / 90)) % 4   # 0, 1, 2, 3 (반시계 방향으로 90도 몇 번?)
            codes = {
                1: cv2.ROTATE_90_COUNTERCLOCKWISE,
                2: cv2.ROTATE_180,
                3: cv2.ROTATE_90_CLOCKWISE,
            }
            rotated = im1 if k == 0 else cv2.rotate(im1, codes[k])
            rh, rw = rotated.shape[:2]   # 90/270도면 가로세로가 바뀜

            # cv2.rotate에는 이동 기능이 없어서, 이동만 하는 행렬로 따로 처리
            M = np.float32([[1, 0, rw * tx_slider.get() / 100],
                            [0, 1, rh * ty_slider.get() / 100]])
            im2 = cv2.warpAffine(rotated, M, (rw, rh))
            info_label.config(text=f"적용된 각도: {k * 90}° (90° 단위로만 회전)")

        else:
            tx = w * tx_slider.get() / 100
            ty = h * ty_slider.get() / 100

            if mode == "manual":
                # 회전 행렬을 직접 계산 (중심 cx, cy 기준)
                theta = np.deg2rad(angle)
                c, s = np.cos(theta), np.sin(theta)
                cx, cy = w / 2, h / 2
                M = np.array([[ c, s, (1 - c) * cx - s * cy],
                              [-s, c, s * cx + (1 - c) * cy]], dtype=np.float32)
            else:
                # OpenCV가 위와 똑같은 행렬을 만들어 줌
                M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)

            # 이동량을 행렬의 마지막 열에 더하기
            M[0, 2] += tx
            M[1, 2] += ty
            im2 = cv2.warpAffine(im1, M, (w, h))
            info_label.config(text=f"적용된 각도: {angle}°")

        show_image(im2, label2)

    # 1. 회전 방식 선택 라디오버튼
    radio_frame = tk.Frame(control_frame)
    radio_frame.pack(side="top", fill="x", pady=2)
    tk.Label(radio_frame, text="회전 방식:").pack(side="left", padx=5)

    options = [
        ("cv2.rotate() (고정 각도)", "rotate"),
        ("cv2.warpAffine() (행렬 직접 계산)", "manual"),
        ("getRotationMatrix2D()", "matrix2d"),
    ]
    for text, value in options:
        rb = tk.Radiobutton(radio_frame, text=text, variable=rotate_type, value=value, command=apply_rotate_move)
        rb.pack(side="left", padx=5)

    # 2. 안내 라벨 (슬라이더 command 연결 전에 만들어 두기)
    info_label = tk.Label(control_frame, text="")
    info_label.pack(side="bottom", pady=2)

    angle_slider = make_slider("회전 각도 (°)", -180, 180, 0)
    tx_slider = make_slider("가로 이동 (%)", -100, 100, 0)
    ty_slider = make_slider("세로 이동 (%)", -100, 100, 0)

    # 슬라이더를 다 만든 '후에' 조작 시 실행될 함수를 연결
    for s in (angle_slider, tx_slider, ty_slider):
        s.config(command=apply_rotate_move)

    # 초기화 버튼: 모든 슬라이더를 0으로
    def reset():
        for s in (angle_slider, tx_slider, ty_slider):
            s.set(0)

    tk.Button(control_frame, text="초기화", command=reset).pack(side="bottom", pady=2)

    # 최초 실행 시 적용
    apply_rotate_move()

# --- [9] 기하학적 처리: 전단 (Shear) ---
def open_shear_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 기하학적 처리 (전단) ")

    def apply_shear(val=None):
        global im2
        sx = sx_slider.get()
        sy = sy_slider.get()
        h, w = im1.shape[:2]

        # 전단 행렬: 왼쪽 2x2가 모양 변화, 마지막 열은 이동(일단 0)
        M = np.float32([[1, sx, 0],
                        [sy, 1, 0]])

        # 변환 후 네 모서리가 어디로 가는지 계산해서, 이미지가 잘리지 않도록 결과 크기를 정함
        corners = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        new_pts = corners @ M[:, :2].T
        min_x, min_y = new_pts.min(axis=0)
        max_x, max_y = new_pts.max(axis=0)

        # 음수 좌표로 밀려난 만큼 이동시켜서 전체가 화면 안에 들어오게 함
        M[0, 2] = -min_x
        M[1, 2] = -min_y
        new_w = int(np.ceil(max_x - min_x))
        new_h = int(np.ceil(max_y - min_y))

        im2 = cv2.warpAffine(im1, M, (new_w, new_h))
        info_label.config(text=f"결과 이미지 크기: {new_w} x {new_h}")
        show_image(im2, label2)

    # 안내 라벨 (슬라이더 command 연결 전에 만들어 두기)
    info_label = tk.Label(control_frame, text="")
    info_label.pack(side="bottom", pady=2)

    sx_slider = make_slider("가로 전단 (sx)", -0.5, 0.5, 0, 0.05)
    sy_slider = make_slider("세로 전단 (sy)", -0.5, 0.5, 0, 0.05)

    # 슬라이더를 다 만든 '후에' 조작 시 실행될 함수를 연결
    for s in (sx_slider, sy_slider):
        s.config(command=apply_shear)

    def reset():
        for s in (sx_slider, sy_slider):
            s.set(0)

    tk.Button(control_frame, text="초기화", command=reset).pack(side="bottom", pady=2)

    # 최초 실행 시 적용
    apply_shear()

# --- [10] 기하학적 처리: 어파인 변환 (3점 이동) ---
def open_affine_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 기하학적 처리 (어파인 변환: 세 점 이동) ")

    def apply_affine(val=None):
        global im2
        h, w = im1.shape[:2]

        # 원본의 세 점: 좌상단, 우상단, 좌하단
        src = np.float32([[0, 0], [w, 0], [0, h]])
        # 각 점을 슬라이더 값(%)만큼 옮긴 목적지
        dst = np.float32([
            [0 + w * x1.get() / 100, 0 + h * y1.get() / 100],
            [w + w * x2.get() / 100, 0 + h * y2.get() / 100],
            [0 + w * x3.get() / 100, h + h * y3.get() / 100],
        ])

        # 세 점의 이동 정보로부터 2x3 변환 행렬을 계산
        M = cv2.getAffineTransform(src, dst)
        im2 = warp_affine_fit(im1, M)

        rh, rw = im2.shape[:2]
        info_label.config(text=f"결과 이미지 크기: {rw} x {rh}")
        show_image(im2, label2)

    # 안내 라벨 (슬라이더 command 연결 전에 만들어 두기)
    info_label = tk.Label(control_frame, text="")
    info_label.pack(side="bottom", pady=2)

    # 점 3개를 가로로 나란히 배치 (점마다 x, y 슬라이더)
    point_frame = tk.Frame(control_frame)
    point_frame.pack(side="top", fill="x")

    sliders = []
    for name in ["좌상단 점", "우상단 점", "좌하단 점"]:
        box = tk.LabelFrame(point_frame, text=name)
        box.pack(side="left", fill="x", expand=True, padx=3)
        sliders.append(make_slider("x (%)", -30, 30, 0, parent=box, label_width=6))
        sliders.append(make_slider("y (%)", -30, 30, 0, parent=box, label_width=6))
    x1, y1, x2, y2, x3, y3 = sliders

    # 슬라이더를 다 만든 '후에' 조작 시 실행될 함수를 연결
    for s in sliders:
        s.config(command=apply_affine)

    def reset():
        for s in sliders:
            s.set(0)

    tk.Button(control_frame, text="초기화", command=reset).pack(side="bottom", pady=2)

    # 최초 실행 시 적용
    apply_affine()

# --- [11] 기하학적 처리: 원근 투시 변환 (4점 이동) ---
def open_perspective_menu():
    global im1, im2
    if im1 is None:
        return
    clear_control_frame()
    control_frame.config(text=" 기하학적 처리 (원근 투시 변환: 네 점 이동) ")

    def apply_perspective(val=None):
        global im2
        h, w = im1.shape[:2]

        # 원본의 네 점: 좌상단, 우상단, 우하단, 좌하단
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        # 각 점을 슬라이더 값(%)만큼 옮긴 목적지
        dst = np.float32([
            [0 + w * x1.get() / 100, 0 + h * y1.get() / 100],
            [w + w * x2.get() / 100, 0 + h * y2.get() / 100],
            [w + w * x3.get() / 100, h + h * y3.get() / 100],
            [0 + w * x4.get() / 100, h + h * y4.get() / 100],
        ])

        # 음수 좌표가 없도록 전체를 이동시키고, 결과 크기를 자동으로 계산 (안 잘리게)
        dst = dst - dst.min(axis=0)
        new_w = max(1, int(np.ceil(dst[:, 0].max())))
        new_h = max(1, int(np.ceil(dst[:, 1].max())))

        # 네 점의 이동 정보로부터 3x3 변환 행렬을 계산하고 적용
        H = cv2.getPerspectiveTransform(src, dst)
        im2 = cv2.warpPerspective(im1, H, (new_w, new_h))

        info_label.config(text=f"결과 이미지 크기: {new_w} x {new_h}")
        show_image(im2, label2)

    # 안내 라벨 (슬라이더 command 연결 전에 만들어 두기)
    info_label = tk.Label(control_frame, text="")
    info_label.pack(side="bottom", pady=2)

    # 점 4개를 가로로 나란히 배치 (점마다 x, y 슬라이더)
    point_frame = tk.Frame(control_frame)
    point_frame.pack(side="top", fill="x")

    sliders = []
    for name in ["좌상단 점", "우상단 점", "우하단 점", "좌하단 점"]:
        box = tk.LabelFrame(point_frame, text=name)
        box.pack(side="left", fill="x", expand=True, padx=3)
        sliders.append(make_slider("x (%)", -30, 30, 0, parent=box, label_width=6))
        sliders.append(make_slider("y (%)", -30, 30, 0, parent=box, label_width=6))
    x1, y1, x2, y2, x3, y3, x4, y4 = sliders

    # 슬라이더를 다 만든 '후에' 조작 시 실행될 함수를 연결
    for s in sliders:
        s.config(command=apply_perspective)

    def reset():
        for s in sliders:
            s.set(0)

    tk.Button(control_frame, text="초기화", command=reset).pack(side="bottom", pady=2)

    # 최초 실행 시 적용
    apply_perspective()

def exit_app():
    root.destroy()

root = tk.Tk()
root.title('202610069_김홍용_tkinter')
root.geometry('800x700')

menubar = tk.Menu(root)
root.config(menu=menubar)

# 파일 메뉴
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='파일', menu=file_menu)
file_menu.add_command(label='열기', command=load_img)
file_menu.add_command(label='저장', command=save_img)
file_menu.add_separator()
file_menu.add_command(label='종료', command=exit_app)

# 화소처리 메뉴
pixel_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='화소처리', menu=pixel_menu)
pixel_menu.add_command(label='밝기 및 대비 조절', command=open_brightness_contrast_menu)
pixel_menu.add_command(label='히스토그램 평활화', command=open_hist_eq_menu)
pixel_menu.add_command(label='그레이스케일/반전/이진화', command=open_pixel_convert_menu)

# 영역처리 메뉴
region_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='영역처리', menu=region_menu)
region_menu.add_command(label='블러링', command=open_blur_menu)
region_menu.add_command(label='샤프닝', command=open_sharp_menu)
region_menu.add_command(label='엣지 검출', command=open_edge_menu)

# 기하학처리 메뉴
geo_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='기하학처리', menu=geo_menu)
geo_menu.add_command(label='확대/축소 & 보간법', command=open_resize_menu)
geo_menu.add_command(label='회전 & 평행이동', command=open_rotate_move_menu)
geo_menu.add_command(label='전단', command=open_shear_menu)
geo_menu.add_command(label='어파인 변환', command=open_affine_menu)
geo_menu.add_command(label='원근 투시 변환', command=open_perspective_menu)


# 이미지 출력용 프레임
image_frame = tk.Frame(root)
image_frame.pack(pady=10)

frame1 = tk.Frame(image_frame, width=IMG_W, height=IMG_H, bg="lightgray")
frame1.pack(side='left', padx=10)
frame1.pack_propagate(False)   # 안에 든 내용 크기에 맞춰 틀이 변하지 않게 고정
label1 = tk.Label(frame1, text="원본 이미지", bg="lightgray")
label1.pack(fill="both", expand=True)

frame2 = tk.Frame(image_frame, width=IMG_W, height=IMG_H, bg="lightgray")
frame2.pack(side='right', padx=10)
frame2.pack_propagate(False)
label2 = tk.Label(frame2, text="결과 이미지", bg="lightgray")
label2.pack(fill="both", expand=True)

# 하단 동적 조절 패널 (기능에 따라 슬라이더가 바뀜)
control_frame = tk.LabelFrame(root, text=" 조절 패널 ", height=400)
control_frame.pack(fill="x", padx=20, pady=10, ipady=5)
control_frame.pack_propagate(False)

root.mainloop()