"""
NeuralAgent视觉模块 - 支持三种视觉技术路线的统一框架
NeuralAgent Vision Module - Unified framework supporting three visual technology approaches
"""

import asyncio
import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import base64
from io import BytesIO
import cv2
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import easyocr

from agno.agents.base_agent import BaseAgent
from agno.memory.memory_manager import MemoryManager


class VisionApproach(Enum):
    """视觉技术路线"""
    PURE_VISION = "pure_vision"  # 纯视觉解析
    OCR_ENHANCED = "ocr_enhanced"  # OCR增强
    MULTIMODAL_FUSION = "multimodal_fusion"  # 多模态融合


class VisionTask(Enum):
    """视觉任务类型"""
    UI_ELEMENT_DETECTION = "ui_element_detection"
    COLOR_ANALYSIS = "color_analysis"
    CONTOUR_DETECTION = "contour_detection"
    TEXT_RECOGNITION = "text_recognition"
    LAYOUT_ANALYSIS = "layout_analysis"
    INTERACTION_PREDICTION = "interaction_prediction"
    VISUAL_QA = "visual_qa"


class ElementType(Enum):
    """UI元素类型"""
    BUTTON = "button"
    TEXT_INPUT = "text_input"
    IMAGE = "image"
    LABEL = "label"
    CONTAINER = "container"
    MENU = "menu"
    TAB = "tab"
    FORM = "form"
    TABLE = "table"
    LINK = "link"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    DROPDOWN = "dropdown"
    SLIDER = "slider"
    PROGRESS_BAR = "progress_bar"
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """边界框"""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class UIElement:
    """UI元素"""
    id: str
    element_type: ElementType
    bounding_box: BoundingBox
    text_content: Optional[str] = None
    attributes: Dict[str, Any] = None
    confidence: float = 0.0
    visual_features: Dict[str, Any] = None
    interaction_properties: Dict[str, Any] = None
    parent_element: Optional[str] = None
    child_elements: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.visual_features is None:
            self.visual_features = {}
        if self.interaction_properties is None:
            self.interaction_properties = {}
        if self.child_elements is None:
            self.child_elements = []
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ColorInfo:
    """颜色信息"""
    dominant_colors: List[Tuple[int, int, int]]  # RGB
    color_names: List[str]
    color_percentages: List[float]
    palette: List[str]
    contrast_ratio: float = 0.0
    brightness: float = 0.0
    saturation: float = 0.0


@dataclass
class ContourInfo:
    """轮廓信息"""
    contours: List[np.ndarray]
    bounding_boxes: List[BoundingBox]
    areas: List[float]
    perimeters: List[float]
    circularity: List[float]
    aspect_ratios: List[float]
    hierarchy: Optional[np.ndarray] = None


@dataclass
class VisionAnalysisResult:
    """视觉分析结果"""
    task_id: str
    approach: VisionApproach
    task_type: VisionTask
    timestamp: datetime
    image_info: Dict[str, Any]
    ui_elements: List[UIElement] = None
    color_analysis: ColorInfo = None
    contour_analysis: ContourInfo = None
    text_regions: List[Dict[str, Any]] = None
    layout_structure: Dict[str, Any] = None
    interaction_suggestions: List[Dict[str, Any]] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.ui_elements is None:
            self.ui_elements = []
        if self.text_regions is None:
            self.text_regions = []
        if self.metadata is None:
            self.metadata = {}


