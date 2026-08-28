"""
用户接口演示 - User Interface Demonstration
==========================================

提供完整的用户接口演示：
1. Web界面演示
2. 命令行接口演示
3. API接口演示
4. 集成接口演示

Author: MiniMax Agent
Date: 2025-11-06
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# Web框架
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# 命令行接口
import argparse
import sys
from io import StringIO

# HTTP服务器
try:
    import uvicorn
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False

# 框架集成
from agno_bmad_integration.framework import IntegrationFramework
from neural_agent_vision.neural_agent_vision import NeuralAgentVision
from voice_interaction.voice_control_interface import VoiceControlInterface
from workflow_demonstration.video_to_prd_demo import VideoToPRDDemo
from workflow_demonstration.collaboration_modes import CollaborationModeDemo


@dataclass
class UserRequest:
    """用户请求"""
    request_id: str
    user_id: str
    request_type: str  # web, cli, api, integration
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'request_type': self.request_type,
            'action': self.action,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status
        }


@dataclass
class UserResponse:
    """用户响应"""
    response_id: str
    request_id: str
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'response_id': self.response_id,
            'request_id': self.request_id,
            'success': self.success,
            'data': self.data,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat()
        }


class WebInterface:
    """Web界面"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app = None
        self.templates = None
        self.video_demo = VideoToPRDDemo()
        self.collaboration_demo = CollaborationModeDemo()
        
        if FASTAPI_AVAILABLE:
            self._initialize_fastapi()
    
    def _initialize_fastapi(self):
        """初始化FastAPI应用"""
        self.app = FastAPI(title="NeuralAgent × Agno-BMAD 演示系统")
        
        # 静态文件
        static_dir = Path("/workspace/web_static")
        static_dir.mkdir(exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # 模板
        templates_dir = Path("/workspace/web_templates")
        templates_dir.mkdir(exist_ok=True)
        self.templates = Jinja2Templates(directory=str(templates_dir))
        
        # 路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """主页"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>NeuralAgent × Agno-BMAD 演示系统</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { text-align: center; margin-bottom: 40px; }
                    .feature { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                    .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                    .button:hover { background: #0056b3; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>NeuralAgent × Agno-BMAD-LM Studio 融合架构</h1>
                        <p>全功能本地化AI智能体大整合方案演示系统</p>
                    </div>
                    
                    <div class="feature">
                        <h2>🎥 视频到PRD自动生成</h2>
                        <p>上传视频文件，自动分析内容并生成产品需求文档</p>
                        <a href="/video-demo" class="button">体验视频分析</a>
                    </div>
                    
                    <div class="feature">
                        <h2>🤝 智能体协作模式</h2>
                        <p>演示三种不同的智能体协作模式：串行、并行、混合</p>
                        <a href="/collaboration-demo" class="button">查看协作演示</a>
                    </div>
                    
                    <div class="feature">
                        <h2>🎤 语音交互系统</h2>
                        <p>体验语音识别、合成、声纹识别和情感分析功能</p>
                        <a href="/voice-demo" class="button">语音交互体验</a>
                    </div>
                    
                    <div class="feature">
                        <h2>👁️ 视觉处理系统</h2>
                        <p>体验图像识别、UI元素检测、颜色分析等功能</p>
                        <a href="/vision-demo" class="button">视觉处理体验</a>
                    </div>
                    
                    <div class="feature">
                        <h2>📊 系统状态监控</h2>
                        <p>查看系统健康状态、性能指标和运行日志</p>
                        <a href="/health" class="button">系统监控</a>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/video-demo", response_class=HTMLResponse)
        async def video_demo_page():
            """视频演示页面"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>视频到PRD演示</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
                    .result { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>视频到PRD自动生成演示</h1>
                <div class="upload-area">
                    <p>拖拽视频文件到此处或点击选择文件</p>
                    <input type="file" id="videoFile" accept="video/*">
                    <button onclick="uploadVideo()">上传并分析</button>
                </div>
                <div id="result"></div>
                
                <script>
                    async function uploadVideo() {
                        const fileInput = document.getElementById('videoFile');
                        const file = fileInput.files[0];
                        if (!file) {
                            alert('请选择视频文件');
                            return;
                        }
                        
                        const formData = new FormData();
                        formData.append('video', file);
                        
                        document.getElementById('result').innerHTML = '<p>正在处理视频...</p>';
                        
                        try {
                            const response = await fetch('/api/video-to-prd', {
                                method: 'POST',
                                body: formData
                            });
                            
                            const result = await response.json();
                            
                            if (result.success) {
                                document.getElementById('result').innerHTML = `
                                    <div class="result">
                                        <h3>分析结果</h3>
                                        <p><strong>处理时间:</strong> ${result.processing_time.toFixed(2)}秒</p>
                                        <p><strong>视频时长:</strong> ${result.video_analysis.duration}秒</p>
                                        <p><strong>转录文本:</strong> ${result.video_analysis.transcript.substring(0, 200)}...</p>
                                        <h4>生成的PRD内容:</h4>
                                        <pre>${JSON.stringify(result.prd_content, null, 2)}</pre>
                                    </div>
                                `;
                            } else {
                                document.getElementById('result').innerHTML = '<p style="color: red;">处理失败: ' + result.error + '</p>';
                            }
                        } catch (error) {
                            document.getElementById('result').innerHTML = '<p style="color: red;">请求失败: ' + error.message + '</p>';
                        }
                    }
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/collaboration-demo", response_class=HTMLResponse)
        async def collaboration_demo_page():
            """协作演示页面"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>智能体协作演示</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .mode-selector { margin: 20px 0; }
                    .mode-button { margin: 10px; padding: 15px 25px; border: none; border-radius: 5px; cursor: pointer; }
                    .sequential { background: #28a745; color: white; }
                    .parallel { background: #007bff; color: white; }
                    .hybrid { background: #ffc107; color: black; }
                    .result { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>智能体协作模式演示</h1>
                <p>选择不同的协作模式，体验智能体之间的协作效果</p>
                
                <div class="mode-selector">
                    <h3>选择协作模式:</h3>
                    <button class="mode-button sequential" onclick="runDemo('sequential')">串行协作</button>
                    <button class="mode-button parallel" onclick="runDemo('parallel')">并行协作</button>
                    <button class="mode-button hybrid" onclick="runDemo('hybrid')">混合协作</button>
                </div>
                
                <div id="result"></div>
                
                <script>
                    async function runDemo(mode) {
                        document.getElementById('result').innerHTML = '<p>正在运行' + mode + '模式演示...</p>';
                        
                        try {
                            const response = await fetch('/api/collaboration-demo', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ mode: mode })
                            });
                            
                            const result = await response.json();
                            
                            if (result.success) {
                                const demoResult = result.result;
                                document.getElementById('result').innerHTML = `
                                    <div class="result">
                                        <h3>${mode} 模式执行结果</h3>
                                        <p><strong>执行时间:</strong> ${demoResult.result.total_execution_time.toFixed(2)}秒</p>
                                        <p><strong>任务完成:</strong> ${demoResult.result.completed_tasks}/${demoResult.result.task_count}</p>
                                        <h4>对比分析:</h4>
                                        <pre>${JSON.stringify(demoResult.comparison, null, 2)}</pre>
                                    </div>
                                `;
                            } else {
                                document.getElementById('result').innerHTML = '<p style="color: red;">演示失败: ' + result.error + '</p>';
                            }
                        } catch (error) {
                            document.getElementById('result').innerHTML = '<p style="color: red;">请求失败: ' + error.message + '</p>';
                        }
                    }
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/voice-demo", response_class=HTMLResponse)
        async def voice_demo_page():
            """语音演示页面"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>语音交互演示</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .audio-controls { margin: 20px 0; text-align: center; }
                    .record-button { background: #dc3545; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; }
                    .stop-button { background: #6c757d; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; }
                    .result { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>语音交互系统演示</h1>
                <p>点击按钮开始录音，体验语音识别和合成功能</p>
                
                <div class="audio-controls">
                    <button class="record-button" id="recordBtn" onclick="startRecording()">开始录音</button>
                    <button class="stop-button" id="stopBtn" onclick="stopRecording()" disabled>停止录音</button>
                </div>
                
                <div id="result"></div>
                
                <script>
                    let mediaRecorder;
                    let audioChunks = [];
                    
                    async function startRecording() {
                        try {
                            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            mediaRecorder = new MediaRecorder(stream);
                            
                            mediaRecorder.ondataavailable = event => {
                                audioChunks.push(event.data);
                            };
                            
                            mediaRecorder.onstop = async () => {
                                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                                const formData = new FormData();
                                formData.append('audio', audioBlob, 'recording.wav');
                                
                                document.getElementById('result').innerHTML = '<p>正在处理音频...</p>';
                                
                                try {
                                    const response = await fetch('/api/voice-process', {
                                        method: 'POST',
                                        body: formData
                                    });
                                    
                                    const result = await response.json();
                                    
                                    if (result.success) {
                                        document.getElementById('result').innerHTML = `
                                            <div class="result">
                                                <h3>语音处理结果</h3>
                                                <p><strong>识别文本:</strong> ${result.asr.text}</p>
                                                <p><strong>置信度:</strong> ${result.asr.confidence}</p>
                                                <p><strong>情感分析:</strong> ${result.emotion.primary_emotion} (${result.emotion.confidence})</p>
                                                <p><strong>声纹识别:</strong> ${result.voiceprint.speaker_id || '未注册用户'}</p>
                                            </div>
                                        `;
                                    } else {
                                        document.getElementById('result').innerHTML = '<p style="color: red;">处理失败: ' + result.error + '</p>';
                                    }
                                } catch (error) {
                                    document.getElementById('result').innerHTML = '<p style="color: red;">请求失败: ' + error.message + '</p>';
                                }
                            };
                            
                            mediaRecorder.start();
                            document.getElementById('recordBtn').disabled = true;
                            document.getElementById('stopBtn').disabled = false;
                            
                        } catch (error) {
                            alert('无法访问麦克风: ' + error.message);
                        }
                    }
                    
                    function stopRecording() {
                        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                            mediaRecorder.stop();
                            document.getElementById('recordBtn').disabled = false;
                            document.getElementById('stopBtn').disabled = true;
                        }
                    }
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/vision-demo", response_class=HTMLResponse)
        async def vision_demo_page():
            """视觉演示页面"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>视觉处理演示</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
                    .result { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>视觉处理系统演示</h1>
                <p>上传图像，体验视觉识别和分析功能</p>
                
                <div class="upload-area">
                    <p>拖拽图像文件到此处或点击选择文件</p>
                    <input type="file" id="imageFile" accept="image/*">
                    <button onclick="uploadImage()">上传并分析</button>
                </div>
                <div id="result"></div>
                
                <script>
                    async function uploadImage() {
                        const fileInput = document.getElementById('imageFile');
                        const file = fileInput.files[0];
                        if (!file) {
                            alert('请选择图像文件');
                            return;
                        }
                        
                        const formData = new FormData();
                        formData.append('image', file);
                        
                        document.getElementById('result').innerHTML = '<p>正在处理图像...</p>';
                        
                        try {
                            const response = await fetch('/api/vision-process', {
                                method: 'POST',
                                body: formData
                            });
                            
                            const result = await response.json();
                            
                            if (result.success) {
                                document.getElementById('result').innerHTML = `
                                    <div class="result">
                                        <h3>视觉分析结果</h3>
                                        <p><strong>处理时间:</strong> ${result.processing_time.toFixed(2)}秒</p>
                                        <p><strong>检测到的对象:</strong> ${result.objects_detected.join(', ')}</p>
                                        <p><strong>文本内容:</strong> ${result.text_content || '未检测到文本'}</p>
                                        <p><strong>颜色分析:</strong> ${JSON.stringify(result.color_analysis)}</p>
                                        <p><strong>UI元素:</strong> ${JSON.stringify(result.ui_elements)}</p>
                                    </div>
                                `;
                            } else {
                                document.getElementById('result').innerHTML = '<p style="color: red;">处理失败: ' + result.error + '</p>';
                            }
                        } catch (error) {
                            document.getElementById('result').innerHTML = '<p style="color: red;">请求失败: ' + error.message + '</p>';
                        }
                    }
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return JSONResponse({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'web_interface': 'running',
                    'video_demo': 'available',
                    'collaboration_demo': 'available',
                    'voice_demo': 'available',
                    'vision_demo': 'available'
                }
            })
        
        # API路由
        @self.app.post("/api/video-to-prd")
        async def api_video_to_prd(video: UploadFile = File(...)):
            """视频到PRD API"""
            try:
                # 保存上传的视频文件
                temp_path = f"/tmp/{video.filename}"
                with open(temp_path, "wb") as buffer:
                    content = await video.read()
                    buffer.write(content)
                
                # 处理视频
                result = await self.video_demo.process_video_to_prd(temp_path)
                
                # 清理临时文件
                Path(temp_path).unlink(missing_ok=True)
                
                return JSONResponse(result)
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/collaboration-demo")
        async def api_collaboration_demo(request: Dict[str, Any]):
            """协作演示API"""
            try:
                mode = request.get('mode', 'sequential')
                
                if mode == 'sequential':
                    result = await self.collaboration_demo.run_sequential_demo()
                elif mode == 'parallel':
                    result = await self.collaboration_demo.run_parallel_demo()
                elif mode == 'hybrid':
                    result = await self.collaboration_demo.run_hybrid_demo()
                else:
                    raise ValueError(f"不支持的模式: {mode}")
                
                return JSONResponse({
                    'success': True,
                    'result': result
                })
                
            except Exception as e:
                return JSONResponse({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.post("/api/voice-process")
        async def api_voice_process(audio: UploadFile = File(...)):
            """语音处理API"""
            try:
                # 保存上传的音频文件
                temp_path = f"/tmp/{audio.filename}"
                with open(temp_path, "wb") as buffer:
                    content = await audio.read()
                    buffer.write(content)
                
                # 模拟语音处理结果
                result = {
                    'success': True,
                    'asr': {
                        'text': '这是模拟的语音识别结果',
                        'confidence': 0.95
                    },
                    'emotion': {
                        'primary_emotion': 'neutral',
                        'confidence': 0.8
                    },
                    'voiceprint': {
                        'speaker_id': None,
                        'confidence': 0.0
                    },
                    'processing_time': 1.5
                }
                
                # 清理临时文件
                Path(temp_path).unlink(missing_ok=True)
                
                return JSONResponse(result)
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/vision-process")
        async def api_vision_process(image: UploadFile = File(...)):
            """视觉处理API"""
            try:
                # 保存上传的图像文件
                temp_path = f"/tmp/{image.filename}"
                with open(temp_path, "wb") as buffer:
                    content = await image.read()
                    buffer.write(content)
                
                # 模拟视觉处理结果
                result = {
                    'success': True,
                    'objects_detected': ['text', 'button', 'image'],
                    'text_content': '这是模拟的图像文本识别结果',
                    'color_analysis': {
                        'dominant_colors': ['#FF5733', '#33FF57', '#3357FF'],
                        'color_count': 3
                    },
                    'ui_elements': {
                        'buttons': 2,
                        'text_elements': 5,
                        'images': 1
                    },
                    'processing_time': 2.1
                }
                
                # 清理临时文件
                Path(temp_path).unlink(missing_ok=True)
                
                return JSONResponse(result)
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


class CommandLineInterface:
    """命令行接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.video_demo = VideoToPRDDemo()
        self.collaboration_demo = CollaborationModeDemo()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(
            description="NeuralAgent × Agno-BMAD 演示系统",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  python cli_demo.py video-demo --input video.mp4
  python cli_demo.py collaboration-demo --mode sequential
  python cli_demo.py system-health
  python cli_demo.py --help
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # 视频演示命令
        video_parser = subparsers.add_parser('video-demo', help='视频到PRD演示')
        video_parser.add_argument('--input', '-i', required=True, help='输入视频文件路径')
        video_parser.add_argument('--output', '-o', help='输出PRD文档路径')
        
        # 协作演示命令
        collab_parser = subparsers.add_parser('collaboration-demo', help='协作模式演示')
        collab_parser.add_argument('--mode', choices=['sequential', 'parallel', 'hybrid'], 
                                 default='sequential', help='协作模式')
        
        # 系统健康命令
        health_parser = subparsers.add_parser('system-health', help='系统健康检查')
        
        # 批量处理命令
        batch_parser = subparsers.add_parser('batch-demo', help='批量演示')
        batch_parser.add_argument('--video-dir', help='视频文件目录')
        batch_parser.add_argument('--output-dir', help='输出目录')
        
        return parser
    
    async def run_command(self, args: argparse.Namespace) -> int:
        """运行命令"""
        try:
            if args.command == 'video-demo':
                return await self._handle_video_demo(args)
            elif args.command == 'collaboration-demo':
                return await self._handle_collaboration_demo(args)
            elif args.command == 'system-health':
                return await self._handle_system_health(args)
            elif args.command == 'batch-demo':
                return await self._handle_batch_demo(args)
            else:
                print("未知命令，使用 --help 查看帮助")
                return 1
                
        except Exception as e:
            print(f"命令执行失败: {e}")
            return 1
    
    async def _handle_video_demo(self, args: argparse.Namespace) -> int:
        """处理视频演示命令"""
        print(f"🎥 开始处理视频: {args.input}")
        
        if not Path(args.input).exists():
            print(f"错误: 视频文件不存在: {args.input}")
            return 1
        
        start_time = time.time()
        
        try:
            # 处理视频
            result = await self.video_demo.process_video_to_prd(args.input)
            
            if result['success']:
                processing_time = time.time() - start_time
                
                print(f"✅ 视频处理完成!")
                print(f"⏱️  处理时间: {processing_time:.2f}秒")
                print(f"📹 视频时长: {result['video_analysis']['duration']:.1f}秒")
                print(f"📝 转录文本: {result['video_analysis']['transcript'][:100]}...")
                
                # 生成PRD文档
                if args.output:
                    from workflow_demonstration.video_to_prd_demo import PRDContent
                    prd_content = PRDContent(**result['prd_content'])
                    doc_path = self.video_demo.generate_prd_document(prd_content, args.output)
                    print(f"📄 PRD文档已保存: {doc_path}")
                
                return 0
            else:
                print(f"❌ 视频处理失败: {result.get('error', '未知错误')}")
                return 1
                
        except Exception as e:
            print(f"❌ 处理异常: {e}")
            return 1
    
    async def _handle_collaboration_demo(self, args: argparse.Namespace) -> int:
        """处理协作演示命令"""
        print(f"🤝 开始{args.mode}协作模式演示")
        
        start_time = time.time()
        
        try:
            if args.mode == 'sequential':
                result = await self.collaboration_demo.run_sequential_demo()
            elif args.mode == 'parallel':
                result = await self.collaboration_demo.run_parallel_demo()
            elif args.mode == 'hybrid':
                result = await self.collaboration_demo.run_hybrid_demo()
            
            if 'result' in result:
                processing_time = time.time() - start_time
                
                print(f"✅ {args.mode}协作演示完成!")
                print(f"⏱️  执行时间: {processing_time:.2f}秒")
                print(f"📊 任务统计:")
                print(f"   - 总任务数: {result['result'].get('task_count', 0)}")
                print(f"   - 完成任务: {result['result'].get('completed_tasks', 0)}")
                print(f"   - 失败任务: {result['result'].get('failed_tasks', 0)}")
                
                # 显示对比分析
                if 'comparison' in result:
                    print(f"📈 模式对比:")
                    for mode, time_val in result['comparison']['execution_time'].items():
                        print(f"   - {mode}: {time_val:.2f}秒")
                
                return 0
            else:
                print(f"❌ 协作演示失败")
                return 1
                
        except Exception as e:
            print(f"❌ 演示异常: {e}")
            return 1
    
    async def _handle_system_health(self, args: argparse.Namespace) -> int:
        """处理系统健康命令"""
        print("🏥 系统健康检查")
        
        try:
            # 模拟健康检查
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'components': {
                    'web_interface': {'status': 'running', 'response_time': '0.1s'},
                    'video_demo': {'status': 'available', 'response_time': '0.5s'},
                    'collaboration_demo': {'status': 'available', 'response_time': '0.3s'},
                    'voice_demo': {'status': 'available', 'response_time': '0.2s'},
                    'vision_demo': {'status': 'available', 'response_time': '0.4s'}
                },
                'system_resources': {
                    'cpu_usage': '25%',
                    'memory_usage': '45%',
                    'disk_usage': '30%'
                }
            }
            
            print(f"📊 系统状态: {health_status['overall_status']}")
            print(f"🕒 检查时间: {health_status['timestamp']}")
            
            print("\n🔧 组件状态:")
            for component, info in health_status['components'].items():
                status_icon = "✅" if info['status'] in ['running', 'available'] else "❌"
                print(f"   {status_icon} {component}: {info['status']} ({info['response_time']})")
            
            print("\n💻 系统资源:")
            for resource, usage in health_status['system_resources'].items():
                print(f"   - {resource}: {usage}")
            
            return 0
            
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return 1
    
    async def _handle_batch_demo(self, args: argparse.Namespace) -> int:
        """处理批量演示命令"""
        print("🔄 开始批量演示")
        
        if not args.video_dir or not Path(args.video_dir).exists():
            print(f"错误: 视频目录不存在: {args.video_dir}")
            return 1
        
        video_dir = Path(args.video_dir)
        video_files = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi")) + list(video_dir.glob("*.mov"))
        
        if not video_files:
            print(f"警告: 目录中没有找到视频文件: {args.video_dir}")
            return 0
        
        print(f"📁 找到 {len(video_files)} 个视频文件")
        
        results = []
        for video_file in video_files:
            print(f"\n🎥 处理: {video_file.name}")
            try:
                result = await self.video_demo.process_video_to_prd(str(video_file))
                results.append({
                    'file': video_file.name,
                    'success': result['success'],
                    'processing_time': result.get('processing_time', 0)
                })
                
                if result['success']:
                    print(f"   ✅ 成功 ({result.get('processing_time', 0):.1f}秒)")
                else:
                    print(f"   ❌ 失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
                results.append({
                    'file': video_file.name,
                    'success': False,
                    'error': str(e)
                })
        
        # 生成批量处理报告
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            report_path = output_dir / "batch_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total_files': len(video_files),
                    'results': results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 批量处理报告已保存: {report_path}")
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📈 批量处理完成: {success_count}/{len(results)} 成功")
        
        return 0 if success_count > 0 else 1


class APIInterface:
    """API接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.video_demo = VideoToPRDDemo()
        self.collaboration_demo = CollaborationModeDemo()
    
    def create_fastapi_app(self) -> Optional[FastAPI]:
        """创建FastAPI应用"""
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI不可用，无法创建API接口")
            return None
        
        app = FastAPI(title="NeuralAgent × Agno-BMAD API", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "NeuralAgent × Agno-BMAD API", "status": "running"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @app.post("/api/video-to-prd")
        async def video_to_prd(request: Dict[str, Any]):
            video_path = request.get('video_path')
            if not video_path or not Path(video_path).exists():
                raise HTTPException(status_code=400, detail="视频文件不存在")
            
            result = await self.video_demo.process_video_to_prd(video_path)
            return result
        
        @app.post("/api/collaboration-demo")
        async def collaboration_demo(request: Dict[str, Any]):
            mode = request.get('mode', 'sequential')
            
            if mode == 'sequential':
                result = await self.collaboration_demo.run_sequential_demo()
            elif mode == 'parallel':
                result = await self.collaboration_demo.run_parallel_demo()
            elif mode == 'hybrid':
                result = await self.collaboration_demo.run_hybrid_demo()
            else:
                raise HTTPException(status_code=400, detail=f"不支持的模式: {mode}")
            
            return {'success': True, 'result': result}
        
        @app.get("/api/statistics")
        async def get_statistics():
            return {
                'video_demo_stats': self.video_demo.get_demo_statistics(),
                'collaboration_demo_stats': self.collaboration_demo.get_demo_statistics(),
                'timestamp': datetime.now().isoformat()
            }
        
        return app


class UserInterfaceDemo:
    """用户接口演示主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化接口
        self.web_interface = WebInterface()
        self.cli_interface = CommandLineInterface()
        self.api_interface = APIInterface()
        
        # 集成框架
        self.integration_framework = IntegrationFramework()
    
    async def start_web_server(self, host: str = "0.0.0.0", port: int = 8000):
        """启动Web服务器"""
        if not FASTAPI_AVAILABLE or not UVICORN_AVAILABLE:
            self.logger.error("FastAPI或Uvicorn不可用，无法启动Web服务器")
            return False
        
        if not self.web_interface.app:
            self.logger.error("Web界面未正确初始化")
            return False
        
        self.logger.info(f"启动Web服务器: http://{host}:{port}")
        
        try:
            config = uvicorn.Config(
                self.web_interface.app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
            return True
        except Exception as e:
            self.logger.error(f"Web服务器启动失败: {e}")
            return False
    
    async def run_cli_demo(self, args: Optional[List[str]] = None) -> int:
        """运行CLI演示"""
        parser = self.cli_interface.create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        return await self.cli_interface.run_command(parsed_args)
    
    async def start_api_server(self, host: str = "0.0.0.0", port: int = 8080):
        """启动API服务器"""
        app = self.api_interface.create_fastapi_app()
        
        if not app:
            self.logger.error("API接口创建失败")
            return False
        
        if not UVICORN_AVAILABLE:
            self.logger.error("Uvicorn不可用，无法启动API服务器")
            return False
        
        self.logger.info(f"启动API服务器: http://{host}:{port}")
        
        try:
            config = uvicorn.Config(app, host=host, port=port, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
            return True
        except Exception as e:
            self.logger.error(f"API服务器启动失败: {e}")
            return False
    
    def get_interface_info(self) -> Dict[str, Any]:
        """获取接口信息"""
        return {
            'web_interface': {
                'available': FASTAPI_AVAILABLE,
                'url': 'http://localhost:8000' if FASTAPI_AVAILABLE else 'N/A',
                'features': ['视频分析', '协作演示', '语音交互', '视觉处理', '系统监控']
            },
            'cli_interface': {
                'available': True,
                'commands': ['video-demo', 'collaboration-demo', 'system-health', 'batch-demo'],
                'features': ['命令行操作', '批量处理', '系统监控']
            },
            'api_interface': {
                'available': FASTAPI_AVAILABLE,
                'base_url': 'http://localhost:8080' if FASTAPI_AVAILABLE else 'N/A',
                'endpoints': ['/api/video-to-prd', '/api/collaboration-demo', '/api/statistics'],
                'features': ['REST API', 'JSON响应', '程序化访问']
            }
        }