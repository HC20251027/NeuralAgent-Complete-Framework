"""
颜色检测和轮廓识别模块 - 专门用于精确的颜色分析和轮廓检测
Color Detection and Contour Recognition Module - Specialized for precise color analysis and contour detection
"""

import asyncio
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageColor
import colorsys
import math
from sklearn.cluster import KMeans
from collections import Counter

from neural_agent_vision.neural_agent_vision import (
    ColorInfo, ContourInfo, BoundingBox, VisionTask,
    NeuralAgentVisionModule
)


class ColorSpace(Enum):
    """颜色空间"""
    RGB = "rgb"
    HSV = "hsv"
    LAB = "lab"
    LUV = "luv"
    YUV = "yuv"
    CMYK = "cmyk"


class ColorHarmony(Enum):
    """色彩和谐"""
    COMPLEMENTARY = "complementary"
    ANALOGOUS = "analogous"
    TRIADIC = "triadic"
    TETRADIC = "tetradic"
    MONOCHROMATIC = "monochromatic"
    NEUTRAL = "neutral"


class ContourMethod(Enum):
    """轮廓检测方法"""
    EXTERNAL = "external"
    LIST = "list"
    TREE = "tree"
    SIMPLE = "simple"
    NONE = "none"


@dataclass
class ColorRegion:
    """颜色区域"""
    id: str
    color: Tuple[int, int, int]  # RGB
    color_name: str
    area: int
    percentage: float
    bounding_box: BoundingBox
    confidence: float
    saturation: float
    brightness: float
    hue: float = 0.0


@dataclass
class ColorScheme:
    """色彩方案"""
    primary_colors: List[ColorRegion]
    secondary_colors: List[ColorRegion]
    accent_colors: List[ColorRegion]
    neutral_colors: List[ColorRegion]
    harmony_type: ColorHarmony
    contrast_ratio: float
    color_temperature: str  # "warm", "cool", "neutral"
    accessibility_score: float


@dataclass
class ContourFeature:
    """轮廓特征"""
    contour_id: str
    area: float
    perimeter: float
    circularity: float
    aspect_ratio: float
    solidity: float
    extent: float
    convexity: float
    eccentricity: float
    orientation: float
    bounding_box: BoundingBox
    centroid: Tuple[int, int]
    moments: Dict[str, float]


@dataclass
class ShapeClassification:
    """形状分类"""
    contour_id: str
    shape_type: str  # "circle", "rectangle", "triangle", "polygon", "irregular"
    confidence: float
    geometric_features: Dict[str, float]
    regularity_score: float
    symmetry_score: float


