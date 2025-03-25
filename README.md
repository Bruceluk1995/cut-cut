# TikTok视频混剪工具

这是一个使用Python和FFmpeg开发的TikTok视频混剪工具，可以从多个视频中随机选择片段并合成新的视频。

## 功能特点

- 自定义片段时长和数量
- 可视化视频文件选择
- 支持多选和批量操作
- 自动调整视频尺寸至TikTok标准分辨率(1080x1920)
- 智能背景模糊填充
- 实时处理进度显示
- 支持视频预览
- 自定义输出文件夹
- 保留原始视频文件

## 系统要求

- Python 3.x
- FFmpeg (需要添加到系统PATH中)
- 依赖包：
  - tkinter (Python标准库)
  - pillow >= 9.0.0

## 安装说明

1. 确保已安装Python 3.x和FFmpeg
2. 克隆或下载本项目
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行程序：
   ```bash
   python src/main.py
   ```

2. 使用界面：
   - 点击"浏览"选择输入视频文件夹
   - 点击"浏览"选择输出文件夹（混剪后的视频将保存在这里）
   - 设置每个片段的时长（秒）和需要的片段数量
   - 在视频列表中选择要使用的视频
   - 点击"开始混剪"开始处理

3. 操作提示：
   - 双击视频可以预览
   - 点击复选框可以选择/取消选择视频
   - 使用"全选"/"取消全选"按钮批量操作
   - 处理完成后会在指定的输出文件夹生成"mixed_output.mp4"文件
   - 原始视频文件不会被修改或删除

## 注意事项

- 确保选择的视频数量大于或等于需要的片段数量
- 处理过程中请勿关闭程序
- 临时文件会自动清理
- 建议使用较短的片段时长以获得更好的效果
- 确保输出文件夹有足够的存储空间

## 错误处理

如果遇到以下情况，程序会显示错误提示：
- 未选择输入视频文件夹
- 未选择输出文件夹
- 输入的参数无效
- 未选择任何视频
- 选中的视频数量不足
- FFmpeg处理失败
- 输出文件夹空间不足

## 许可证

MIT License 