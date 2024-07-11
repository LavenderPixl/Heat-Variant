# base image
FROM node:20-alpine

# set working directory
WORKDIR /app

# add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# install and cache app dependencies
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json

RUN npm install
RUN npm install @vue/cli -g

# copy project files
COPY . /app

EXPOSE 5173
# start app
CMD ["npm", "run", "dev"]


# # Use an official Node.js runtime as a parent image
# FROM node:16

# # Set the working directory
# WORKDIR /app

# # Copy package.json and package-lock.json
# COPY package.json package-lock.json ./

# # Install dependencies including nodemon
# RUN npm install

# # Copy the rest of the application
# COPY . .

# # Expose the application port
# EXPOSE 5173

# # Command to run the application with nodemon
# CMD ["npx", "nodemon", "--watch", ".", "--exec", "npx vue-cli-service serve"]