class ColorAnalyzer:
    """颜色分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 颜色分析配置
        self.color_config = {
            "cluster_count": config.get("cluster_count", 8),
            "color_space": ColorSpace(config.get("color_space", "rgb")),
            "min_region_area": config.get("min_region_area", 100),
            "color_name_accuracy": config.get("color_name_accuracy", 0.8),
            "harmony_threshold": config.get("harmony_threshold", 0.7),
            "accessibility_threshold": config.get("accessibility_threshold", 4.5)
        }
        
        # 预定义颜色名称映射
        self.color_names = self._initialize_color_names()
        
        # 颜色和谐规则
        self.harmony_rules = {
            ColorHarmony.COMPLEMENTARY: self._check_complementary_harmony,
            ColorHarmony.ANALOGOUS: self._check_analogous_harmony,
            ColorHarmony.TRIADIC: self._check_triadic_harmony,
            ColorHarmony.TETRADIC: self._check_tetradic_harmony,
            ColorHarmony.MONOCHROMATIC: self._check_monochromatic_harmony,
            ColorHarmony.NEUTRAL: self._check_neutral_harmony
        }
    
    def _initialize_color_names(self) -> Dict[str, Tuple[int, int, int]]:
        """初始化颜色名称映射"""
        return {
            # 基础颜色
            "红色": (255, 0, 0),
            "绿色": (0, 255, 0),
            "蓝色": (0, 0, 255),
            "黄色": (255, 255, 0),
            "紫色": (128, 0, 128),
            "橙色": (255, 165, 0),
            "粉色": (255, 192, 203),
            "棕色": (165, 42, 42),
            "灰色": (128, 128, 128),
            "黑色": (0, 0, 0),
            "白色": (255, 255, 255),
            
            # 扩展颜色
            "深红色": (139, 0, 0),
            "浅红色": (255, 182, 193),
            "深绿色": (0, 100, 0),
            "浅绿色": (144, 238, 144),
            "深蓝色": (0, 0, 139),
            "浅蓝色": (173, 216, 230),
            "深黄色": (255, 215, 0),
            "浅黄色": (255, 255, 224),
            "深紫色": (75, 0, 130),
            "浅紫色": (221, 160, 221),
            "深橙色": (255, 140, 0),
            "浅橙色": (255, 218, 185),
            "深粉色": (255, 20, 147),
            "浅粉色": (255, 218, 185),
            "深棕色": (101, 67, 33),
            "浅棕色": (210, 180, 140),
            "深灰色": (64, 64, 64),
            "浅灰色": (211, 211, 211),
            
            # 专业颜色
            "天蓝色": (135, 206, 235),
            "深天蓝色": (0, 191, 255),
            "海绿色": (46, 139, 87),
            "深海绿色": (0, 100, 0),
            "森林绿": (34, 139, 34),
            "橄榄绿": (128, 128, 0),
            "暗橄榄绿": (85, 107, 47),
            "亮橄榄绿": (154, 205, 50),
            "暗青色": (0, 139, 139),
            "亮青色": (64, 224, 208),
            "深青色": (0, 206, 209),
            "亮青色": (224, 255, 255),
            "暗紫罗兰": (148, 0, 211),
            "亮紫罗兰": (238, 130, 238),
            "暗兰花紫": (153, 50, 204),
            "亮兰花紫": (186, 85, 211)
        }
    
    async def analyze_colors(self, image: np.ndarray, region: Optional[BoundingBox] = None) -> ColorInfo:
        """分析颜色"""
        try:
            start_time = datetime.now()
            
            # 提取分析区域
            if region:
                analysis_region = image[region.y:region.y + region.height, region.x:region.x + region.width]
            else:
                analysis_region = image
            
            # 颜色聚类分析
            color_regions = await self._perform_color_clustering(analysis_region)
            
            # 颜色命名
            named_colors = await self._name_colors(color_regions)
            
            # 颜色和谐分析
            harmony_analysis = await self._analyze_color_harmony(color_regions)
            
            # 可访问性分析
            accessibility_analysis = await self._analyze_accessibility(color_regions)
            
            # 构建结果
            result = ColorInfo(
                dominant_colors=[region.color for region in color_regions],
                color_names=named_colors,
                color_percentages=[region.percentage for region in color_regions],
                palette=named_colors,
                contrast_ratio=accessibility_analysis.get("contrast_ratio", 0.0),
                brightness=np.mean([region.brightness for region in color_regions]),
                saturation=np.mean([region.saturation for region in color_regions])
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"颜色分析完成，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"颜色分析失败: {str(e)}")
            raise
    
    async def detect_color_regions(self, image: np.ndarray) -> List[ColorRegion]:
        """检测颜色区域"""
        try:
            # 转换颜色空间
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 颜色分割
            color_masks = await self._create_color_masks(hsv_image)
            
            # 提取区域
            regions = []
            for i, (color_name, mask) in enumerate(color_masks.items()):
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > self.color_config["min_region_area"]:
                        # 计算边界框
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # 计算平均颜色
                        roi = image[y:y + h, x:x + w]
                        avg_color = np.mean(roi.reshape(-1, 3), axis=0).astype(int)
                        
                        # 计算颜色属性
                        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                        avg_hsv = np.mean(hsv_roi.reshape(-1, 3), axis=0)
                        
                        region = ColorRegion(
                            id=f"color_region_{i}_{len(regions)}",
                            color=tuple(avg_color),
                            color_name=color_name,
                            area=area,
                            percentage=0.0,  # 稍后计算
                            bounding_box=BoundingBox(x, y, w, h),
                            confidence=0.8,
                            saturation=avg_hsv[1] / 255.0,
                            brightness=avg_hsv[2] / 255.0,
                            hue=avg_hsv[0]
                        )
                        regions.append(region)
            
            # 计算百分比
            total_area = sum(region.area for region in regions)
            for region in regions:
                region.percentage = (region.area / total_area) * 100 if total_area > 0 else 0
            
            return regions
            
        except Exception as e:
            self.logger.error(f"颜色区域检测失败: {str(e)}")
            return []
    
    async def _perform_color_clustering(self, image: np.ndarray) -> List[ColorRegion]:
        """执行颜色聚类"""
        # 重塑图像数据
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        # K-means聚类
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(
            data, self.color_config["cluster_count"], None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )
        
        # 计算聚类分布
        labels = labels.flatten()
        percentages = []
        for i in range(self.color_config["cluster_count"]):
            percentage = (labels == i).sum() / len(labels) * 100
            percentages.append(percentage)
        
        # 创建颜色区域
        regions = []
        for i, (center, percentage) in enumerate(zip(centers, percentages)):
            if percentage > 1.0:  # 过滤小区域
                color = tuple(center.astype(int))
                
                # 转换到HSV计算属性
                hsv_center = cv2.cvtColor(
                    np.uint8([[center]]), cv2.COLOR_BGR2HSV
                )[0][0]
                
                region = ColorRegion(
                    id=f"cluster_{i}",
                    color=color,
                    color_name="",  # 稍后命名
                    area=int(percentage * image.shape[0] * image.shape[1] / 100),
                    percentage=percentage,
                    bounding_box=BoundingBox(0, 0, 0, 0),  # 聚类没有具体位置
                    confidence=0.9,
                    saturation=hsv_center[1] / 255.0,
                    brightness=hsv_center[2] / 255.0,
                    hue=hsv_center[0]
                )
                regions.append(region)
        
        # 按百分比排序
        regions.sort(key=lambda x: x.percentage, reverse=True)
        
        return regions
    
    async def _name_colors(self, regions: List[ColorRegion]) -> List[str]:
        """命名颜色"""
        color_names = []
        
        for region in regions:
            # 查找最接近的预定义颜色
            min_distance = float('inf')
            closest_name = "未知颜色"
            
            for name, reference_color in self.color_names.items():
                distance = self._calculate_color_distance(region.color, reference_color)
                if distance < min_distance:
                    min_distance = distance
                    closest_name = name
            
            # 如果距离太远，使用RGB值描述
            if min_distance > 100:
                closest_name = f"RGB({region.color[0]}, {region.color[1]}, {region.color[2]})"
            
            region.color_name = closest_name
            color_names.append(closest_name)
        
        return color_names
    
    def _calculate_color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """计算颜色距离"""
        return math.sqrt(
            (color1[0] - color2[0]) ** 2 +
            (color1[1] - color2[1]) ** 2 +
            (color1[2] - color2[2]) ** 2
        )
    
    async def _analyze_color_harmony(self, regions: List[ColorRegion]) -> Dict[str, Any]:
        """分析颜色和谐"""
        if len(regions) < 2:
            return {"harmony_type": ColorHarmony.NEUTRAL.value, "score": 0.0}
        
        # 提取主要颜色
        primary_colors = [region.hue for region in regions[:5] if region.hue >= 0]
        
        harmony_scores = {}
        for harmony_type, checker in self.harmony_rules.items():
            score = checker(primary_colors)
            harmony_scores[harmony_type.value] = score
        
        # 选择最佳和谐类型
        best_harmony = max(harmony_scores.items(), key=lambda x: x[1])
        
        return {
            "harmony_type": best_harmony[0],
            "score": best_harmony[1],
            "all_scores": harmony_scores
        }
    
    async def _analyze_accessibility(self, regions: List[ColorRegion]) -> Dict[str, Any]:
        """分析可访问性"""
        if len(regions) < 2:
            return {"contrast_ratio": 1.0, "accessibility_score": 0.0}
        
        # 计算最高对比度
        max_contrast = 0.0
        for i, region1 in enumerate(regions):
            for region2 in regions[i+1:]:
                contrast = self._calculate_contrast_ratio(region1.color, region2.color)
                max_contrast = max(max_contrast, contrast)
        
        # 计算可访问性得分
        accessibility_score = min(max_contrast / self.color_config["accessibility_threshold"], 1.0)
        
        return {
            "contrast_ratio": max_contrast,
            "accessibility_score": accessibility_score,
            "wcag_level": "AA" if max_contrast >= 4.5 else "A" if max_contrast >= 3.0 else "Fail"
        }
    
    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """计算对比度比率"""
        def relative_luminance(color):
            def linearize(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = map(linearize, color)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = relative_luminance(color1)
        l2 = relative_luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    async def _create_color_masks(self, hsv_image: np.ndarray) -> Dict[str, np.ndarray]:
        """创建颜色掩码"""
        masks = {}
        
        # 定义颜色范围
        color_ranges = {
            "红色": [(0, 50, 50), (10, 255, 255)],
            "绿色": [(40, 40, 40), (80, 255, 255)],
            "蓝色": [(100, 50, 50), (130, 255, 255)],
            "黄色": [(20, 100, 100), (30, 255, 255)],
            "紫色": [(130, 50, 50), (160, 255, 255)],
            "橙色": [(10, 100, 100), (20, 255, 255)],
            "粉色": [(140, 50, 50), (180, 255, 255)],
            "青色": [(90, 50, 50), (110, 255, 255)]
        }
        
        for color_name, (lower, upper) in color_ranges.items():
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv_image, lower, upper)
            masks[color_name] = mask
        
        return masks
    
    # 颜色和谐检查方法
    
    def _check_complementary_harmony(self, hues: List[float]) -> float:
        """检查互补色和谐"""
        if len(hues) < 2:
            return 0.0
        
        # 检查是否有互补色对
        for i, h1 in enumerate(hues):
            for h2 in hues[i+1:]:
                diff = abs(h1 - h2)
                if 170 <= diff <= 190:  # 互补色范围
                    return 0.8
        
        return 0.2
    
    def _check_analogous_harmony(self, hues: List[float]) -> float:
        """检查类似色和谐"""
        if len(hues) < 2:
            return 0.0
        
        # 检查色相是否相近
        sorted_hues = sorted(hues)
        max_gap = max(sorted_hues[i+1] - sorted_hues[i] for i in range(len(sorted_hues)-1))
        
        if max_gap < 30:  # 类似色范围
            return 0.9
        elif max_gap < 60:
            return 0.6
        else:
            return 0.2
    
    def _check_triadic_harmony(self, hues: List[float]) -> float:
        """检查三角色和谐"""
        if len(hues) < 3:
            return 0.0
        
        # 检查是否有120度间隔的颜色
        for i, h1 in enumerate(hues):
            for j, h2 in enumerate(hues[i+1:], i+1):
                for k, h3 in enumerate(hues[j+1:], j+1):
                    diff1 = abs(h2 - h1)
                    diff2 = abs(h3 - h2)
                    diff3 = abs(h3 - h1)
                    
                    if (110 <= diff1 <= 130 and 110 <= diff2 <= 130) or \
                       (110 <= diff1 <= 130 and 110 <= diff3 <= 130) or \
                       (110 <= diff2 <= 130 and 110 <= diff3 <= 130):
                        return 0.8
        
        return 0.3
    
    def _check_tetradic_harmony(self, hues: List[float]) -> float:
        """检查四角色和谐"""
        if len(hues) < 4:
            return 0.0
        
        # 检查是否有两组互补色
        complementary_pairs = 0
        for i, h1 in enumerate(hues):
            for j, h2 in enumerate(hues[i+1:], i+1):
                diff = abs(h2 - h1)
                if 170 <= diff <= 190:
                    complementary_pairs += 1
        
        if complementary_pairs >= 2:
            return 0.8
        elif complementary_pairs >= 1:
            return 0.5
        else:
            return 0.2
    
    def _check_monochromatic_harmony(self, hues: List[float]) -> float:
        """检查单色和谐"""
        if len(hues) < 2:
            return 0.0
        
        # 检查色相是否相近
        hue_range = max(hues) - min(hues)
        
        if hue_range < 15:  # 单色范围
            return 0.9
        elif hue_range < 30:
            return 0.6
        else:
            return 0.2
    
    def _check_neutral_harmony(self, hues: List[float]) -> float:
        """检查中性色和谐"""
        # 中性色和谐主要基于亮度和饱和度
        # 简化实现，返回中等分数
        return 0.5


class ContourRecognizer:
    """轮廓识别器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 轮廓识别配置
        self.contour_config = {
            "min_area": config.get("min_area", 100),
            "max_area": config.get("max_area", 100000),
            "min_perimeter": config.get("min_perimeter", 50),
            "epsilon_factor": config.get("epsilon_factor", 0.02),
            "shape_tolerance": config.get("shape_tolerance", 0.1)
        }
        
        # 形状分类阈值
        self.shape_thresholds = {
            "circle_circularity": 0.7,
            "rectangle_aspect_ratio": 0.3,
            "triangle_corners": 3,
            "polygon_max_corners": 8
        }
    
    async def detect_contours(self, image: np.ndarray, method: ContourMethod = ContourMethod.EXTERNAL) -> ContourInfo:
        """检测轮廓"""
        try:
            start_time = datetime.now()
            
            # 预处理图像
            processed_image = await self._preprocess_image(image)
            
            # 提取轮廓
            contours, hierarchy = await self._extract_contours(processed_image, method)
            
            # 分析轮廓特征
            contour_features = []
            bounding_boxes = []
            areas = []
            perimeters = []
            circularities = []
            aspect_ratios = []
            
            for i, contour in enumerate(contours):
                # 计算基础特征
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                # 过滤太小的轮廓
                if area < self.contour_config["min_area"] or area > self.contour_config["max_area"]:
                    continue
                
                if perimeter < self.contour_config["min_perimeter"]:
                    continue
                
                # 计算边界框
                x, y, w, h = cv2.boundingRect(contour)
                bbox = BoundingBox(x, y, w, h)
                
                # 计算高级特征
                features = await self._calculate_contour_features(contour, bbox)
                
                contour_features.append(features)
                bounding_boxes.append(bbox)
                areas.append(area)
                perimeters.append(perimeter)
                circularities.append(features.circularity)
                aspect_ratios.append(features.aspect_ratio)
            
            # 构建结果
            result = ContourInfo(
                contours=contours[:len(contour_features)],  # 过滤后的轮廓
                bounding_boxes=bounding_boxes,
                areas=areas,
                perimeters=perimeters,
                circularity=circularities,
                aspect_ratios=aspect_ratios,
                hierarchy=hierarchy
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"轮廓检测完成，检测到 {len(contour_features)} 个轮廓，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"轮廓检测失败: {str(e)}")
            raise
    
    async def classify_shapes(self, contours: List[np.ndarray], bounding_boxes: List[BoundingBox]) -> List[ShapeClassification]:
        """分类形状"""
        try:
            classifications = []
            
            for i, (contour, bbox) in enumerate(zip(contours, bounding_boxes)):
                # 计算形状特征
                features = await self._calculate_shape_features(contour, bbox)
                
                # 分类形状
                shape_type = await self._classify_shape_type(features)
                
                # 计算规则性和对称性
                regularity_score = await self._calculate_regularity_score(contour)
                symmetry_score = await self._calculate_symmetry_score(contour, bbox)
                
                classification = ShapeClassification(
                    contour_id=f"shape_{i}",
                    shape_type=shape_type,
                    confidence=features.get("classification_confidence", 0.5),
                    geometric_features=features,
                    regularity_score=regularity_score,
                    symmetry_score=symmetry_score
                )
                
                classifications.append(classification)
            
            return classifications
            
        except Exception as e:
            self.logger.error(f"形状分类失败: {str(e)}")
            return []
    
    async def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 应用高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 边缘检测
        edges = cv2.Canny(blurred, 50, 150)
        
        # 形态学操作
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return edges
    
    async def _extract_contours(self, processed_image: np.ndarray, method: ContourMethod) -> Tuple[List[np.ndarray], Optional[np.ndarray]]:
        """提取轮廓"""
        if method == ContourMethod.EXTERNAL:
            contours, hierarchy = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        elif method == ContourMethod.LIST:
            contours, hierarchy = cv2.findContours(processed_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        elif method == ContourMethod.TREE:
            contours, hierarchy = cv2.findContours(processed_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours, hierarchy = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        return contours, hierarchy
    
    async def _calculate_contour_features(self, contour: np.ndarray, bbox: BoundingBox) -> ContourFeature:
        """计算轮廓特征"""
        # 基础特征
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # 圆形度
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # 长宽比
        aspect_ratio = bbox.width / bbox.height if bbox.height > 0 else 0
        
        # 实心度
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # 延展度
        extent = area / (bbox.width * bbox.height) if bbox.area > 0 else 0
        
        # 凸性
        convexity = hull_area / area if area > 0 else 0
        
        # 离心率
        if len(contour) >= 5:
            ellipse = cv2.fitEllipse(contour)
            (center, axes, angle) = ellipse
            major_axis = max(axes)
            minor_axis = min(axes)
            eccentricity = math.sqrt(1 - (minor_axis / major_axis) ** 2) if major_axis > 0 else 0
        else:
            eccentricity = 0
        
        # 方向
        if len(contour) >= 5:
            ellipse = cv2.fitEllipse(contour)
            orientation = ellipse[2]
        else:
            orientation = 0
        
        # 质心
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = bbox.center
        
        # 矩特征
        moments = {
            "hu_moments": cv2.HuMoments(M).flatten().tolist(),
            "central_moments": {
                "m20": M["m20"],
                "m02": M["m02"],
                "m11": M["m11"]
            }
        }
        
        return ContourFeature(
            contour_id=str(uuid.uuid4()),
            area=area,
            perimeter=perimeter,
            circularity=circularity,
            aspect_ratio=aspect_ratio,
            solidity=solidity,
            extent=extent,
            convexity=convexity,
            eccentricity=eccentricity,
            orientation=orientation,
            bounding_box=bbox,
            centroid=(cx, cy),
            moments=moments
        )
    
    async def _calculate_shape_features(self, contour: np.ndarray, bbox: BoundingBox) -> Dict[str, float]:
        """计算形状特征"""
        features = {}
        
        # 近似多边形
        epsilon = self.contour_config["epsilon_factor"] * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 角点数量
        features["corner_count"] = len(approx)
        
        # 边界框比率
        features["bbox_ratio"] = bbox.width / bbox.height if bbox.height > 0 else 0
        
        # 轮廓复杂度
        contour_length = cv2.arcLength(contour, True)
        features["complexity"] = contour_length / (2 * (bbox.width + bbox.height)) if bbox.width + bbox.height > 0 else 0
        
        # 紧凑性
        area = cv2.contourArea(contour)
        features["compactness"] = (perimeter ** 2) / area if area > 0 else 0
        
        # 分类置信度
        features["classification_confidence"] = self._calculate_classification_confidence(contour, bbox)
        
        return features
    
    def _calculate_classification_confidence(self, contour: np.ndarray, bbox: BoundingBox) -> float:
        """计算分类置信度"""
        # 基于轮廓特征计算分类置信度
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # 圆形度
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # 边界框比率
        bbox_ratio = bbox.width / bbox.height if bbox.height > 0 else 0
        
        # 综合置信度
        confidence = 0.0
        
        # 圆形置信度
        if circularity > 0.8:
            confidence += 0.4
        elif circularity > 0.6:
            confidence += 0.2
        
        # 矩形置信度
        if 0.5 < bbox_ratio < 2.0:
            confidence += 0.3
        
        # 轮廓完整性
        if area > 1000:  # 大轮廓更可靠
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    async def _classify_shape_type(self, features: Dict[str, float]) -> str:
        """分类形状类型"""
        corner_count = features.get("corner_count", 0)
        bbox_ratio = features.get("bbox_ratio", 1.0)
        complexity = features.get("complexity", 1.0)
        
        # 圆形检测
        if features.get("circularity", 0) > self.shape_thresholds["circle_circularity"]:
            return "circle"
        
        # 三角形检测
        elif corner_count == 3:
            return "triangle"
        
        # 矩形检测
        elif corner_count == 4 and 0.5 < bbox_ratio < 2.0:
            return "rectangle"
        
        # 多边形检测
        elif 4 < corner_count <= self.shape_thresholds["polygon_max_corners"]:
            return "polygon"
        
        # 不规则形状
        else:
            return "irregular"
    
    async def _calculate_regularity_score(self, contour: np.ndarray) -> float:
        """计算规则性得分"""
        # 计算轮廓的不规则程度
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if area == 0 or perimeter == 0:
            return 0.0
        
        # 圆形度作为规则性指标
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        
        # 转换为规则性得分
        regularity = min(circularity, 1.0)
        
        return regularity
    
    async def _calculate_symmetry_score(self, contour: np.ndarray, bbox: BoundingBox) -> float:
        """计算对称性得分"""
        # 简化实现：基于边界框的对称性
        center_x = bbox.x + bbox.width / 2
        center_y = bbox.y + bbox.height / 2
        
        # 计算轮廓的矩
        M = cv2.moments(contour)
        
        if M["m00"] == 0:
            return 0.0
        
        # 水平对称性
        mu20 = M["m20"] / M["m00"] - center_x ** 2
        mu02 = M["m02"] / M["m00"] - center_y ** 2
        
        # 对称性得分
        horizontal_symmetry = 1.0 - abs(mu20) / (mu20 + mu02 + 1e-10)
        vertical_symmetry = 1.0 - abs(mu02) / (mu20 + mu02 + 1e-10)
        
        symmetry_score = (horizontal_symmetry + vertical_symmetry) / 2
        
        return max(0.0, min(1.0, symmetry_score))


class ColorContourAnalyzer:
    """颜色轮廓分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.color_analyzer = ColorAnalyzer(config)
        self.contour_recognizer = ContourRecognizer(config)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_color_contours(self, image: np.ndarray) -> Dict[str, Any]:
        """分析颜色和轮廓"""
        try:
            start_time = datetime.now()
            
            # 并行执行颜色和轮廓分析
            color_task = asyncio.create_task(self.color_analyzer.analyze_colors(image))
            contour_task = asyncio.create_task(self.contour_recognizer.detect_contours(image))
            
            color_result = await color_task
            contour_result = await contour_task
            
            # 颜色轮廓关联分析
            color_contour_analysis = await self._analyze_color_contour_relationship(
                image, color_result, contour_result
            )
            
            # 综合分析结果
            combined_result = {
                "color_analysis": asdict(color_result),
                "contour_analysis": asdict(contour_result),
                "color_contour_relationship": color_contour_analysis,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "analysis_summary": await self._generate_analysis_summary(color_result, contour_result)
            }
            
            return combined_result
            
        except Exception as e:
            self.logger.error(f"颜色轮廓分析失败: {str(e)}")
            raise
    
    async def _analyze_color_contour_relationship(self, 
                                                image: np.ndarray, 
                                                color_result: ColorInfo, 
                                                contour_result: ContourInfo) -> Dict[str, Any]:
        """分析颜色与轮廓的关系"""
        relationship_analysis = {
            "color_dominant_regions": [],
            "contour_color_mapping": [],
            "shape_color_consistency": 0.0,
            "visual_harmony_score": 0.0
        }
        
        # 分析主要颜色区域
        if color_result.dominant_colors:
            dominant_regions = await self._identify_dominant_color_regions(image, color_result)
            relationship_analysis["color_dominant_regions"] = dominant_regions
        
        # 轮廓颜色映射
        if contour_result.bounding_boxes:
            contour_colors = await self._map_contours_to_colors(image, contour_result)
            relationship_analysis["contour_color_mapping"] = contour_colors
        
        # 形状颜色一致性
        consistency_score = await self._calculate_shape_color_consistency(contour_result, color_result)
        relationship_analysis["shape_color_consistency"] = consistency_score
        
        # 视觉和谐得分
        harmony_score = await self._calculate_visual_harmony(color_result, contour_result)
        relationship_analysis["visual_harmony_score"] = harmony_score
        
        return relationship_analysis
    
    async def _identify_dominant_color_regions(self, image: np.ndarray, color_result: ColorInfo) -> List[Dict[str, Any]]:
        """识别主要颜色区域"""
        regions = []
        
        # 转换颜色空间进行分割
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        for i, color in enumerate(color_result.dominant_colors[:5]):  # 取前5个主要颜色
            # 转换颜色到HSV
            color_bgr = np.uint8([[color]])
            color_hsv = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)[0][0]
            
            # 创建颜色掩码
            lower = np.array([color_hsv[0] - 10, 50, 50])
            upper = np.array([color_hsv[0] + 10, 255, 255])
            mask = cv2.inRange(hsv_image, lower, upper)
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找到最大轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                
                if area > 1000:  # 最小区域阈值
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    
                    regions.append({
                        "color": color,
                        "color_name": color_result.color_names[i] if i < len(color_result.color_names) else "unknown",
                        "area": area,
                        "percentage": color_result.color_percentages[i] if i < len(color_result.color_percentages) else 0,
                        "bounding_box": {"x": x, "y": y, "width": w, "height": h},
                        "contour_count": len(contours)
                    })
        
        return regions
    
    async def _map_contours_to_colors(self, image: np.ndarray, contour_result: ContourInfo) -> List[Dict[str, Any]]:
        """将轮廓映射到颜色"""
        mappings = []
        
        for i, bbox in enumerate(contour_result.bounding_boxes):
            # 提取轮廓区域
            roi = image[bbox.y:bbox.y + bbox.height, bbox.x:bbox.x + bbox.width]
            
            if roi.size > 0:
                # 计算区域平均颜色
                avg_color = np.mean(roi.reshape(-1, 3), axis=0).astype(int)
                
                # 计算颜色方差（衡量颜色一致性）
                color_variance = np.var(roi.reshape(-1, 3), axis=0).mean()
                
                mappings.append({
                    "contour_id": i,
                    "average_color": avg_color.tolist(),
                    "color_variance": float(color_variance),
                    "area": contour_result.areas[i],
                    "color_consistency": 1.0 / (1.0 + color_variance / 1000.0)  # 归一化一致性得分
                })
        
        return mappings
    
    async def _calculate_shape_color_consistency(self, contour_result: ContourInfo, color_result: ColorInfo) -> float:
        """计算形状颜色一致性"""
        if not contour_result.bounding_boxes or not color_result.dominant_colors:
            return 0.0
        
        # 简化的计算：基于颜色分布的均匀性
        color_uniformity = 1.0 - np.std(color_result.color_percentages) / 100.0 if color_result.color_percentages else 0.0
        
        # 形状规则性
        avg_circularity = np.mean(contour_result.circularity) if contour_result.circularity else 0.0
        shape_regularity = avg_circularity
        
        # 综合一致性得分
        consistency = (color_uniformity + shape_regularity) / 2
        
        return max(0.0, min(1.0, consistency))
    
    async def _calculate_visual_harmony(self, color_result: ColorInfo, contour_result: ContourInfo) -> float:
        """计算视觉和谐得分"""
        harmony_score = 0.0
        
        # 颜色和谐得分
        if hasattr(color_result, 'contrast_ratio') and color_result.contrast_ratio > 0:
            harmony_score += 0.4
        
        # 饱和度平衡
        if hasattr(color_result, 'saturation') and 0.3 < color_result.saturation < 0.8:
            harmony_score += 0.3
        
        # 轮廓规则性
        if contour_result.circularity:
            avg_circularity = np.mean(contour_result.circularity)
            if 0.5 < avg_circularity < 0.9:
                harmony_score += 0.3
        
        return min(harmony_score, 1.0)
    
    async def _generate_analysis_summary(self, color_result: ColorInfo, contour_result: ContourInfo) -> Dict[str, Any]:
        """生成分析摘要"""
        return {
            "dominant_colors_count": len(color_result.dominant_colors),
            "contours_detected": len(contour_result.bounding_boxes),
            "average_color_saturation": getattr(color_result, 'saturation', 0.0),
            "average_color_brightness": getattr(color_result, 'brightness', 0.0),
            "average_contour_circularity": np.mean(contour_result.circularity) if contour_result.circularity else 0.0,
            "largest_contour_area": max(contour_result.areas) if contour_result.areas else 0,
            "color_diversity": len(set(color_result.color_names)) if color_result.color_names else 0,
            "shape_diversity": len(set(contour_result.circularity)) if contour_result.circularity else 0
        }


class ColorContourModule:
    """颜色轮廓模块主类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzer = ColorContourAnalyzer(config)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_image(self, 
                          image_data: Union[str, np.ndarray, bytes],
                          analysis_type: str = "combined") -> Dict[str, Any]:
        """分析图像"""
        try:
            # 预处理图像
            image = await self._preprocess_image(image_data)
            
            if analysis_type == "color_only":
                result = await self.analyzer.color_analyzer.analyze_colors(image)
                return asdict(result)
            
            elif analysis_type == "contour_only":
                result = await self.analyzer.contour_recognizer.detect_contours(image)
                return asdict(result)
            
            else:  # combined
                result = await self.analyzer.analyze_color_contours(image)
                return result
                
        except Exception as e:
            self.logger.error(f"图像分析失败: {str(e)}")
            raise
    
    async def detect_color_regions(self, image_data: Union[str, np.ndarray, bytes]) -> List[ColorRegion]:
        """检测颜色区域"""
        image = await self._preprocess_image(image_data)
        return await self.analyzer.color_analyzer.detect_color_regions(image)
    
    async def detect_contours(self, 
                            image_data: Union[str, np.ndarray, bytes],
                            method: ContourMethod = ContourMethod.EXTERNAL) -> ContourInfo:
        """检测轮廓"""
        image = await self._preprocess_image(image_data)
        return await self.analyzer.contour_recognizer.detect_contours(image, method)
    
    async def _preprocess_image(self, image_data: Union[str, np.ndarray, bytes]) -> np.ndarray:
        """预处理图像"""
        if isinstance(image_data, str):
            # 从文件路径加载
            if image_data.startswith("data:image"):
                import base64
                from io import BytesIO
                header, data = image_data.split(",", 1)
                image_data = base64.b64decode(data)
            
            image = Image.open(BytesIO(image_data))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
        elif isinstance(image_data, bytes):
            from io import BytesIO
            image = Image.open(BytesIO(image_data))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
        elif isinstance(image_data, np.ndarray):
            image = image_data
            
        else:
            raise ValueError(f"不支持的图像数据类型: {type(image_data)}")
        
        # 标准化处理
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        return image