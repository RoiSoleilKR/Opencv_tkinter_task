import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np

im1 = None
im2 = None

def load_img():
    global im1
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
    if not file_path:
        return
    im1 = cv2.imread(file_path)
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
        cv2.imwrite(file_path, im2)

def show_image(img, target_label):
    im_tk = ImageTk.PhotoImage(Image.fromarray(img[:, :, ::-1]))
    target_label.config(image=im_tk)
    target_label.image = im_tk

# 기존 하단 슬라이더 프레임 초기화용 함수
def clear_control_frame():
    for widget in control_frame.winfo_children():
        widget.destroy()
    control_frame.config(text=" 조절 패널 ")

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

def exit_app():
    root.destroy()

root = tk.Tk()
root.title('202610069_김홍용_tkinter')
root.geometry('750x550')

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

# 영역처리 메뉴
region_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='영역처리', menu=region_menu)
region_menu.add_command(label='블러링', command=open_blur_menu)
region_menu.add_command(label='샤프닝', command=open_sharp_menu)
region_menu.add_command(label='엣지 검출', command=open_edge_menu)

# 이미지 출력용 프레임
image_frame = tk.Frame(root)
image_frame.pack(pady=10)

label1 = tk.Label(image_frame, text="원본 이미지", bg="lightgray", width=320, height=240)
label1.pack(side='left', padx=10)

label2 = tk.Label(image_frame, text="결과 이미지", bg="lightgray", width=320, height=240)
label2.pack(side='right', padx=10)

# 하단 동적 조절 패널 (기능에 따라 슬라이더가 바뀜)
control_frame = tk.LabelFrame(root, text=" 조절 패널 ")
control_frame.pack(fill="x", padx=20, pady=10, ipady=5)

root.mainloop()