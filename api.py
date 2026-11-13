import os
import json
import shutil
import subprocess
import tempfile
from flask import Flask, request, jsonify, Response, render_template_string
from build_resume import build

app = Flask(__name__)

# Request size cap: 256 KB
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

LATEX_TIMEOUT = int(os.environ.get("LATEX_TIMEOUT", "30"))
API_KEY = os.environ.get("API_KEY")

# Load sample resume for Swagger examples
SAMPLE_RESUME_PATH = os.path.join(os.path.dirname(__file__), "sample_resume.json")
try:
    with open(SAMPLE_RESUME_PATH, "r", encoding="utf-8") as f:
        SAMPLE_RESUME = json.load(f)
except Exception:
    SAMPLE_RESUME = {"name": "Aakash Chavla"}

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "ATS Resume Builder API",
        "description": "High-performance REST API converting structured resume JSON into ATS-optimized LaTeX and single-page PDFs via isolated pdflatex compilation.",
        "version": "1.0.0"
    },
    "servers": [
        {"url": "/", "description": "Current Server"}
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {
                    "200": {
                        "description": "Server is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "ok"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/resume/tex": {
            "post": {
                "summary": "Generate LaTeX Source",
                "description": "Converts resume JSON into fully-escaped LaTeX document matching the ATS template.",
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ResumeRequest"},
                            "example": SAMPLE_RESUME
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Rendered LaTeX source code",
                        "content": {
                            "text/plain": {
                                "schema": {"type": "string"}
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/400Error"},
                    "401": {"$ref": "#/components/responses/401Error"},
                    "500": {"$ref": "#/components/responses/500Error"}
                }
            }
        },
        "/resume/pdf": {
            "post": {
                "summary": "Generate ATS Resume PDF",
                "description": "Compiles the generated LaTeX into a clean, ATS-parsable PDF file via pdflatex.",
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ResumeRequest"},
                            "example": SAMPLE_RESUME
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Compiled PDF file attachment",
                        "headers": {
                            "Content-Disposition": {
                                "schema": {"type": "string", "example": "attachment; filename=\"resume.pdf\""}
                            }
                        },
                        "content": {
                            "application/pdf": {
                                "schema": {"type": "string", "format": "binary"}
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/400Error"},
                    "401": {"$ref": "#/components/responses/401Error"},
                    "500": {"$ref": "#/components/responses/500Error"}
                }
            }
        }
    },
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        },
        "responses": {
            "400Error": {
                "description": "Validation or bad request error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"error": {"type": "string"}}
                        }
                    }
                }
            },
            "401Error": {
                "description": "Unauthorized - Missing or invalid API key",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"error": {"type": "string", "example": "Unauthorized"}}
                        }
                    }
                }
            },
            "500Error": {
                "description": "LaTeX compilation or server error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "details": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        "schemas": {
            "ResumeRequest": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "example": "Jane Doe"},
                    "contact": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "example": "San Francisco, CA"},
                            "phone": {"type": "string", "example": "+1 (555) 123-4567"},
                            "email": {"type": "string", "example": "jane.doe@example.com"},
                            "linkedin": {"type": "string", "example": "https://linkedin.com/in/janedoe/"},
                            "github": {"type": "string", "example": "https://github.com/janedoe/"},
                            "website": {"type": "string", "example": "https://janedoe.dev"}
                        }
                    },
                    "summary": {
                        "type": "string",
                        "example": "Backend Software Engineer with 1.5+ years of experience in Java, Python, Node.js, and LLM applications."
                    },
                    "skills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string", "example": "Languages"},
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "example": ["Java", "Python", "Node.js", "SQL"]
                                }
                            }
                        }
                    },
                    "experience": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "company": {"type": "string", "example": "Tech Corp"},
                                "location": {"type": "string", "example": "San Francisco, CA"},
                                "title": {"type": "string", "example": "Backend Developer"},
                                "dates": {"type": "string", "example": "June 2023 -- Present"},
                                "bullets": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "example": ["Architected microservices handling 2M+ daily requests."]
                                }
                            }
                        }
                    },
                    "projects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "example": "SmartResume AI"},
                                "tech": {"type": "string", "example": "Python, Flask, Docker, LaTeX"},
                                "link": {"type": "string", "example": "https://github.com/janedoe/smart-resume"},
                                "bullets": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "example": ["Automated ATS-compliant resume compilation using LaTeX."]
                                }
                            }
                        }
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "school": {"type": "string", "example": "UC Berkeley"},
                                "location": {"type": "string", "example": "Berkeley, CA"},
                                "degree": {"type": "string", "example": "B.S. in Computer Science"},
                                "dates": {"type": "string", "example": "2019 -- 2023"},
                                "details": {"type": "string", "example": "Relevant Coursework: Distributed Systems."}
                            }
                        }
                    },
                    "certifications": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["AWS Certified Solutions Architect"]
                    },
                    "achievements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["1st place in Regional AI Hackathon 2024"]
                    },
                    "section_order": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["summary", "skills", "experience", "projects", "education", "certifications", "achievements"]
                    }
                }
            }
        }
    }
}

