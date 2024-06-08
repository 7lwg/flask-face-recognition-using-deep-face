import os

import cv2
import deepface.DeepFace as DeepFace
from flask import Flask, jsonify, request

image_names = []
k = 0
ips = []
messages = []

app = Flask(__name__)

hello_string = "Hello, world!"


@app.route('/hello', methods=['GET'])
def get_hello_string():
  global hello_string
  if (request.remote_addr not in ips):
    ips.append(request.remote_addr)
    messages.append("Hello, world!")

  return jsonify({'message': messages})


def update_hello_string(new_string):
  global hello_string
  if (request.remote_addr in ips):
    messages[ips.index(request.remote_addr)] = new_string

    hello_string = messages
  else:
    ips.append(request.remote_addr)
    messages.append(new_string)
    # hello_string = new_string
    hello_string = messages


@app.route('/ip', methods=['GET'])
def get_ip():
  global hello_string
  if (request.remote_addr not in ips):
    ips.append(request.remote_addr)
  print(ips)
  return jsonify({'ip': ips})


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def preprocess_image(image_path):
  try:
    # Check if the image file exists
    if not os.path.isfile(image_path):
      raise FileNotFoundError(f"The file {image_path} does not exist.")

    # Read the image using OpenCV
    image = cv2.imread(image_path)

    # Check if the image is read properly
    if image is None:
      raise ValueError(f"The file {image_path} is not a valid image.")

    # Resize the image to a standard size
    standard_size = (224, 224)
    image_resized = cv2.resize(image, standard_size)

    # Save the preprocessed image temporarily
    preprocessed_image_path = "temp_preprocessed_image.jpg"
    cv2.imwrite(preprocessed_image_path, image_resized)

    return preprocessed_image_path

  except Exception as e:
    print(f"Exception while processing {image_path}: {e}")
    return "Error"


def analyze_image(image_path1, image_path2):
  try:

    if image_path1 and image_path2:

      result = DeepFace.verify(img1_path=image_path1, img2_path=image_path2)
      return result
    else:
      print("Preprocessing failed. Unable to analyze the image.")
      return None

  except Exception as e:
    print(f"Exception while analyzing {image_path1}: {e}")
    return None


@app.route('/upload_photo', methods=['POST'])
def upload_photo():
  if 'photo' not in request.files:
    return jsonify({'error': 'No file part in the request'}), 400

  photo = request.files['photo']
  if photo.filename == '':
    return jsonify({'error': 'No selected file'}), 400

  if photo:

    filename = os.path.join(
        app.config['UPLOAD_FOLDER'],
        str(len(image_names)) + ' ' + str(request.remote_addr) + ' ' +
        str(photo.filename))
    image_names.append(request.remote_addr)
    photo.save(filename)

    preprocessed_image_path1 = preprocess_image(filename)
    try:

      detect_face = DeepFace.detectFace(preprocessed_image_path1)
      detected = True
    except:
      detect_face = 0
      detected = False
      print("No faces found in the image.")
    print(str(detect_face) + 'test')

    image_files = [
        f for f in os.listdir(app.config['UPLOAD_FOLDER'])
        if f.endswith('.jpg') or f.endswith('.png')
    ]
    if detected == True:
      print("The image contains faces.")
      update_hello_string("Upload anther image to compare between them")
    else:
      print("No faces found in the image.")
      os.remove(
          os.path.join(app.config['UPLOAD_FOLDER'],
                       image_files[len(image_names) - 1]))
      image_names.pop()

    for i in ips:
      parts = i.split(' ')
      if (image_names.count(i) == 2):
        print("two images found from the same device : " + str(i))
        indices = [
            index for index, value in enumerate(image_names) if value == i
        ]
        print(indices[0])
        print(indices[1])
        print(image_files[indices[0]])
        print(image_files[indices[1]])
        print("true")
        try:
          results = analyze_image(f"uploads/{image_files[indices[0]]}",
                                  f"uploads/{image_files[indices[1]]}")
          # results = analyze_image("cr7.jpg", "cr7.jpg")
          first_item = list(results.values())[0]
          print(first_item)
          print(results)

          if results['verified'] is True:
            # if 4 == 4:
            print("it's a picture of me!")
            update_hello_string("it's a picture of me!")
            os.remove(
                os.path.join(app.config['UPLOAD_FOLDER'],
                             image_files[indices[0]]))
            os.remove(
                os.path.join(app.config['UPLOAD_FOLDER'],
                             image_files[indices[1]]))
            del image_names[indices[1]]
            del image_names[indices[0]]
            return jsonify({
                'message':
                'Deleted all images and uploaded the new one successfully'
            }), 200
          else:
            print("it's not a picture of me!")
            update_hello_string("it's not a picture of me!")
            os.remove(
                os.path.join(app.config['UPLOAD_FOLDER'],
                             image_files[indices[1]]))
            del image_names[indices[1]]

            return jsonify({
                'message':
                'Deleted all images and uploaded the new one successfully'
            }), 200
        except:
          print("error")
          update_hello_string("error")
          # for image_file in image_files:
          os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
          del image_names[-1]
          return jsonify({
              'message':
              'Deleted all images and uploaded the new one successfully'
          }), 200
      else:
        print("false")
    return jsonify({
        'message': 'Photo uploaded successfully',
        'filename': filename
    }), 200
  return jsonify({
      'message': 'Photo uploaded successfully',
      'filename': ""
  }), 200


if __name__ == '__main__':
  app.run(host='0.0.0.0')