class PureVisionAnalyzer:
    """纯视觉解析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 预训练的UI检测模型配置
        self.ui_detection_config = {
            "model_path": config.get("ui_model_path", "models/ui_detection.pth"),
            "confidence_threshold": config.get("confidence_threshold", 0.7),
            "nms_threshold": config.get("nms_threshold", 0.4)
        }
        
        # 颜色分析配置
        self.color_config = {
            "k_clusters": config.get("color_clusters", 8),
            "color_space": config.get("color_space", "RGB"),
            "dominant_color_count": config.get("dominant_colors", 5)
        }
    
    async def analyze_image(self, image: np.ndarray, task_type: VisionTask) -> Dict[str, Any]:
        """分析图像"""
        try:
            start_time = datetime.now()
            
            result = {
                "approach": VisionApproach.PURE_VISION,
                "task_type": task_type,
                "timestamp": start_time,
                "image_shape": image.shape,
                "ui_elements": [],
                "color_analysis": None,
                "contour_analysis": None,
                "processing_details": {}
            }
            
            if task_type == VisionTask.UI_ELEMENT_DETECTION:
                result["ui_elements"] = await self._detect_ui_elements(image)
                result["processing_details"]["detection_method"] = "deep_learning"
                
            elif task_type == VisionTask.COLOR_ANALYSIS:
                result["color_analysis"] = await self._analyze_colors(image)
                result["processing_details"]["analysis_method"] = "k_means_clustering"
                
            elif task_type == VisionTask.CONTOUR_DETECTION:
                result["contour_analysis"] = await self._detect_contours(image)
                result["processing_details"]["detection_method"] = "opencv_contours"
                
            elif task_type == VisionTask.LAYOUT_ANALYSIS:
                result["layout_structure"] = await self._analyze_layout(image)
                result["processing_details"]["analysis_method"] = "geometric_analysis"
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time"] = processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"纯视觉分析失败: {str(e)}")
            raise
    
    async def _detect_ui_elements(self, image: np.ndarray) -> List[UIElement]:
        """检测UI元素"""
        elements = []
        
        # 模拟UI元素检测
        # 实际实现中会使用预训练的深度学习模型
        
        # 检测按钮
        button_regions = await self._detect_button_regions(image)
        for region in button_regions:
            element = UIElement(
                id=str(uuid.uuid4()),
                element_type=ElementType.BUTTON,
                bounding_box=region,
                confidence=0.85,
                attributes={"shape": "rectangular", "has_text": True}
            )
            elements.append(element)
        
        # 检测文本输入框
        input_regions = await self._detect_input_regions(image)
        for region in input_regions:
            element = UIElement(
                id=str(uuid.uuid4()),
                element_type=ElementType.TEXT_INPUT,
                bounding_box=region,
                confidence=0.78,
                attributes={"input_type": "text", "placeholder": "detected"}
            )
            elements.append(element)
        
        # 检测图片元素
        image_regions = await self._detect_image_regions(image)
        for region in image_regions:
            element = UIElement(
                id=str(uuid.uuid4()),
                element_type=ElementType.IMAGE,
                bounding_box=region,
                confidence=0.92,
                attributes={"format": "detected", "is_clickable": False}
            )
            elements.append(element)
        
        return elements
    
    async def _detect_button_regions(self, image: np.ndarray) -> List[BoundingBox]:
        """检测按钮区域"""
        # 使用边缘检测和轮廓分析
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        button_regions = []
        for contour in contours:
            # 计算边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 过滤条件：大小和长宽比
            if 50 < w < 300 and 20 < h < 100 and 0.5 < w/h < 5:
                button_regions.append(BoundingBox(x, y, w, h, 0.85))
        
        return button_regions
    
    async def _detect_input_regions(self, image: np.ndarray) -> List[BoundingBox]:
        """检测输入框区域"""
        # 检测矩形边框
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用霍夫变换检测直线
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
        input_regions = []
        if lines is not None:
            # 组合线条形成矩形
            # 简化实现：查找水平线对
            horizontal_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(y2 - y1) < 5:  # 近似水平线
                    horizontal_lines.append((min(x1, x2), max(x1, x2), y1))
            
            # 配对形成输入框
            for i in range(len(horizontal_lines)):
                for j in range(i + 1, len(horizontal_lines)):
                    line1 = horizontal_lines[i]
                    line2 = horizontal_lines[j]
                    
                    y1, y2 = line1[2], line2[2]
                    x_start = min(line1[0], line1[1], line2[0], line2[1])
                    x_end = max(line1[0], line1[1], line2[0], line2[1])
                    
                    height = abs(y2 - y1)
                    width = x_end - x_start
                    
                    if 20 < height < 50 and 50 < width < 400:
                        input_regions.append(BoundingBox(x_start, min(y1, y2), width, height, 0.78))
        
        return input_regions
    
    async def _detect_image_regions(self, image: np.ndarray) -> List[BoundingBox]:
        """检测图片区域"""
        # 检测具有均匀纹理的区域
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用纹理分析
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 如果图像整体纹理较少，可能是图片区域
        if laplacian_var < 100:
            # 查找大的均匀区域
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            image_regions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # 最小面积阈值
                    x, y, w, h = cv2.boundingRect(contour)
                    if w > 50 and h > 50:
                        image_regions.append(BoundingBox(x, y, w, h, 0.92))
            
            return image_regions
        
        return []
    
    async def _analyze_colors(self, image: np.ndarray) -> ColorInfo:
        """分析颜色"""
        # 重塑图像数据
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        # K-means聚类
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, self.color_config["k_clusters"], None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 计算颜色分布
        labels = labels.flatten()
        percentages = []
        for i in range(self.color_config["k_clusters"]):
            percentage = (labels == i).sum() / len(labels) * 100
            percentages.append(percentage)
        
        # 获取主要颜色
        dominant_indices = np.argsort(percentages)[::-1][:self.color_config["dominant_color_count"]]
        dominant_colors = [centers[i].astype(int).tolist() for i in dominant_indices]
        
        # 颜色命名（简化实现）
        color_names = await self._name_colors(dominant_colors)
        
        # 计算其他颜色指标
        brightness = np.mean(cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 2])
        saturation = np.mean(cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1])
        
        return ColorInfo(
            dominant_colors=dominant_colors,
            color_names=color_names,
            color_percentages=percentages[:self.color_config["dominant_color_count"]],
            palette=color_names,
            brightness=brightness / 255.0,
            saturation=saturation / 255.0
        )
    
    async def _name_colors(self, colors: List[List[int]]) -> List[str]:
        """颜色命名"""
        color_names = []
        
        for color in colors:
            r, g, b = color
            
            # 简化的颜色命名逻辑
            if r > 200 and g > 200 and b > 200:
                color_names.append("白色")
            elif r < 50 and g < 50 and b < 50:
                color_names.append("黑色")
            elif r > g and r > b:
                if g > 100:
                    color_names.append("黄色")
                else:
                    color_names.append("红色")
            elif g > r and g > b:
                if r > 100:
                    color_names.append("黄绿色")
                else:
                    color_names.append("绿色")
            elif b > r and b > g:
                color_names.append("蓝色")
            elif r > 150 and g > 150 and b < 100:
                color_names.append("橙色")
            elif r > 150 and g < 100 and b > 150:
                color_names.append("紫色")
            else:
                color_names.append("灰色")
        
        return color_names
    
    async def _detect_contours(self, image: np.ndarray) -> ContourInfo:
        """检测轮廓"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 应用高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 边缘检测
        edges = cv2.Canny(blurred, 50, 150)
        
        # 查找轮廓
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # 分析轮廓特征
        bounding_boxes = []
        areas = []
        perimeters = []
        circularity = []
        aspect_ratios = []
        
        for contour in contours:
            # 边界框
            x, y, w, h = cv2.boundingRect(contour)
            bounding_boxes.append(BoundingBox(x, y, w, h))
            
            # 面积
            area = cv2.contourArea(contour)
            areas.append(area)
            
            # 周长
            perimeter = cv2.arcLength(contour, True)
            perimeters.append(perimeter)
            
            # 圆形度
            if perimeter > 0:
                circ = 4 * np.pi * area / (perimeter * perimeter)
                circularity.append(circ)
            else:
                circularity.append(0)
            
            # 长宽比
            aspect_ratios.append(w / h if h > 0 else 0)
        
        return ContourInfo(
            contours=contours,
            bounding_boxes=bounding_boxes,
            areas=areas,
            perimeters=perimeters,
            circularity=circularity,
            aspect_ratios=aspect_ratios,
            hierarchy=hierarchy
        )
    
    async def _analyze_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """分析布局结构"""
        # 分析图像的布局特征
        height, width = image.shape[:2]
        
        # 检测网格结构
        grid_structure = await self._detect_grid_structure(image)
        
        # 检测对齐模式
        alignment_patterns = await self._detect_alignment_patterns(image)
        
        # 检测空白区域
        white_space_regions = await self._detect_white_space(image)
        
        return {
            "image_dimensions": {"width": width, "height": height},
            "grid_structure": grid_structure,
            "alignment_patterns": alignment_patterns,
            "white_space_regions": white_space_regions,
            "layout_complexity": len(grid_structure.get("grid_lines", [])),
            "dominant_direction": "horizontal"  # 简化实现
        }
    
    async def _detect_grid_structure(self, image: np.ndarray) -> Dict[str, Any]:
        """检测网格结构"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 霍夫变换检测直线
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        grid_lines = []
        if lines is not None:
            for line in lines:
                rho, theta = line[0]
                if abs(theta) < 0.1 or abs(theta - np.pi/2) < 0.1:  # 水平或垂直线
                    grid_lines.append({"rho": rho, "theta": theta})
        
        return {
            "grid_lines": grid_lines,
            "grid_columns": len([l for l in grid_lines if abs(l["theta"] - np.pi/2) < 0.1]),
            "grid_rows": len([l for l in grid_lines if abs(l["theta"]) < 0.1])
        }
    
    async def _detect_alignment_patterns(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """检测对齐模式"""
        # 简化实现：检测边缘对齐
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        alignment_patterns = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 检测左对齐
            if x < 50:
                alignment_patterns.append({
                    "type": "left_aligned",
                    "x": x,
                    "confidence": 0.8
                })
            
            # 检测居中对齐
            center_x = x + w // 2
            if abs(center_x - image.shape[1] // 2) < 50:
                alignment_patterns.append({
                    "type": "center_aligned",
                    "x": center_x,
                    "confidence": 0.7
                })
            
            # 检测右对齐
            if x + w > image.shape[1] - 50:
                alignment_patterns.append({
                    "type": "right_aligned",
                    "x": x + w,
                    "confidence": 0.8
                })
        
        return alignment_patterns
    
    async def _detect_white_space(self, image: np.ndarray) -> List[BoundingBox]:
        """检测空白区域"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 检测低纹理区域
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        low_texture_mask = laplacian.var() < 100
        
        # 查找连通区域
        contours, _ = cv2.findContours(low_texture_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        white_space_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 最小空白区域
                x, y, w, h = cv2.boundingRect(contour)
                white_space_regions.append(BoundingBox(x, y, w, h, 0.6))
        
        return white_space_regions


class OCREnhancedAnalyzer:
    """OCR增强解析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # OCR引擎配置
        self.ocr_engines = {
            "tesseract": pytesseract,
            "easyocr": easyocr.Reader(['en'])
        }
        
        # OCR配置
        self.ocr_config = {
            "languages": config.get("languages", ["eng"]),
            "psm": config.get("page_segmentation_mode", 6),  # 假设为统一文本块
            "oem": config.get("ocr_engine_mode", 3),  # 默认引擎
            "confidence_threshold": config.get("confidence_threshold", 60)
        }
    
    async def analyze_image(self, image: np.ndarray, task_type: VisionTask) -> Dict[str, Any]:
        """分析图像"""
        try:
            start_time = datetime.now()
            
            result = {
                "approach": VisionApproach.OCR_ENHANCED,
                "task_type": task_type,
                "timestamp": start_time,
                "image_shape": image.shape,
                "text_regions": [],
                "ui_elements": [],
                "processing_details": {}
            }
            
            if task_type == VisionTask.TEXT_RECOGNITION:
                result["text_regions"] = await self._extract_text_regions(image)
                result["processing_details"]["ocr_engine"] = "tesseract"
                
            elif task_type == VisionTask.UI_ELEMENT_DETECTION:
                result["ui_elements"] = await self._detect_ui_elements_with_ocr(image)
                result["processing_details"]["detection_method"] = "ocr_enhanced"
                
            elif task_type == VisionTask.LAYOUT_ANALYSIS:
                result["layout_structure"] = await self._analyze_text_layout(image)
                result["processing_details"]["analysis_method"] = "text_based_layout"
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time"] = processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"OCR增强分析失败: {str(e)}")
            raise
    
    async def _extract_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """提取文本区域"""
        text_regions = []
        
        # 使用Tesseract OCR
        try:
            # 预处理图像
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # OCR数据
            ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            # 解析OCR结果
            for i in range(len(ocr_data["text"])):
                text = ocr_data["text"][i].strip()
                confidence = int(ocr_data["conf"][i])
                
                if text and confidence > self.ocr_config["confidence_threshold"]:
                    x = ocr_data["left"][i]
                    y = ocr_data["top"][i]
                    w = ocr_data["width"][i]
                    h = ocr_data["height"][i]
                    
                    text_regions.append({
                        "text": text,
                        "confidence": confidence,
                        "bounding_box": {"x": x, "y": y, "width": w, "height": h},
                        "position": {"x": x + w // 2, "y": y + h // 2},
                        "font_size": h,
                        "ocr_engine": "tesseract"
                    })
            
        except Exception as e:
            self.logger.error(f"Tesseract OCR失败: {str(e)}")
        
        # 使用EasyOCR作为备选
        try:
            easyocr_results = self.ocr_engines["easyocr"].readtext(image)
            
            for (bbox, text, confidence) in easyocr_results:
                if confidence > self.ocr_config["confidence_threshold"] / 100:
                    # 转换边界框格式
                    x_min = int(min(point[0] for point in bbox))
                    y_min = int(min(point[1] for point in bbox))
                    x_max = int(max(point[0] for point in bbox))
                    y_max = int(max(point[1] for point in bbox))
                    
                    text_regions.append({
                        "text": text,
                        "confidence": confidence * 100,
                        "bounding_box": {"x": x_min, "y": y_min, "width": x_max - x_min, "height": y_max - y_min},
                        "position": {"x": (x_min + x_max) // 2, "y": (y_min + y_max) // 2},
                        "font_size": y_max - y_min,
                        "ocr_engine": "easyocr"
                    })
        
        except Exception as e:
            self.logger.error(f"EasyOCR失败: {str(e)}")
        
        return text_regions
    
    async def _detect_ui_elements_with_ocr(self, image: np.ndarray) -> List[UIElement]:
        """使用OCR检测UI元素"""
        elements = []
        
        # 提取文本区域
        text_regions = await self._extract_text_regions(image)
        
        # 基于文本内容推断UI元素类型
        for region in text_regions:
            text = region["text"].lower()
            bbox = region["bounding_box"]
            
            element_type = ElementType.UNKNOWN
            confidence = region["confidence"] / 100
            
            # 基于关键词推断元素类型
            if any(keyword in text for keyword in ["button", "click", "submit", "ok", "cancel", "save"]):
                element_type = ElementType.BUTTON
                confidence *= 0.9
            elif any(keyword in text for keyword in ["input", "enter", "search", "name", "email"]):
                element_type = ElementType.TEXT_INPUT
                confidence *= 0.8
            elif any(keyword in text for keyword in ["menu", "nav", "home", "about", "contact"]):
                element_type = ElementType.MENU
                confidence *= 0.7
            elif any(keyword in text for keyword in ["link", "www", "http", "https"]):
                element_type = ElementType.LINK
                confidence *= 0.8
            elif any(keyword in text for keyword in ["checkbox", "check"]):
                element_type = ElementType.CHECKBOX
                confidence *= 0.75
            elif any(keyword in text for keyword in ["radio", "option", "choice"]):
                element_type = ElementType.RADIO_BUTTON
                confidence *= 0.75
            
            # 创建UI元素
            if element_type != ElementType.UNKNOWN:
                bounding_box = BoundingBox(
                    bbox["x"], bbox["y"], bbox["width"], bbox["height"], confidence
                )
                
                element = UIElement(
                    id=str(uuid.uuid4()),
                    element_type=element_type,
                    bounding_box=bounding_box,
                    text_content=region["text"],
                    confidence=confidence,
                    attributes={
                        "detected_by": "ocr",
                        "ocr_confidence": region["confidence"],
                        "font_size": region["font_size"]
                    }
                )
                
                elements.append(element)
        
        return elements
    
    async def _analyze_text_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """分析文本布局"""
        text_regions = await self._extract_text_regions(image)
        
        if not text_regions:
            return {"layout_type": "no_text", "text_regions": []}
        
        # 分析文本排列
        text_positions = [(region["position"]["x"], region["position"]["y"]) for region in text_regions]
        
        # 检测文本对齐
        alignment_analysis = await self._analyze_text_alignment(text_positions)
        
        # 检测文本层次
        hierarchy_analysis = await self._analyze_text_hierarchy(text_regions)
        
        # 检测文本流
        text_flow = await self._analyze_text_flow(text_regions)
        
        return {
            "layout_type": "text_based",
            "text_regions": text_regions,
            "alignment_analysis": alignment_analysis,
            "hierarchy_analysis": hierarchy_analysis,
            "text_flow": text_flow,
            "total_text_elements": len(text_regions),
            "dominant_font_size": max(region["font_size"] for region in text_regions) if text_regions else 0
        }
    
    async def _analyze_text_alignment(self, positions: List[Tuple[int, int]]) -> Dict[str, Any]:
        """分析文本对齐"""
        if len(positions) < 2:
            return {"alignment_type": "single_element"}
        
        x_positions = [pos[0] for pos in positions]
        y_positions = [pos[1] for pos in positions]
        
        # 检测左对齐
        left_aligned = len(set(x_positions[:min(3, len(x_positions))])) == 1
        
        # 检测居中对齐
        center_x = sum(x_positions) / len(x_positions)
        center_aligned = all(abs(x - center_x) < 50 for x in x_positions)
        
        # 检测右对齐
        right_aligned = len(set(x_positions[-min(3, len(x_positions)):])) == 1
        
        alignment_type = "mixed"
        if left_aligned:
            alignment_type = "left_aligned"
        elif center_aligned:
            alignment_type = "center_aligned"
        elif right_aligned:
            alignment_type = "right_aligned"
        
        return {
            "alignment_type": alignment_type,
            "left_aligned": left_aligned,
            "center_aligned": center_aligned,
            "right_aligned": right_aligned,
            "center_x": center_x
        }
    
    async def _analyze_text_hierarchy(self, text_regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析文本层次"""
        if not text_regions:
            return {"hierarchy_levels": 0}
        
        # 按字体大小分组
        font_sizes = [region["font_size"] for region in text_regions]
        min_size, max_size = min(font_sizes), max(font_sizes)
        
        # 定义层次级别
        if max_size - min_size < 10:
            hierarchy_levels = 1
        elif max_size - min_size < 20:
            hierarchy_levels = 2
        else:
            hierarchy_levels = 3
        
        # 分析标题和正文的分布
        title_regions = [region for region in text_regions if region["font_size"] > max_size * 0.8]
        body_regions = [region for region in text_regions if region["font_size"] <= max_size * 0.8]
        
        return {
            "hierarchy_levels": hierarchy_levels,
            "title_regions": len(title_regions),
            "body_regions": len(body_regions),
            "font_size_range": {"min": min_size, "max": max_size}
        }
    
    async def _analyze_text_flow(self, text_regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析文本流"""
        if len(text_regions) < 2:
            return {"flow_direction": "single_element"}
        
        # 按Y坐标排序（从上到下）
        sorted_regions = sorted(text_regions, key=lambda x: x["position"]["y"])
        
        # 分析阅读顺序
        flow_direction = "vertical"
        
        # 检查是否主要是水平流动
        y_differences = [abs(sorted_regions[i+1]["position"]["y"] - sorted_regions[i]["position"]["y"]) 
                        for i in range(len(sorted_regions)-1)]
        
        x_differences = [abs(sorted_regions[i+1]["position"]["x"] - sorted_regions[i]["position"]["x"]) 
                        for i in range(len(sorted_regions)-1)]
        
        avg_y_diff = sum(y_differences) / len(y_differences) if y_differences else 0
        avg_x_diff = sum(x_differences) / len(x_differences) if x_differences else 0
        
        if avg_x_diff > avg_y_diff * 1.5:
            flow_direction = "horizontal"
        
        return {
            "flow_direction": flow_direction,
            "reading_order": [region["text"] for region in sorted_regions],
            "avg_y_spacing": avg_y_diff,
            "avg_x_spacing": avg_x_diff
        }


class MultimodalFusionAnalyzer:
    """多模态融合解析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 融合策略配置
        self.fusion_config = {
            "weight_vision": config.get("vision_weight", 0.4),
            "weight_ocr": config.get("ocr_weight", 0.3),
            "weight_layout": config.get("layout_weight", 0.3),
            "confidence_threshold": config.get("confidence_threshold", 0.7)
        }
        
        # 子分析器
        self.pure_vision_analyzer = PureVisionAnalyzer(config)
        self.ocr_analyzer = OCREnhancedAnalyzer(config)
    
    async def analyze_image(self, image: np.ndarray, task_type: VisionTask) -> Dict[str, Any]:
        """分析图像"""
        try:
            start_time = datetime.now()
            
            # 并行执行多种分析方法
            vision_task = asyncio.create_task(
                self.pure_vision_analyzer.analyze_image(image, task_type)
            )
            ocr_task = asyncio.create_task(
                self.ocr_analyzer.analyze_image(image, task_type)
            )
            
            # 等待结果
            vision_result = await vision_task
            ocr_result = await ocr_task
            
            # 融合结果
            fused_result = await self._fuse_results(vision_result, ocr_result, task_type)
            
            # 添加融合元数据
            fused_result["approach"] = VisionApproach.MULTIMODAL_FUSION
            fused_result["fusion_strategy"] = "weighted_combination"
            fused_result["component_results"] = {
                "pure_vision": vision_result,
                "ocr_enhanced": ocr_result
            }
            
            processing_time = (datetime.now() - start_time).total_seconds()
            fused_result["processing_time"] = processing_time
            
            return fused_result
            
        except Exception as e:
            self.logger.error(f"多模态融合分析失败: {str(e)}")
            raise
    
    async def _fuse_results(self, vision_result: Dict[str, Any], ocr_result: Dict[str, Any], task_type: VisionTask) -> Dict[str, Any]:
        """融合分析结果"""
        fused_result = {
            "approach": VisionApproach.MULTIMODAL_FUSION,
            "task_type": task_type,
            "timestamp": datetime.now(),
            "fusion_metadata": {
                "fusion_method": "weighted_confidence_fusion",
                "weights": self.fusion_config
            }
        }
        
        if task_type == VisionTask.UI_ELEMENT_DETECTION:
            fused_result["ui_elements"] = await self._fuse_ui_elements(
                vision_result.get("ui_elements", []),
                ocr_result.get("ui_elements", [])
            )
            
        elif task_type == VisionTask.COLOR_ANALYSIS:
            fused_result["color_analysis"] = await self._fuse_color_analysis(
                vision_result.get("color_analysis"),
                ocr_result.get("color_analysis")
            )
            
        elif task_type == VisionTask.TEXT_RECOGNITION:
            fused_result["text_regions"] = await self._fuse_text_regions(
                vision_result.get("text_regions", []),
                ocr_result.get("text_regions", [])
            )
            
        elif task_type == VisionTask.LAYOUT_ANALYSIS:
            fused_result["layout_structure"] = await self._fuse_layout_analysis(
                vision_result.get("layout_structure", {}),
                ocr_result.get("layout_structure", {})
            )
        
        # 计算融合置信度
        fused_result["confidence_score"] = await self._calculate_fusion_confidence(
            vision_result, ocr_result
        )
        
        return fused_result
    
    async def _fuse_ui_elements(self, vision_elements: List[UIElement], ocr_elements: List[UIElement]) -> List[UIElement]:
        """融合UI元素检测结果"""
        fused_elements = []
        used_ocr_indices = set()
        
        # 首先添加纯视觉检测的元素
        for element in vision_elements:
            # 检查是否有重叠的OCR检测元素
            overlapping_ocr = []
            for i, ocr_element in enumerate(ocr_elements):
                if i in used_ocr_indices:
                    continue
                    
                if self._calculate_overlap(element.bounding_box, ocr_element.bounding_box) > 0.5:
                    overlapping_ocr.append((i, ocr_element))
                    used_ocr_indices.add(i)
            
            if overlapping_ocr:
                # 融合重叠元素
                best_ocr = max(overlapping_ocr, key=lambda x: x[1].confidence)[1]
                fused_element = await self._merge_ui_elements(element, best_ocr)
                fused_elements.append(fused_element)
            else:
                fused_elements.append(element)
        
        # 添加没有重叠的OCR元素
        for i, element in enumerate(ocr_elements):
            if i not in used_ocr_indices:
                fused_elements.append(element)
        
        return fused_elements
    
    async def _merge_ui_elements(self, vision_element: UIElement, ocr_element: UIElement) -> UIElement:
        """合并UI元素"""
        # 计算融合边界框
        v_bbox = vision_element.bounding_box
        o_bbox = ocr_element.bounding_box
        
        x = min(v_bbox.x, o_bbox.x)
        y = min(v_bbox.y, o_bbox.y)
        width = max(v_bbox.x + v_bbox.width, o_bbox.x + o_bbox.width) - x
        height = max(v_bbox.y + v_bbox.height, o_bbox.y + o_bbox.height) - y
        
        # 计算融合置信度
        fused_confidence = (
            v_bbox.confidence * self.fusion_config["weight_vision"] +
            o_bbox.confidence * self.fusion_config["weight_ocr"]
        )
        
        # 合并属性
        merged_attributes = {**vision_element.attributes, **ocr_element.attributes}
        merged_attributes["fusion_method"] = "vision_ocr_merge"
        merged_attributes["vision_confidence"] = v_bbox.confidence
        merged_attributes["ocr_confidence"] = o_bbox.confidence
        
        # 合并文本内容
        merged_text = ocr_element.text_content or vision_element.text_content
        
        return UIElement(
            id=str(uuid.uuid4()),
            element_type=vision_element.element_type,  # 优先使用视觉检测的类型
            bounding_box=BoundingBox(x, y, width, height, fused_confidence),
            text_content=merged_text,
            attributes=merged_attributes,
            confidence=fused_confidence
        )
    
    async def _fuse_color_analysis(self, vision_color: ColorInfo, ocr_color: ColorInfo) -> ColorInfo:
        """融合颜色分析结果"""
        if vision_color and ocr_color:
            # 融合主要颜色
            all_colors = vision_color.dominant_colors + ocr_color.dominant_colors
            all_percentages = vision_color.color_percentages + ocr_color.color_percentages
            
            # 重新计算百分比
            total_percentage = sum(all_percentages)
            if total_percentage > 0:
                normalized_percentages = [p / total_percentage * 100 for p in all_percentages]
            else:
                normalized_percentages = all_percentages
            
            return ColorInfo(
                dominant_colors=all_colors[:8],  # 限制颜色数量
                color_names=vision_color.color_names + ocr_color.color_names,
                color_percentages=normalized_percentages[:8],
                palette=vision_color.palette + ocr_color.palette,
                brightness=(vision_color.brightness + ocr_color.brightness) / 2,
                saturation=(vision_color.saturation + ocr_color.saturation) / 2
            )
        elif vision_color:
            return vision_color
        elif ocr_color:
            return ocr_color
        else:
            return None
    
    async def _fuse_text_regions(self, vision_texts: List[Dict[str, Any]], ocr_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """融合文本区域"""
        fused_texts = []
        used_ocr_indices = set()
        
        # 添加视觉检测的文本（如果有）
        for text_region in vision_texts:
            # 检查重叠的OCR文本
            overlapping_ocr = []
            for i, ocr_region in enumerate(ocr_texts):
                if i in used_ocr_indices:
                    continue
                    
                bbox1 = text_region["bounding_box"]
                bbox2 = ocr_region["bounding_box"]
                
                if self._calculate_overlap(bbox1, bbox2) > 0.3:
                    overlapping_ocr.append((i, ocr_region))
                    used_ocr_indices.add(i)
            
            if overlapping_ocr:
                # 选择置信度更高的文本
                best_ocr = max(overlapping_ocr, key=lambda x: x[1]["confidence"])[1]
                
                # 合并文本信息
                merged_region = {
                    "text": best_ocr["text"],  # 优先使用OCR文本
                    "confidence": (text_region.get("confidence", 0) * self.fusion_config["weight_vision"] + 
                                 best_ocr["confidence"] * self.fusion_config["weight_ocr"]),
                    "bounding_box": text_region["bounding_box"],  # 使用视觉边界框
                    "position": text_region["position"],
                    "font_size": text_region.get("font_size", best_ocr.get("font_size", 0)),
                    "detection_methods": ["vision", "ocr"],
                    "fusion_applied": True
                }
                fused_texts.append(merged_region)
            else:
                fused_texts.append(text_region)
        
        # 添加没有重叠的OCR文本
        for i, text_region in enumerate(ocr_texts):
            if i not in used_ocr_indices:
                text_region["detection_methods"] = ["ocr"]
                text_region["fusion_applied"] = False
                fused_texts.append(text_region)
        
        return fused_texts
    
    async def _fuse_layout_analysis(self, vision_layout: Dict[str, Any], ocr_layout: Dict[str, Any]) -> Dict[str, Any]:
        """融合布局分析结果"""
        fused_layout = {
            "layout_type": "multimodal_fusion",
            "fusion_method": "comprehensive_analysis"
        }
        
        # 融合布局特征
        if "grid_structure" in vision_layout and "grid_structure" in ocr_layout:
            fused_layout["grid_structure"] = {
                "vision_grid": vision_layout["grid_structure"],
                "ocr_grid": ocr_layout["grid_structure"],
                "fusion_strategy": "combined_grid_analysis"
            }
        
        if "alignment_patterns" in vision_layout and "alignment_patterns" in ocr_layout:
            all_patterns = vision_layout["alignment_patterns"] + ocr_layout["alignment_patterns"]
            fused_layout["alignment_patterns"] = all_patterns
        
        # 添加文本布局信息
        if "text_regions" in ocr_layout:
            fused_layout["text_layout"] = {
                "text_regions": ocr_layout["text_regions"],
                "text_hierarchy": ocr_layout.get("hierarchy_analysis", {}),
                "text_flow": ocr_layout.get("text_flow", {})
            }
        
        # 添加视觉布局信息
        if "white_space_regions" in vision_layout:
            fused_layout["visual_layout"] = {
                "white_space_regions": vision_layout["white_space_regions"],
                "layout_complexity": vision_layout.get("layout_complexity", 0)
            }
        
        return fused_layout
    
    async def _calculate_fusion_confidence(self, vision_result: Dict[str, Any], ocr_result: Dict[str, Any]) -> float:
        """计算融合置信度"""
        # 计算各组件的置信度
        vision_confidence = 0.0
        ocr_confidence = 0.0
        
        # 从UI元素计算置信度
        if "ui_elements" in vision_result and vision_result["ui_elements"]:
            vision_confidence = sum(elem.confidence for elem in vision_result["ui_elements"]) / len(vision_result["ui_elements"])
        
        if "ui_elements" in ocr_result and ocr_result["ui_elements"]:
            ocr_confidence = sum(elem.confidence for elem in ocr_result["ui_elements"]) / len(ocr_result["ui_elements"])
        
        # 从文本区域计算置信度
        if "text_regions" in vision_result and vision_result["text_regions"]:
            text_confidence = sum(region["confidence"] for region in vision_result["text_regions"]) / len(vision_result["text_regions"])
            vision_confidence = max(vision_confidence, text_confidence)
        
        if "text_regions" in ocr_result and ocr_result["text_regions"]:
            text_confidence = sum(region["confidence"] for region in ocr_result["text_regions"]) / len(ocr_result["text_regions"])
            ocr_confidence = max(ocr_confidence, text_confidence)
        
        # 加权融合置信度
        fused_confidence = (
            vision_confidence * self.fusion_config["weight_vision"] +
            ocr_confidence * self.fusion_config["weight_ocr"]
        )
        
        return fused_confidence
    
    def _calculate_overlap(self, bbox1: Union[BoundingBox, Dict], bbox2: Union[BoundingBox, Dict]) -> float:
        """计算两个边界框的重叠率"""
        # 转换为统一格式
        if isinstance(bbox1, dict):
            x1, y1, w1, h1 = bbox1["x"], bbox1["y"], bbox1["width"], bbox1["height"]
        else:
            x1, y1, w1, h1 = bbox1.x, bbox1.y, bbox1.width, bbox1.height
            
        if isinstance(bbox2, dict):
            x2, y2, w2, h2 = bbox2["x"], bbox2["y"], bbox2["width"], bbox2["height"]
        else:
            x2, y2, w2, h2 = bbox2.x, bbox2.y, bbox2.width, bbox2.height
        
        # 计算交集
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        union_area = w1 * h1 + w2 * h2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0


class NeuralAgentVisionModule(BaseAgent):
    """NeuralAgent视觉模块主类"""
    
    def __init__(self, 
                 agent_id: str,
                 name: str = "NeuralAgent Vision Module",
                 memory_manager: Optional[MemoryManager] = None,
                 config: Optional[Dict] = None):
        super().__init__(agent_id, name, memory_manager, config)
        
        # 视觉模块配置
        self.vision_config = config or {}
        
        # 初始化分析器
        self.analyzers = {
            VisionApproach.PURE_VISION: PureVisionAnalyzer(self.vision_config),
            VisionApproach.OCR_ENHANCED: OCREnhancedAnalyzer(self.vision_config),
            VisionApproach.MULTIMODAL_FUSION: MultimodalFusionAnalyzer(self.vision_config)
        }
        
        # 任务配置
        self.task_config = {
            "default_approach": VisionApproach.MULTIMODAL_FUSION,
            "timeout": 30,
            "max_retries": 3
        }
        
        # 结果缓存
        self.result_cache: Dict[str, VisionAnalysisResult] = {}
        self.cache_ttl = 300  # 5分钟
        
        self.logger = logging.getLogger(__name__)
    
    async def analyze_image(self, 
                          image_data: Union[str, np.ndarray, bytes],
                          task_type: VisionTask,
                          approach: Optional[VisionApproach] = None,
                          options: Dict[str, Any] = None) -> VisionAnalysisResult:
        """分析图像"""
        try:
            # 1. 预处理图像
            image = await self._preprocess_image(image_data)
            
            # 2. 选择分析方法
            if not approach:
                approach = self._select_approach(task_type, options)
            
            # 3. 检查缓存
            cache_key = self._generate_cache_key(image, task_type, approach)
            if cache_key in self.result_cache:
                cached_result = self.result_cache[cache_key]
                if (datetime.now() - cached_result.timestamp).total_seconds() < self.cache_ttl:
                    return cached_result
            
            # 4. 执行分析
            analyzer = self.analyzers[approach]
            raw_result = await analyzer.analyze_image(image, task_type)
            
            # 5. 构建标准化结果
            result = VisionAnalysisResult(
                task_id=str(uuid.uuid4()),
                approach=approach,
                task_type=task_type,
                timestamp=datetime.now(),
                image_info={
                    "shape": image.shape,
                    "dtype": str(image.dtype),
                    "size": image.nbytes
                },
                ui_elements=raw_result.get("ui_elements", []),
                color_analysis=raw_result.get("color_analysis"),
                contour_analysis=raw_result.get("contour_analysis"),
                text_regions=raw_result.get("text_regions", []),
                layout_structure=raw_result.get("layout_structure"),
                interaction_suggestions=raw_result.get("interaction_suggestions", []),
                confidence_score=raw_result.get("confidence_score", 0.0),
                processing_time=raw_result.get("processing_time", 0.0),
                metadata=raw_result.get("processing_details", {})
            )
            
            # 6. 缓存结果
            self.result_cache[cache_key] = result
            
            # 7. 保存到记忆
            await self.save_memory(f"vision_analysis_{result.task_id}", asdict(result))
            
            return result
            
        except Exception as e:
            self.logger.error(f"图像分析失败: {str(e)}")
            raise
    
    async def detect_ui_elements(self, 
                               image_data: Union[str, np.ndarray, bytes],
                               approach: Optional[VisionApproach] = None,
                               element_types: Optional[List[ElementType]] = None) -> List[UIElement]:
        """检测UI元素"""
        result = await self.analyze_image(
            image_data, 
            VisionTask.UI_ELEMENT_DETECTION, 
            approach
        )
        
        elements = result.ui_elements
        
        # 过滤指定类型的元素
        if element_types:
            elements = [elem for elem in elements if elem.element_type in element_types]
        
        return elements
    
    async def analyze_colors(self, 
                           image_data: Union[str, np.ndarray, bytes],
                           approach: Optional[VisionApproach] = None) -> ColorInfo:
        """分析颜色"""
        result = await self.analyze_image(
            image_data,
            VisionTask.COLOR_ANALYSIS,
            approach
        )
        
        return result.color_analysis
    
    async def detect_contours(self, 
                            image_data: Union[str, np.ndarray, bytes],
                            approach: Optional[VisionApproach] = None) -> ContourInfo:
        """检测轮廓"""
        result = await self.analyze_image(
            image_data,
            VisionTask.CONTOUR_DETECTION,
            approach
        )
        
        return result.contour_analysis
    
    async def recognize_text(self, 
                           image_data: Union[str, np.ndarray, bytes],
                           approach: Optional[VisionApproach] = None) -> List[Dict[str, Any]]:
        """识别文本"""
        result = await self.analyze_image(
            image_data,
            VisionTask.TEXT_RECOGNITION,
            approach
        )
        
        return result.text_regions
    
    async def analyze_layout(self, 
                           image_data: Union[str, np.ndarray, bytes],
                           approach: Optional[VisionApproach] = None) -> Dict[str, Any]:
        """分析布局"""
        result = await self.analyze_image(
            image_data,
            VisionTask.LAYOUT_ANALYSIS,
            approach
        )
        
        return result.layout_structure
    
    async def predict_interactions(self, 
                                 image_data: Union[str, np.ndarray, bytes],
                                 target_elements: Optional[List[UIElement]] = None) -> List[Dict[str, Any]]:
        """预测交互"""
        try:
            # 1. 检测UI元素
            if not target_elements:
                elements = await self.detect_ui_elements(image_data)
            else:
                elements = target_elements
            
            # 2. 分析交互可能性
            interaction_suggestions = []
            
            for element in elements:
                suggestion = await self._predict_element_interaction(element)
                if suggestion:
                    interaction_suggestions.append(suggestion)
            
            return interaction_suggestions
            
        except Exception as e:
            self.logger.error(f"交互预测失败: {str(e)}")
            return []
    
    async def batch_analyze(self, 
                          image_tasks: List[Dict[str, Any]],
                          max_concurrent: int = 3) -> List[VisionAnalysisResult]:
        """批量分析"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single_task(task):
            async with semaphore:
                return await self.analyze_image(
                    task["image_data"],
                    task["task_type"],
                    task.get("approach"),
                    task.get("options")
                )
        
        # 并行执行任务
        tasks = [analyze_single_task(task) for task in image_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"批量分析任务 {i} 失败: {result}")
                # 创建错误结果
                error_result = VisionAnalysisResult(
                    task_id=f"error_{i}",
                    approach=VisionApproach.PURE_VISION,
                    task_type=image_tasks[i]["task_type"],
                    timestamp=datetime.now(),
                    image_info={},
                    confidence_score=0.0,
                    metadata={"error": str(result)}
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    # 私有方法
    
    async def _preprocess_image(self, image_data: Union[str, np.ndarray, bytes]) -> np.ndarray:
        """预处理图像"""
        if isinstance(image_data, str):
            # 从文件路径加载
            if image_data.startswith("data:image"):
                # Base64编码的图像数据
                header, data = image_data.split(",", 1)
                image_data = base64.b64decode(data)
            
            image = Image.open(BytesIO(image_data))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
        elif isinstance(image_data, bytes):
            # 从字节数据加载
            image = Image.open(BytesIO(image_data))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
        elif isinstance(image_data, np.ndarray):
            # 直接使用numpy数组
            image = image_data
            
        else:
            raise ValueError(f"不支持的图像数据类型: {type(image_data)}")
        
        # 标准化处理
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        return image
    
    def _select_approach(self, task_type: VisionTask, options: Optional[Dict[str, Any]]) -> VisionApproach:
        """选择分析方法"""
        if options and "approach" in options:
            return VisionApproach(options["approach"])
        
        # 根据任务类型选择默认方法
        if task_type == VisionTask.TEXT_RECOGNITION:
            return VisionApproach.OCR_ENHANCED
        elif task_type == VisionTask.UI_ELEMENT_DETECTION:
            return VisionApproach.MULTIMODAL_FUSION
        elif task_type == VisionTask.COLOR_ANALYSIS:
            return VisionApproach.PURE_VISION
        else:
            return self.task_config["default_approach"]
    
    def _generate_cache_key(self, image: np.ndarray, task_type: VisionTask, approach: VisionApproach) -> str:
        """生成缓存键"""
        # 使用图像的哈希值作为缓存键的一部分
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        key_parts = [image_hash, task_type.value, approach.value]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    async def _predict_element_interaction(self, element: UIElement) -> Optional[Dict[str, Any]]:
        """预测元素交互"""
        suggestion = {
            "element_id": element.id,
            "element_type": element.element_type.value,
            "interaction_type": "unknown",
            "confidence": 0.0,
            "reasoning": ""
        }
        
        # 基于元素类型预测交互
        if element.element_type == ElementType.BUTTON:
            suggestion.update({
                "interaction_type": "click",
                "confidence": 0.9,
                "reasoning": "按钮元素通常支持点击交互"
            })
        elif element.element_type == ElementType.TEXT_INPUT:
            suggestion.update({
                "interaction_type": "type",
                "confidence": 0.85,
                "reasoning": "文本输入框支持键盘输入"
            })
        elif element.element_type == ElementType.LINK:
            suggestion.update({
                "interaction_type": "click",
                "confidence": 0.8,
                "reasoning": "链接元素支持点击跳转"
            })
        elif element.element_type == ElementType.CHECKBOX:
            suggestion.update({
                "interaction_type": "toggle",
                "confidence": 0.8,
                "reasoning": "复选框支持切换状态"
            })
        elif element.element_type == ElementType.SLIDER:
            suggestion.update({
                "interaction_type": "drag",
                "confidence": 0.75,
                "reasoning": "滑块支持拖拽调节"
            })
        
        # 基于视觉特征调整置信度
        if element.visual_features.get("has_hover_effect", False):
            suggestion["confidence"] += 0.1
        
        if element.attributes.get("disabled", False):
            suggestion["confidence"] = 0.0
            suggestion["interaction_type"] = "disabled"
            suggestion["reasoning"] = "元素被禁用，无法交互"
        
        return suggestion if suggestion["confidence"] > 0.3 else None