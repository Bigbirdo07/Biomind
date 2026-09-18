"""
src/bioreason/server.py

Unified HTTP server for BioReason Chat and Guided Pipeline Mode.
Serves static frontend assets (chat/ directory) and provides backend API endpoints:
- POST /api/chat
- POST /api/pipeline/update
- POST /api/pipeline/inspect
- GET /api/status
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional

from bioreason.pipeline.engine import BioReasonPipelineEngine
from bioreason.schemas.guided_pipeline import GuidedPipelineResponse, ResponseSource
from bioreason.models.inference_router import BioReasonInferenceError

CHAT_DIR = Path(__file__).resolve().parent.parent.parent / "chat"
WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent


class BioReasonRequestHandler(SimpleHTTPRequestHandler):
    """Handles static file requests from chat/ and API requests."""

    engine = BioReasonPipelineEngine()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CHAT_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            model_status = self.engine.inference_router.startup_status if self.engine.inference_router else {
                "status": "READY",
                "backend": "injected_adapter",
            }
            status_data = {
                "status": "ready" if model_status.get("status") == "READY" else "model_unavailable",
                "model_name": "BR-VERIFIED-SFT-002",
                "checkpoint": "BR-VERIFIED-SFT-002 (final_adapter)",
                "pipeline_mode": "DYNAMIC_MODEL_DRIVEN",
                "engine": "BioReasonPipelineEngine",
                "model_status": model_status,
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        # Default static file handling
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
        elif self.path == "/api/pipeline/update":
            self._handle_pipeline_update()
        elif self.path == "/api/pipeline/inspect":
            self._handle_pipeline_inspect()
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_chat(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            req_data = json.loads(body)
        except Exception as e:
            self._send_json_error(400, f"Invalid JSON payload: {str(e)}")
            return

        session_id = req_data.get("activeChatId", "default_session")
        messages = req_data.get("messages", [])
        dev_mode = req_data.get("devMode", False)

        if not messages:
            self._send_json_error(400, "No messages provided.")
            return

        last_user_msg = messages[-1]
        user_text = last_user_msg.get("content", "")
        attachment = last_user_msg.get("attachmentName")

        try:
            response: GuidedPipelineResponse = self.engine.process_turn(
                session_id=session_id,
                user_message=user_text,
                conversation_history=messages[:-1],
                attached_file_path=attachment,
                dev_mode=dev_mode,
            )
            resp_dict = response.model_dump()
            self._send_json_response(200, resp_dict)
        except BioReasonInferenceError as e:
            err_resp = {
                "status": "error",
                "mode": "conversational",
                "message": f"BIOREASON_INFERENCE_FAILED: {str(e)}",
                "source_trace": ResponseSource.ERROR.value,
                "model_checkpoint": "BR-VERIFIED-SFT-002",
                "diagnostics": {
                    "error": str(e),
                    "exception_type": type(e).__name__,
                    "model_status": self.engine.inference_router.startup_status if self.engine.inference_router else None,
                },
                "provenance": {
                    "conversation_id": session_id,
                    "turn_id": len(messages),
                    "model": "BR-VERIFIED-SFT-002",
                    "checkpoint": "BR-VERIFIED-SFT-002 (final_adapter)",
                    "response_source": ResponseSource.ERROR.value,
                    "mode": "ERROR",
                },
            }
            self._send_json_response(500, err_resp)
        except Exception as e:
            err_resp = {
                "status": "error",
                "mode": "conversational",
                "message": f"BIOREASON_INFERENCE_FAILED: {str(e)}",
                "source_trace": ResponseSource.ERROR.value,
                "model_checkpoint": "BR-VERIFIED-SFT-002",
                "diagnostics": {"error": str(e), "exception_type": type(e).__name__},
            }
            self._send_json_response(500, err_resp)

    def _handle_pipeline_update(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            req_data = json.loads(body)
            session_id = req_data.get("activeChatId", "default_session")
            key = req_data.get("key")
            value = req_data.get("value")

            mgr = self.engine.get_or_create_state_manager(session_id)
            if key == "N_PCS":
                try:
                    mgr.context.n_pcs = int(value)
                except ValueError:
                    pass
            elif key == "COUNTS_FILE":
                mgr.context.file_paths["counts"] = str(value)
            elif key == "METADATA_FILE":
                mgr.context.file_paths["metadata"] = str(value)

            # Regenerate pipeline data
            pipeline_data = self.engine.generator.build_guided_pipeline(mgr.context)
            mgr.generated_pipeline = pipeline_data

            self._send_json_response(200, {
                "status": "success",
                "guided_pipeline": pipeline_data.model_dump(),
                "pipeline_context": mgr.context.model_dump(),
                "source_trace": ResponseSource.BACKEND_DERIVED.value,
            })
        except Exception as e:
            self._send_json_error(500, f"Pipeline update failed: {str(e)}")

    def _handle_pipeline_inspect(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            req_data = json.loads(body)
            file_path = req_data.get("filePath", "")
            inspection = self.engine.file_inspector.inspect_file(file_path)
            self._send_json_response(200, inspection)
        except Exception as e:
            self._send_json_error(500, f"Inspection failed: {str(e)}")

    def _send_json_response(self, code: int, data: Dict[str, Any]):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_json_error(self, code: int, message: str):
        self._send_json_response(code, {
            "status": "error",
            "message": message,
            "source_trace": ResponseSource.ERROR.value
        })


def run_server(port: int = 8088):
    server_address = ("", port)
    httpd = HTTPServer(server_address, BioReasonRequestHandler)
    print(f"BioReason Chat Server running on http://localhost:{port} (Serving {CHAT_DIR})")
    if BioReasonRequestHandler.engine.inference_router:
        BioReasonRequestHandler.engine.inference_router.print_startup_banner()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping BioReason server.")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
    run_server(port)
