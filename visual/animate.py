"""
Module for creating educational animations using OpenCV.
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path


class Animator:
    """
    Creates educational animations frame by frame.
    """
    def __init__(self, width: int = 800, height: int = 600, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.frames = []
    
    def create_blank_frame(self, bg_color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """Create a blank frame with specified background color."""
        return np.full((self.height, self.width, 3), bg_color, dtype=np.uint8)
    
    def add_text(self, frame: np.ndarray, text: str, position: Tuple[int, int],
                 font_scale: float = 1.0, color: Tuple[int, int, int] = (0, 0, 0),
                 thickness: int = 2) -> np.ndarray:
        """Add text to a frame."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
        return frame
    
    def add_circle(self, frame: np.ndarray, center: Tuple[int, int], radius: int,
                   color: Tuple[int, int, int] = (0, 0, 255), thickness: int = -1) -> np.ndarray:
        """Add a circle to a frame."""
        cv2.circle(frame, center, radius, color, thickness)
        return frame
    
    def add_rectangle(self, frame: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int],
                      color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """Add a rectangle to a frame."""
        cv2.rectangle(frame, pt1, pt2, color, thickness)
        return frame
    
    def add_arrow(self, frame: np.ndarray, start: Tuple[int, int], end: Tuple[int, int],
                  color: Tuple[int, int, int] = (0, 0, 255), thickness: int = 2) -> np.ndarray:
        """Add an arrow to a frame."""
        cv2.arrowedLine(frame, start, end, color, thickness, tipLength=0.3)
        return frame
    
    def add_frame(self, frame: np.ndarray, duration_frames: int = 1) -> None:
        """Add a frame to the animation, repeating it for the specified duration."""
        for _ in range(duration_frames):
            self.frames.append(frame.copy())
    
    def save_video(self, output_path: str, codec: str = 'mp4v') -> None:
        """
        Save the animation as a video file.
        
        Args:
            output_path: Path to save the video
            codec: Video codec to use
        """
        if not self.frames:
            raise ValueError("No frames to save")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        
        try:
            for frame in self.frames:
                out.write(frame)
        finally:
            out.release()
    
    def clear_frames(self) -> None:
        """Clear all frames."""
        self.frames = []


def create_tcp_handshake_animation(output_path: str = "data/animations/tcp_handshake.mp4") -> str:
    """
    Create an animation demonstrating TCP 3-way handshake.
    
    Args:
        output_path: Path to save the animation
        
    Returns:
        Path to the saved animation
    """
    animator = Animator(width=800, height=600, fps=30)
    
    # Positions
    client_x, client_y = 150, 300
    server_x, server_y = 650, 300
    
    # Frame 1: Initial state
    frame = animator.create_blank_frame()
    frame = animator.add_text(frame, "TCP 3-Way Handshake", (250, 50), font_scale=1.5, color=(0, 0, 0))
    frame = animator.add_circle(frame, (client_x, client_y), 40, color=(100, 100, 255))
    frame = animator.add_text(frame, "Client", (client_x - 30, client_y + 80), color=(0, 0, 0))
    frame = animator.add_circle(frame, (server_x, server_y), 40, color=(255, 100, 100))
    frame = animator.add_text(frame, "Server", (server_x - 30, server_y + 80), color=(0, 0, 0))
    animator.add_frame(frame, duration_frames=30)
    
    # Frame 2: SYN
    frame = frame.copy()
    frame = animator.add_arrow(frame, (client_x + 50, client_y - 20), (server_x - 50, server_y - 20), 
                              color=(0, 255, 0), thickness=3)
    frame = animator.add_text(frame, "SYN", (400, 250), color=(0, 200, 0), font_scale=0.8)
    animator.add_frame(frame, duration_frames=30)
    
    # Frame 3: SYN-ACK
    frame = animator.create_blank_frame()
    frame = animator.add_text(frame, "TCP 3-Way Handshake", (250, 50), font_scale=1.5, color=(0, 0, 0))
    frame = animator.add_circle(frame, (client_x, client_y), 40, color=(100, 100, 255))
    frame = animator.add_text(frame, "Client", (client_x - 30, client_y + 80), color=(0, 0, 0))
    frame = animator.add_circle(frame, (server_x, server_y), 40, color=(255, 100, 100))
    frame = animator.add_text(frame, "Server", (server_x - 30, server_y + 80), color=(0, 0, 0))
    frame = animator.add_arrow(frame, (server_x - 50, server_y + 20), (client_x + 50, client_y + 20),
                              color=(0, 0, 255), thickness=3)
    frame = animator.add_text(frame, "SYN-ACK", (370, 350), color=(0, 0, 200), font_scale=0.8)
    animator.add_frame(frame, duration_frames=30)
    
    # Frame 4: ACK
    frame = animator.create_blank_frame()
    frame = animator.add_text(frame, "TCP 3-Way Handshake", (250, 50), font_scale=1.5, color=(0, 0, 0))
    frame = animator.add_circle(frame, (client_x, client_y), 40, color=(100, 100, 255))
    frame = animator.add_text(frame, "Client", (client_x - 30, client_y + 80), color=(0, 0, 0))
    frame = animator.add_circle(frame, (server_x, server_y), 40, color=(255, 100, 100))
    frame = animator.add_text(frame, "Server", (server_x - 30, server_y + 80), color=(0, 0, 0))
    frame = animator.add_arrow(frame, (client_x + 50, client_y), (server_x - 50, server_y),
                              color=(255, 0, 0), thickness=3)
    frame = animator.add_text(frame, "ACK", (400, 300), color=(200, 0, 0), font_scale=0.8)
    animator.add_frame(frame, duration_frames=30)
    
    # Frame 5: Connected
    frame = animator.create_blank_frame()
    frame = animator.add_text(frame, "Connection Established!", (220, 50), font_scale=1.5, color=(0, 200, 0))
    frame = animator.add_circle(frame, (client_x, client_y), 40, color=(0, 255, 0))
    frame = animator.add_text(frame, "Client", (client_x - 30, client_y + 80), color=(0, 0, 0))
    frame = animator.add_circle(frame, (server_x, server_y), 40, color=(0, 255, 0))
    frame = animator.add_text(frame, "Server", (server_x - 30, server_y + 80), color=(0, 0, 0))
    animator.add_frame(frame, duration_frames=60)
    
    animator.save_video(output_path)
    return output_path


