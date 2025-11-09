import numpy as np
import cv2
# import RPi.GPIO as GPIO


def draw_largest_box(image, boxes, scores):
    if len(boxes) == 0:
        return image, None

    num_boxes = boxes.shape[0]


    #find the largest box

    #chatgpt generated this to find the index of the largest box in one line
    idx = max(range(len(boxes)), key=lambda i: (boxes[i][2]-boxes[i][0]) * (boxes[i][3]-boxes[i][1]))


    box = boxes[idx]
    score = scores[idx][0]

    # Convert the box coordinates to integers
    box = box.astype(int)

    # Draw the box on the image
    cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

    # Define the text parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    color = (255, 255, 255)
    thickness = 1

    # Create the text string
    text = '{:.2f}'.format(score)

    # Determine the text size
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

    # Define the text position relative to the box
    text_x = box[0]
    text_y = box[1] - text_size[1]

    # Draw the text background rectangle
    cv2.rectangle(image, (text_x, text_y), (text_x + text_size[0], text_y + text_size[1]), (0, 255, 0), -1)

    # Draw the text on top of the background rectangle
    cv2.putText(image, text, (text_x, text_y + text_size[1]), font, font_scale, color, thickness)

    #returns the image and ((x_min, y_min), (x_max, y_max))
    return image, ((box[0], box[1]), (box[2], box[3]))


#midpoint of the face box and the size of the frame
def center(midpoint, size):
    x_mid = size[1]//2
    y_mid = size[0]//2

    x = midpoint[0]
    y = midpoint[1]
    print(y)
    
    #we only rotate by a tiny bit. we can probably just recursively call it until it's centered
    #the left right rotation might be wrong cuz mirroring
    if (x < x_mid):
        #rotate_left()
        print("rotate left", end = " ")
        pass
    elif (x > x_mid):
        #rotate_right()
        print("rotate right", end = " ")
        pass
    if (y < y_mid):
        #rotate_up()
        print("rotate up")
        pass
    elif (y > y_mid):
        #rotate_down()
        print("rotate down")
        pass
