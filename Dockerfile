FROM python:3.10-alpine
RUN apk add --no-cache build-base
ADD ./ /
RUN pip3 install --upgrade pip
RUN pip3 install pipenv
RUN pipenv install --system --deploy
CMD [ "python", "./manage.py", "run", "0.0.0.0:5000"]