def create_stack_animation(output_path: str = "data/animations/stack.mp4") -> str:
    """
    Create an animation demonstrating stack operations.
    
    Args:
        output_path: Path to save the animation
        
    Returns:
        Path to the saved animation
    """
    animator = Animator(width=800, height=600, fps=30)
    
    stack_x, stack_y = 400, 400
    item_height = 50
    item_width = 150
    
    # Initial empty stack
    frame = animator.create_blank_frame()
    frame = animator.add_text(frame, "Stack: LIFO Data Structure", (200, 50), font_scale=1.2, color=(0, 0, 0))
    animator.add_frame(frame, duration_frames=30)
    
    # Push operations
    elements = ["Item 1", "Item 2", "Item 3"]
    for i, element in enumerate(elements):
        frame = animator.create_blank_frame()
        frame = animator.add_text(frame, "Stack: LIFO Data Structure", (200, 50), font_scale=1.2, color=(0, 0, 0))
        frame = animator.add_text(frame, f"PUSH: {element}", (300, 100), font_scale=0.8, color=(0, 150, 0))
        
        # Draw existing items
        for j in range(i + 1):
            y_pos = stack_y - (j * item_height)
            frame = animator.add_rectangle(frame, 
                                          (stack_x - item_width // 2, y_pos - item_height),
                                          (stack_x + item_width // 2, y_pos),
                                          color=(100, 200, 255), thickness=-1)
            frame = animator.add_rectangle(frame,
                                          (stack_x - item_width // 2, y_pos - item_height),
                                          (stack_x + item_width // 2, y_pos),
                                          color=(0, 0, 0), thickness=2)
            frame = animator.add_text(frame, elements[j], 
                                     (stack_x - 35, y_pos - 15), 
                                     font_scale=0.7, color=(0, 0, 0))
        
        animator.add_frame(frame, duration_frames=45)
    
    # Pop operation
    frame = animator.create_blank_frame()
    frame = animator.add_text(frame, "Stack: LIFO Data Structure", (200, 50), font_scale=1.2, color=(0, 0, 0))
    frame = animator.add_text(frame, "POP: Item 3", (300, 100), font_scale=0.8, color=(200, 0, 0))
    
    # Draw remaining items
    for j in range(2):
        y_pos = stack_y - (j * item_height)
        frame = animator.add_rectangle(frame,
                                      (stack_x - item_width // 2, y_pos - item_height),
                                      (stack_x + item_width // 2, y_pos),
                                      color=(100, 200, 255), thickness=-1)
        frame = animator.add_rectangle(frame,
                                      (stack_x - item_width // 2, y_pos - item_height),
                                      (stack_x + item_width // 2, y_pos),
                                      color=(0, 0, 0), thickness=2)
        frame = animator.add_text(frame, elements[j],
                                 (stack_x - 35, y_pos - 15),
                                 font_scale=0.7, color=(0, 0, 0))
    
    animator.add_frame(frame, duration_frames=60)
    
    animator.save_video(output_path)
    return output_path
