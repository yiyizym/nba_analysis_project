#!/usr/bin/env python3
"""
文章语音生成脚本

使用 edge-tts 将 Markdown 文章转换为语音。
支持长文章分段处理和音频拼接。

用法:
    python scripts/text_to_speech.py data/articles/article.md
    python scripts/text_to_speech.py data/articles/article.md -o output.mp3
    python scripts/text_to_speech.py data/articles/article.md --voice zh-CN-XiaoxiaoNeural
    python scripts/text_to_speech.py --test "这是一个测试"

依赖:
    pip install edge-tts pydub
    系统需要安装 ffmpeg
"""

import sys
import re
import argparse
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

try:
    import edge_tts
except ImportError:
    print("请先安装 edge-tts: pip install edge-tts")
    sys.exit(1)

try:
    from pydub import AudioSegment
except ImportError:
    print("请先安装 pydub: pip install pydub")
    sys.exit(1)

# 默认配置
DEFAULT_VOICE = "zh-CN-YunxiNeural"  # 男声
DEFAULT_RATE = "+0%"  # 正常语速
MAX_SEGMENT_LENGTH = 2000  # 每段最大字符数
AUDIO_OUTPUT_DIR = Path("data/audio")


def clean_markdown(text: str) -> str:
    """
    清理 Markdown 格式，保留纯文本。

    Args:
        text: Markdown 格式文本

    Returns:
        清理后的纯文本
    """
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # 移除 Markdown 标题符号，保留标题文本
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # 移除加粗和斜体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # 移除链接，保留文本
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 移除图片
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    # 移除分隔线
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*\*+\s*$', '', text, flags=re.MULTILINE)

    # 移除表格
    text = re.sub(r'\|[^\n]+\|', '', text)
    text = re.sub(r'^[\s\-|]+$', '', text, flags=re.MULTILINE)

    # 移除列表符号
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 移除 emoji（可选，保留也可以）
    # text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)

    # 移除多余空白行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    # 去除首尾空白
    text = text.strip()

    return text


def split_text(text: str, max_length: int = MAX_SEGMENT_LENGTH) -> List[str]:
    """
    智能分割文本为多个片段。

    策略:
    1. 按段落分割
    2. 短段落合并
    3. 长段落按句子切分

    Args:
        text: 要分割的文本
        max_length: 每段最大字符数

    Returns:
        文本片段列表
    """
    # 按段落分割
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    segments = []
    current_segment = ""

    for para in paragraphs:
        # 如果当前段落本身就超长，需要按句子切分
        if len(para) > max_length:
            # 先保存当前累积的内容
            if current_segment:
                segments.append(current_segment.strip())
                current_segment = ""

            # 按句子切分长段落
            sentences = split_into_sentences(para)
            for sentence in sentences:
                if len(current_segment) + len(sentence) + 1 <= max_length:
                    current_segment += sentence
                else:
                    if current_segment:
                        segments.append(current_segment.strip())
                    current_segment = sentence

        # 正常段落，尝试合并
        elif len(current_segment) + len(para) + 2 <= max_length:
            if current_segment:
                current_segment += "\n\n" + para
            else:
                current_segment = para
        else:
            # 当前段无法合并，保存并开始新段
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = para

    # 保存最后一段
    if current_segment:
        segments.append(current_segment.strip())

    return segments


def split_into_sentences(text: str) -> List[str]:
    """
    将文本按句子分割。

    Args:
        text: 要分割的文本

    Returns:
        句子列表
    """
    # 中文和英文句号
    pattern = r'([。！？!?])'
    parts = re.split(pattern, text)

    sentences = []
    current = ""

    for part in parts:
        current += part
        if re.match(pattern, part):
            sentences.append(current)
            current = ""

    if current.strip():
        sentences.append(current)

    return sentences


async def text_to_speech_segment(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE
) -> bool:
    """
    生成单个音频片段。

    Args:
        text: 要转换的文本
        output_path: 输出文件路径
        voice: 语音名称
        rate: 语速调整

    Returns:
        是否成功
    """
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  生成音频失败: {e}")
        return False


def merge_audio_files(audio_files: List[str], output_path: str) -> bool:
    """
    合并多个音频文件。

    Args:
        audio_files: 音频文件路径列表
        output_path: 输出文件路径

    Returns:
        是否成功
    """
    try:
        if len(audio_files) == 1:
            # 只有一个文件，直接复制
            shutil.copy(audio_files[0], output_path)
            return True

        # 合并多个音频
        combined = AudioSegment.empty()

        for audio_file in audio_files:
            segment = AudioSegment.from_mp3(audio_file)
            # 添加短暂停顿（300ms）
            combined += segment + AudioSegment.silent(duration=300)

        # 导出
        combined.export(output_path, format="mp3")
        return True

    except Exception as e:
        print(f"合并音频失败: {e}")
        return False


