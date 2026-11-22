# 이미지 처리 프로그램 (Image Processing Program)



## 프로젝트 소개



본 프로젝트는 Python의 Tkinter GUI 라이브러리와 OpenCV 라이브러리를 활용하여 제작한 이미지 처리 프로그램입니다.



사용자는 이미지 파일을 불러온 후 밝기 및 대비 조절, 히스토그램 평활화, 블러링, 샤프닝, 엣지 검출 등의 기능을 적용할 수 있으며, 처리 결과를 확인하고 저장할 수 있습니다.







## 개발 환경



\- Python 3.12

\- Tkinter

\- OpenCV (cv2)

\- Pillow (PIL)

\- NumPy







## 사용 라이브러리 설치



프로그램 실행 전 필요한 라이브러리를 설치합니다.



```bash

pip install opencv-python pillow numpy

```







## 실행 방법



```bash

Opencv_tkinter_task.py

```



※ 파일명은 본인이 사용하는 Python 파일명으로 변경할 수 있습니다.







## 프로그램 기능



### 1. 파일 기능



#### 열기



\- PNG, JPG, JPEG, BMP 형식의 이미지 불러오기



#### 저장



\- 처리된 결과 이미지를 저장



#### 종료



\- 프로그램 종료







### 2. 화소 처리(Pixel Processing)



#### 밝기 및 대비 조절



\- 밝기(Brightness) 조절

\- 대비(Contrast) 조절

\- 슬라이더를 이용하여 실시간 적용



#### 히스토그램 평활화



\- 이미지를 그레이스케일로 변환

\- 히스토그램 평활화를 통해 명암 대비 향상







### 3. 영역 처리(Spatial Processing)



#### 블러링(Blurring)



블러 강도를 조절할 수 있으며 다음 알고리즘을 제공합니다.



\- Blur

\- Gaussian Blur

\- Box Filter

\- Median Blur







#### 샤프닝(Sharpening)



이미지의 경계를 강조하여 선명도를 향상시킵니다.



제공 알고리즘:



\- 기본 샤프닝

\- 고강도 샤프닝

\- Laplacian

\- Unsharp Masking







#### 엣지 검출(Edge Detection)



이미지의 경계선을 검출합니다.



제공 알고리즘:



\- Canny

\- Sobel

\- Laplacian



조절 가능 항목:



\- Canny Threshold

\- Sobel/Laplacian Kernel Size







## 프로그램 구조



### 주요 함수



| 함수 | 설명 |

|--------|--------|

| load\_img() | 이미지 불러오기 |

| save\_img() | 이미지 저장 |

| show\_image() | 이미지 화면 출력 |

| open\_brightness\_contrast\_menu() | 밝기 및 대비 조절 |

| open\_blur\_menu() | 블러링 처리 |

| open\_sharp\_menu() | 샤프닝 처리 |

| open\_hist\_eq\_menu() | 히스토그램 평활화 |

| open\_edge\_menu() | 엣지 검출 |

| clear\_control\_frame() | 조절 패널 초기화 |

| exit\_app() | 프로그램 종료 |







## 프로그램 화면 구성



### 메뉴바



\- 파일

\- 화소처리

\- 영역처리



### 이미지 출력 영역



\- 원본 이미지

\- 결과 이미지



### 조절 패널



선택한 기능에 따라 슬라이더 및 옵션이 동적으로 변경됩니다.







\## 구현 기능 예시



### 화소 처리



\- 밝기 조절

\- 대비 조절

\- 히스토그램 평활화



### 영역 처리



\- 블러링

\- 샤프닝

\- 엣지 검출







## 프로젝트 특징



\- Tkinter 기반 GUI 환경 제공

\- OpenCV 기반 이미지 처리

\- 실시간 슬라이더 조작 지원

\- 다양한 블러링 알고리즘 제공

\- 다양한 샤프닝 알고리즘 제공

\- 다양한 엣지 검출 알고리즘 제공

\- 결과 이미지 저장 기능 제공







## 프로젝트 목적



본 프로젝트는 Python GUI 프로그래밍과 OpenCV 기반 영상 처리 기법을 학습하기 위해 제작되었습니다.



화소 단위 처리와 영역 기반 처리 기법을 직접 구현하고 다양한 영상 처리 알고리즘의 동작을 이해하는 것을 목표로 하였습니다.







## 제작자



\- 학번: 202610069

\- 이름: 김홍용
\- Github: https://github.com/RoiSoleilKR/Opencv_tkinter_task
