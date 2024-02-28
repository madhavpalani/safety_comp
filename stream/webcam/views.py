from django.http import StreamingHttpResponse
from ultralytics.utils.plotting import Annotator
from ultralytics import YOLO
import cv2
import re
from .models import Employee1, Supervisor, Alert
from django.shortcuts import render
import plotly.express as px
from django.core.mail import send_mail
import datetime
from stream.simple_facerec import SimpleFacerec
import time
import pandas as pd

sfr = SimpleFacerec()
sfr.load_encoding_images('images/')
emails = []
emails1 = []
emails2 = []
label1 = []
face_first_detected = {}  # Dictionary to store the first detection time
face_last_detected = {}  # Dictionary to store the last detection time
total_duration = {}
model = YOLO('best_v8.pt')
model.conf = 0.45

# Create your views here.

def stream():
    cap = cv2.VideoCapture(0)  # Use 0 for the default webcam, or specify the camera index

    while True:
        current_time = datetime.datetime.now()
        ret, frame = cap.read()

        if not ret:
            break
        label1 = []
        results = model(frame, verbose=False)

        # Perform face detection using OpenCV
        for r in results:

            annotator = Annotator(frame)

            boxes = r.boxes
            labels = []
            for box in boxes:
                b = box.xyxy[0]  # get box coordinates in (top, left, bottom, right) format
                c = box.cls
                label = model.names[int(c)]
                labels.append(label)
                annotator.box_label(b, label)
                print(model.names[int(c)])
                label1 = labels
                print(label1)
                label1 = [item for item in label1 if 'no' in item]
                print(label1)

        frame = annotator.result()
        # face detection
        face_locations, face_names = sfr.detect_known_faces(frame)
        print(face_names)
        for face_loc, name in zip(face_locations, face_names):
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

            # Draw a rectangle around the detected face
            if name != 'Unknown':
                # Display the recognized name (you can use the label to map to a name)
                try:
                    # Query the database to get the email associated with the name
                    employee = Employee1.objects.get(name=name)
                    email = employee.email
                    emails.append(email)
                    print(emails)
                    sup1 = employee.sup_id
                    supervisor = Supervisor.objects.get(sup_id=sup1)
                    email1 = supervisor.email
                    emails1.append(email1)
                    print(emails1)

                except Employee1.DoesNotExist:
                    email = "Nope"
                    emails.append(email)

                equip = ['no helmet', 'no vests', 'no shoes']
                set_l1 = set(label1)
                set_l2 = set(equip)
                print(set_l1)
                print(set_l2)
                elements_str = ' '.join(map(str, set_l1))
                for email in emails:
                    if any("no" in label for label in label1) and email != 'Nope':
                        print('test')
                        subject = 'WARNING'
                        message = f'You didnt wear the necessary equipment {elements_str} in the sector at {current_time}'
                        from_email = 'plmadhav03@gmail.com'  # Replace with your email address
                        samp = []
                        samp.append(email)
                        # Use the email address from the database as the recipient
                        recipient_list = samp

                        # Send the email
                        send_mail(subject, message, from_email, recipient_list)
                        alert_name = f'{name} didnt wear the necessary equipment {elements_str} in the sector'
                        alert = Alert(name=alert_name)
                        alert.save()
                        print("Mail sent")
                        samp = []
                        if emails1:
                            samp.append(emails1[len(emails1) - 1])
                            message1 = f'{name} didnt wear the necessary equipment {elements_str} in the sector at {current_time}'
                            recipient_list = samp
                            send_mail(subject, message1, from_email, recipient_list)
                            print("Mail sent")
                            samp = []

            elif name == 'Unknown':
                samp = []
                supervisor = Supervisor.objects.get(sup_id=1002)
                email2 = supervisor.email
                from_email = "plmadhav03@gmail.com"
                samp.append(email2)
                subject = "TRESPASSER ENTERED"
                message2 = f"Trespasser is entered at {current_time}"
                recipient_list = samp
                send_mail(subject, message2, from_email, recipient_list)
                print('mail sent')
                samp = []
                alert_name = f'Trespasser entry in the sector'
                alert = Alert(name=alert_name)
                alert.save()

        # Display the frame with detections
        image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # Return emails1 after processing is complete
    print(emails1)
    return emails1


def video_feed(request):
    return StreamingHttpResponse(stream(), content_type='multipart/x-mixed-replace; boundary=frame')


