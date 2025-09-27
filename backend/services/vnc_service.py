import asyncio
import os
import subprocess
from typing import Dict, Optional


class VNCService:
    """Service for managing VNC server for remote browser display"""

    def __init__(self):
        self.vnc_process: Optional[subprocess.Popen] = None
        self.display_process: Optional[subprocess.Popen] = None

        # Configuration from environment
        self.vnc_port = int(os.getenv("VNC_PORT", "5901"))
        self.vnc_password = os.getenv("VNC_PASSWORD", "webagent")
        self.vnc_display = os.getenv("VNC_DISPLAY", ":1")
        self.width = int(os.getenv("BROWSER_WIDTH", "1920"))
        self.height = int(os.getenv("BROWSER_HEIGHT", "1080"))

    async def start(self):
        """Start VNC server and virtual display"""
        try:
            # Start virtual display (Xvfb)
            await self._start_virtual_display()

            # Start VNC server
            await self._start_vnc_server()

            print(f"VNC service started on display {self.vnc_display}:{self.vnc_port}")

        except Exception as e:
            print(f"Error starting VNC service: {e}")
            await self.stop()
            raise

    async def _start_virtual_display(self):
        """Start Xvfb virtual display"""
        try:
            # Kill any existing display
            subprocess.run(
                ["pkill", "-f", f"Xvfb.*{self.vnc_display}"],
                capture_output=True
            )

            # Start Xvfb
            self.display_process = subprocess.Popen([
                "Xvfb",
                self.vnc_display,
                "-screen", "0", f"{self.width}x{self.height}x24",
                "-ac",
                "+extension", "GLX",
                "+render",
                "-noreset"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait a bit for display to start
            await asyncio.sleep(2)

            # Set DISPLAY environment variable
            os.environ["DISPLAY"] = self.vnc_display

            print(f"Virtual display started: {self.vnc_display}")

        except Exception as e:
            print(f"Error starting virtual display: {e}")
            raise

    async def _start_vnc_server(self):
        """Start VNC server (x11vnc)"""
        try:
            # Kill any existing VNC server
            subprocess.run(
                ["pkill", "-f", f"x11vnc.*{self.vnc_display}"],
                capture_output=True
            )

            # Create VNC password file
            password_file = "/tmp/vncpasswd"
            subprocess.run([
                "x11vnc", "-storepasswd", self.vnc_password, password_file
            ], check=True)

            # Start x11vnc
            self.vnc_process = subprocess.Popen([
                "x11vnc",
                "-display", self.vnc_display,
                "-rfbport", str(self.vnc_port),
                "-passwd", password_file,
                "-shared",
                "-forever",
                "-noxdamage",
                "-noxfixes",
                "-noxcomposite",
                "-bg",
                "-nopw"  # Remove this if you want password protection
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for VNC server to start
            await asyncio.sleep(2)

            print(f"VNC server started on port {self.vnc_port}")

        except Exception as e:
            print(f"Error starting VNC server: {e}")
            raise

    async def stop(self):
        """Stop VNC server and virtual display"""
        try:
            # Stop VNC server
            if self.vnc_process:
                self.vnc_process.terminate()
                try:
                    self.vnc_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.vnc_process.kill()

            # Stop virtual display
            if self.display_process:
                self.display_process.terminate()
                try:
                    self.display_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.display_process.kill()

            # Kill any remaining processes
            subprocess.run(
                ["pkill", "-f", f"x11vnc.*{self.vnc_display}"],
                capture_output=True
            )
            subprocess.run(
                ["pkill", "-f", f"Xvfb.*{self.vnc_display}"],
                capture_output=True
            )

            print("VNC service stopped")

        except Exception as e:
            print(f"Error stopping VNC service: {e}")

    def get_connection_info(self) -> Dict:
        """Get VNC connection information for clients"""
        return {
            "host": "localhost",
            "port": self.vnc_port,
            "display": self.vnc_display,
            "width": self.width,
            "height": self.height,
            "ws_url": f"ws://localhost:{self.vnc_port + 1000}/websockify"  # noVNC WebSocket
        }

    def is_running(self) -> bool:
        """Check if VNC service is running"""
        try:
            if self.vnc_process and self.display_process:
                return (
                    self.vnc_process.poll() is None and
                    self.display_process.poll() is None
                )
            return False
        except:
            return False