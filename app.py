import os
import uuid
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g, make_response
from werkzeug.utils import secure_filename
from openai import OpenAI

import config
from animal_data import (
    ANIMAL_CATEGORIES,
    ANIMALS_DATA,
    get_animals_by_category,
    get_animal_detail,
)

app = Flask(__name__)
app.config.from_object("config")

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# ---------------------------
# i18n (简单稳定的本地方案)
# ---------------------------
LANGS = [
    ("en", "English"),
    ("zh", "中文"),
    ("ko", "한국어"),
]

TRANSLATIONS = {
    "en": {
        "site_title": "Animal Vision & Encyclopedia",
        "nav_home": "Home",
        "nav_encyclopedia": "Encyclopedia",
        "upload_title": "Animal Identification",
        "upload_hint": "Upload an image to identify animals using a vision model.",
        "upload_button": "Upload & Identify",
        "supported_formats": "Supported formats",
        "max_size": "Max size",
        "category_title": "Categories",
        "view_category": "View Category",
        "back_home": "Back to Home",
        "animals_in_category": "Animals in this category",
        "learn_more": "Learn more",
        "scientific_name": "Scientific name",
        "conservation_status": "Conservation status",
        "habitat": "Habitat",
        "distribution": "Distribution",
        "characteristics": "Key characteristics",
        "facts": "Fun facts",
        "upload_error_no_file": "No file uploaded.",
        "upload_error_empty": "No file selected.",
        "upload_error_type": "Unsupported file format.",
        "upload_error_process": "Processing failed.",
        "model_result": "Model description",
    },
    "zh": {
        "site_title": "动物识别与动物百科",
        "nav_home": "首页",
        "nav_encyclopedia": "动物百科",
        "upload_title": "动物识别",
        "upload_hint": "上传图片，使用视觉模型识别动物并生成科普介绍。",
        "upload_button": "上传并识别",
        "supported_formats": "支持格式",
        "max_size": "最大大小",
        "category_title": "动物分类",
        "view_category": "查看分类",
        "back_home": "返回首页",
        "animals_in_category": "本分类动物",
        "learn_more": "了解更多",
        "scientific_name": "学名",
        "conservation_status": "保护等级",
        "habitat": "栖息地",
        "distribution": "分布范围",
        "characteristics": "主要特征",
        "facts": "有趣事实",
        "upload_error_no_file": "没有文件上传。",
        "upload_error_empty": "没有选择文件。",
        "upload_error_type": "不支持的文件格式。",
        "upload_error_process": "处理失败。",
        "model_result": "模型描述",
    },
    "ko": {
        "site_title": "동물 인식 & 동물 백과",
        "nav_home": "홈",
        "nav_encyclopedia": "백과",
        "upload_title": "동물 인식",
        "upload_hint": "이미지를 업로드하면 시각 모델이 동물을 식별하고 설명을 생성합니다.",
        "upload_button": "업로드 및 인식",
        "supported_formats": "지원 형식",
        "max_size": "최대 크기",
        "category_title": "분류",
        "view_category": "카테고리 보기",
        "back_home": "홈으로",
        "animals_in_category": "이 카테고리의 동물",
        "learn_more": "더 알아보기",
        "scientific_name": "학명",
        "conservation_status": "보전 상태",
        "habitat": "서식지",
        "distribution": "분포",
        "characteristics": "주요 특징",
        "facts": "재미있는 사실",
        "upload_error_no_file": "파일이 업로드되지 않았습니다.",
        "upload_error_empty": "파일을 선택하지 않았습니다.",
        "upload_error_type": "지원하지 않는 파일 형식입니다.",
        "upload_error_process": "처리 실패.",
        "model_result": "모델 설명",
    },
}


def get_lang():
    lang = request.args.get("lang") or request.cookies.get("lang")
    if lang not in dict(LANGS):
        lang = "en"
    return lang


@app.before_request
def set_lang():
    g.lang = get_lang()


def t(key: str):
    return (
        TRANSLATIONS.get(g.lang, {}).get(key)
        or TRANSLATIONS["en"].get(key)
        or key
    )


@app.context_processor
def inject_i18n():
    return {
        "t": t,
        "current_lang": lambda: g.lang,
        "langs": LANGS,
    }


@app.template_filter("l10n")
def l10n(value):
    """模板里安全取多语言字段"""
    if isinstance(value, dict):
        return value.get(g.lang) or value.get("en") or next(iter(value.values()), "")
    return value


# ---------------------------
# 文件处理
# ---------------------------
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def file_to_data_url(local_path: str):
    ext = local_path.rsplit(".", 1)[1].lower()
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")

    with open(local_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def identify_animal(image_url: str):
    """使用 Qwen 视觉模型识别图片中的动物"""
    try:
        client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.DASHSCOPE_BASE_URL,
        )

        completion = client.chat.completions.create(
            model=config.QWEN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {
                            "type": "text",
                            "text": (
                                "Please carefully examine this image. "
                                "If there is an animal, describe it in this format:\n\n"
                                "1. Animal name (English + scientific name)\n"
                                "2. Key features\n"
                                "3. Behavior\n"
                                "4. Habitat\n"
                                "5. Fun facts\n\n"
                                "If there is no animal, describe the main content of the image."
                            ),
                        },
                    ],
                }
            ],
        )

        return {"success": True, "content": completion.choices[0].message.content}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------
# 路由
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html", categories=ANIMAL_CATEGORIES)


@app.route("/category/<category_id>")
def category(category_id):
    if category_id not in ANIMAL_CATEGORIES:
        return "Category not found", 404

    category_info = ANIMAL_CATEGORIES[category_id]
    animals = get_animals_by_category(category_id)

    return render_template(
        "category.html",
        category_id=category_id,
        category_info=category_info,
        animals=animals,
    )


@app.route("/animal/<animal_id>")
def animal_detail(animal_id):
    animal = get_animal_detail(animal_id)
    if not animal:
        return "Animal not found", 404

    category_info = ANIMAL_CATEGORIES[animal["category"]]

    return render_template(
        "animal_detail.html",
        animal_id=animal_id,
        animal=animal,
        category_info=category_info,
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": t("upload_error_no_file")}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": t("upload_error_empty")}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {
                "success": False,
                "error": f'{t("upload_error_type")} '
                f'({", ".join(sorted(config.ALLOWED_EXTENSIONS))})',
            }
        ), 400

    local_path = None

    try:
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

        local_path = os.path.join(config.UPLOAD_FOLDER, unique_filename)
        file.save(local_path)

        # 不强依赖 OSS，直接用 data URL
        image_url = file_to_data_url(local_path)

        identify_result = identify_animal(image_url)

        if not identify_result["success"]:
            return jsonify(
                {"success": False, "error": identify_result["error"]}
            ), 500

        return jsonify(
            {
                "success": True,
                "image_url": image_url,  # 前端可直接预览
                "description": identify_result["content"],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": f'{t("upload_error_process")} {e}'}), 500

    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