def alert_history(request):
    alerts = Alert.objects.all()
    names = Employee1.objects.values_list('name', flat=True)
    violations_by_employee = {}
    violations_by_employee['Unknown'] = 0
    for name in names:
        violations_count = Alert.objects.filter(name__icontains=name).count()
        violations_by_employee[name] = violations_count
    violations_count = Alert.objects.filter(name__icontains='Trespasser').count()
    violations_by_employee['Unknown'] = violations_count
    print(violations_by_employee)
    labels = list(violations_by_employee.keys())
    values = list(violations_by_employee.values())
    alert_entries = Alert.objects.all()  # Retrieve all alert entries

    # Extracting name and creating a DataFrame
    data = []
    name_pattern = r'(\w+)'  # Regular expression to extract the first word as the name (change as per your log structure)

    for entry in alert_entries:
        match = re.search(name_pattern, entry.name)
        name1 = match.group(1) if match else None
        if name1:
            data.append({'name': name1, 'timestamp': entry.timestamp})

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(data)

    # Display the DataFrame
    print(df)
    # Plotting the line graph using Plotly
    df['timestamp'] = pd.to_datetime(df['timestamp'])

     #Extract date to create a new 'date' column
    df['date'] = df['timestamp'].dt.date

    # Group by 'date' and 'name' to count violations for each person on each day
    violations_count = df.groupby(['date', 'name']).size().reset_index(name='violation_count')

    # Plotting separate lines for each person
    fig = px.bar(violations_count, x='date', y='violation_count', color='name', title='Violations by Person Each Day')
    chart_html = fig.to_html()
    fig_pie = px.pie(names=labels, values=values, title='Pie chart')
    chart_html_pie = fig_pie.to_html()
    context = {'chart_html': chart_html,
               'chart_html_pie': chart_html_pie,
               'alerts': alerts}
    return render(request, 'alert_history.html', context)


def index(request):
    # Capture emails1 returned by the stream function
    return render(request, 'index.html')


def web(request):
    return render(request, 'web.html')


def stream1(request):
    cap = cv2.VideoCapture(0)  # Use 0 for the default webcam, or specify the camera index
    while True:
        ret, frame = cap.read()
        face_locations, face_names = sfr.detect_known_faces(frame)

        current_time = time.time()

        # Process faces that were detected before
        for name, last_detected_time in face_last_detected.copy().items():
            if name not in face_names:
                # Calculate the duration for this face
                first_detected_time = face_first_detected.pop(name, None)
                if first_detected_time is not None:
                    duration = last_detected_time - first_detected_time
                    total_duration[name] = total_duration.get(name, 0) + duration

        for face_loc, name in zip(face_locations, face_names):
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

            if name not in face_first_detected:
                face_first_detected[name] = current_time
            face_last_detected[name] = current_time

            # Display the duration on the frame in seconds
            duration = face_last_detected[name] - face_first_detected[name]
            text = f"{name} ({int(duration)} sec)"
            cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

        # Display the frame with detections
        image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n')


def video_feed1(request):
    return StreamingHttpResponse(stream1(request), content_type='multipart/x-mixed-replace; boundary=frame')


def web1(request):
    return render(request, 'web1.html', {'total_duration': total_duration})


def history(request):
    file_name = 'total_duration.txt'
    # Open the file in write mode
    with open(file_name, 'w') as file:
        for key, value in total_duration.items():
            file.write(f'{key}:{value}\n')

    print(f'Dictionary has been stored in {file_name}')
    return render(request, 'history.html', {'total_duration': total_duration})


def visualize(request):
    names = Employee1.objects.values_list('name', flat=True)
    violations_by_employee = {}
    violations_by_employee['Unknown'] = 0
    for name in names:
        violations_count = Alert.objects.filter(name__icontains=name).count()
        violations_by_employee[name] = violations_count
    violations_count = Alert.objects.filter(name__icontains='Trespasser').count()
    violations_by_employee['Unknown'] = violations_count
    print(violations_by_employee)
    labels = list(violations_by_employee.keys())
    values = list(violations_by_employee.values())
    fig = px.bar(x=labels, y=values, labels={'x': 'Employee', 'y': 'Violations'})
    chart_html = fig.to_html()
    fig_pie = px.pie(names=labels, values=values, title='Violations by Employee')
    chart_html_pie = fig_pie.to_html()
    context = {'chart_html': chart_html,
               'chart_html_pie': chart_html_pie}
    return render(request, 'visualize.html', context)