SWAGGER_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Swagger UI - ATS Resume Builder API</title>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
  <link rel="icon" type="image/png" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/favicon-32x32.png" sizes="32x32" />
  <style>
    html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }
    .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
  window.onload = function() {
    window.ui = SwaggerUIBundle({
      url: "/swagger.json",
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIStandalonePreset
      ],
      plugins: [
        SwaggerUIBundle.plugins.DownloadUrl
      ],
      layout: "StandaloneLayout"
    });
  };
  </script>
</body>
</html>
"""

PUBLIC_PATHS = {"/health", "/docs", "/swagger", "/swagger.json"}

@app.before_request
def check_auth():
    if request.path in PUBLIC_PATHS or request.path.startswith("/docs") or request.path.startswith("/swagger"):
        return None
    if API_KEY:
        header_key = request.headers.get("X-API-Key")
        if header_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
    return None

def validate_input(data):
    if not isinstance(data, dict):
        return "Body must be a JSON object"

    if "name" not in data or not str(data["name"]).strip():
        return "'name' is required"

    contact = data.get("contact")
    if contact is not None and not isinstance(contact, dict):
        return "'contact' must be an object"

    list_fields = [
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
        "achievements",
        "section_order",
    ]
    for field in list_fields:
        if field in data and data[field] is not None and not isinstance(data[field], list):
            return f"'{field}' must be a list"

    return None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/swagger.json", methods=["GET"])
def swagger_json():
    return jsonify(OPENAPI_SPEC)

@app.route("/docs", methods=["GET"])
@app.route("/swagger", methods=["GET"])
def swagger_ui():
    return render_template_string(SWAGGER_HTML_TEMPLATE)

@app.route("/resume/tex", methods=["POST"])
def get_tex():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON"}), 400

    error = validate_input(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        tex_content = build(data)
        return Response(tex_content, mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return jsonify({"error": f"Failed to generate TeX: {str(e)}"}), 500

@app.route("/resume/pdf", methods=["POST"])
def get_pdf():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON"}), 400

    error = validate_input(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        tex_content = build(data)
    except Exception as e:
        return jsonify({"error": f"Failed to generate TeX: {str(e)}"}), 500

    temp_dir = tempfile.mkdtemp(prefix="resume_compile_")
    try:
        tex_path = os.path.join(temp_dir, "resume.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        env = os.environ.copy()
        env["openin_any"] = "p"
        env["openout_any"] = "p"

        # Run pdflatex with relative filename resume.tex
        cmd = [
            "pdflatex",
            "-no-shell-escape",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "resume.tex",
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=LATEX_TIMEOUT,
        )

        log_path = os.path.join(temp_dir, "resume.log")
        pdf_path = os.path.join(temp_dir, "resume.pdf")

        if result.returncode != 0 or not os.path.exists(pdf_path):
            log_output = ""
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        log_output = lf.read()
                except Exception:
                    pass
            if not log_output:
                log_output = result.stdout or ""

            details = log_output[-1500:] if len(log_output) > 1500 else log_output
            return jsonify({"error": "PDF generation failed", "details": details}), 500

        with open(pdf_path, "rb") as pf:
            pdf_bytes = pf.read()

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="resume.pdf"'},
        )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "PDF generation failed", "details": f"pdflatex timed out after {LATEX_TIMEOUT}s"}), 500
    except Exception as e:
        return jsonify({"error": "PDF generation failed", "details": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
