# inference.py
import cv2
import numpy as np

class PIDController:
    """一個簡單的 PID 控制器"""
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp  # 比例 Proportional
        self.Ki = Ki  # 積分 Integral
        self.Kd = Kd  # 微分 Derivative
        self.reset()

    def reset(self):
        """重置控制器狀態"""
        self.integral = 0.0
        self.previous_error = 0.0

    def update(self, error):
        """
        根據當前誤差計算控制輸出
        :param error: 當前誤差 (例如, target_x - current_x)
        :return: 控制量 (例如, 滑鼠應移動的量)
        """
        # 積分項
        self.integral += error
        
        # 微分項
        derivative = error - self.previous_error
        
        # 計算輸出
        output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)
        
        # 更新上一次的誤差
        self.previous_error = error
        
        return output

def preprocess_image(image, model_input_size):
    """預處理圖像以適配ONNX模型"""
    resized = cv2.resize(image, (model_input_size, model_input_size))
    rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = rgb_image.astype(np.float32) / 255.0
    input_tensor = np.transpose(normalized, (2, 0, 1))
    input_tensor = np.expand_dims(input_tensor, axis=0)
    return input_tensor

def postprocess_outputs(outputs, original_width, original_height, model_input_size, min_confidence):
    """後處理ONNX模型輸出"""
    predictions = outputs[0][0].T
    boxes, confidences = [], []
    scale_x = original_width / model_input_size
    scale_y = original_height / model_input_size

    for detection in predictions:
        confidence = detection[4]
        if confidence >= min_confidence:
            cx, cy, w, h = detection[:4]
            x1 = (cx - w / 2) * scale_x
            y1 = (cy - h / 2) * scale_y
            x2 = (cx + w / 2) * scale_x
            y2 = (cy + h / 2) * scale_y
            boxes.append([x1, y1, x2, y2])
            confidences.append(confidence)
            
    return boxes, confidences

def non_max_suppression(boxes, confidences, iou_threshold=0.4):
    """非極大值抑制"""
    if len(boxes) == 0:
        return [], []
    
    boxes = np.array(boxes)
    confidences = np.array(confidences)
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    order = confidences.argsort()[::-1]
    
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        if len(order) == 1:
            break
        
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        
        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        intersection = w * h
        union = areas[i] + areas[order[1:]] - intersection
        iou = intersection / union
        
        order = order[1:][iou <= iou_threshold]
        
    return boxes[keep].tolist(), confidences[keep].tolist()