async def generate_speech(
    input_file: str,
    output_file: Optional[str] = None,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    verbose: bool = True
) -> bool:
    """
    主函数：将文章转换为语音。

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选）
        voice: 语音名称
        rate: 语速调整
        verbose: 是否显示详细信息

    Returns:
        是否成功
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"文件不存在: {input_file}")
        return False

    # 读取文件
    if verbose:
        print(f"读取文件: {input_file}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 清理 Markdown
    text = clean_markdown(content)

    if not text:
        print("文件内容为空")
        return False

    if verbose:
        print(f"文本长度: {len(text)} 字符")

    # 分割文本
    segments = split_text(text)

    if verbose:
        print(f"分割为 {len(segments)} 个片段")

    # 确定输出路径
    if output_file:
        output_path = Path(output_file)
    else:
        AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = AUDIO_OUTPUT_DIR / f"{input_path.stem}.mp3"

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    temp_files = []

    try:
        # 生成各段音频
        for i, segment in enumerate(segments):
            if verbose:
                print(f"  生成片段 {i+1}/{len(segments)} ({len(segment)} 字符)...", end=" ")

            temp_file = Path(temp_dir) / f"segment_{i:03d}.mp3"
            success = await text_to_speech_segment(segment, str(temp_file), voice, rate)

            if success:
                temp_files.append(str(temp_file))
                if verbose:
                    print("完成")
            else:
                if verbose:
                    print("失败")
                return False

        # 合并音频
        if verbose:
            print(f"合并 {len(temp_files)} 个音频文件...")

        success = merge_audio_files(temp_files, str(output_path))

        if success:
            if verbose:
                print(f"输出文件: {output_path}")
            return True
        else:
            return False

    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_speech(text: str, voice: str = DEFAULT_VOICE) -> bool:
    """
    测试语音生成。

    Args:
        text: 测试文本
        voice: 语音名称

    Returns:
        是否成功
    """
    print(f"测试文本: {text}")
    print(f"使用语音: {voice}")

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = AUDIO_OUTPUT_DIR / "test.mp3"

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_file))
        print(f"输出文件: {output_file}")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


async def list_voices():
    """列出可用的中文语音。"""
    voices = await edge_tts.list_voices()

    print("可用的中文语音:")
    print("-" * 60)

    for voice in voices:
        if voice["Locale"].startswith("zh-"):
            gender = "男" if voice["Gender"] == "Male" else "女"
            print(f"  {voice['ShortName']} ({gender}) - {voice['Locale']}")


def main():
    parser = argparse.ArgumentParser(
        description='将 Markdown 文章转换为语音',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/text_to_speech.py data/articles/article.md
  python scripts/text_to_speech.py data/articles/article.md -o output.mp3
  python scripts/text_to_speech.py data/articles/article.md --voice zh-CN-XiaoxiaoNeural
  python scripts/text_to_speech.py --test "这是一个测试"
  python scripts/text_to_speech.py --list-voices
        """
    )

    parser.add_argument('input', type=str, nargs='?', help='输入文件路径')
    parser.add_argument('-o', '--output', type=str, help='输出文件路径')
    parser.add_argument('--voice', type=str, default=DEFAULT_VOICE,
                        help=f'语音名称 (默认: {DEFAULT_VOICE})')
    parser.add_argument('--rate', type=str, default=DEFAULT_RATE,
                        help=f'语速调整 (默认: {DEFAULT_RATE})，如 "+10%", "-20%"')
    parser.add_argument('--test', type=str, metavar='TEXT',
                        help='测试模式：生成指定文本的语音')
    parser.add_argument('--list-voices', action='store_true',
                        help='列出可用的中文语音')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='安静模式，减少输出')

    args = parser.parse_args()

    # 列出语音
    if args.list_voices:
        asyncio.run(list_voices())
        return 0

    # 测试模式
    if args.test:
        success = asyncio.run(test_speech(args.test, args.voice))
        return 0 if success else 1

    # 正常模式
    if not args.input:
        parser.print_help()
        return 1

    success = asyncio.run(generate_speech(
        args.input,
        args.output,
        args.voice,
        args.rate,
        verbose=not args.quiet
    ))

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
