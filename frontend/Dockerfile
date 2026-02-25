# Stage 1: Build the Vite + React Frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies exclusively based on package-lock integrity
COPY package*.json ./
RUN npm ci

# Copy the frontend app source code
COPY . .

# Accept Supabase environment parameters as ARG injects during Docker execution builds
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# Assign ARGS to direct ENV params for the Vite `build` pipeline
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Compile the static dist output folder
RUN npm run build

# Stage 2: Serve the compiled SPA via an unprivileged Nginx server container
FROM nginx:alpine

# Copy the bundled assets out of the stage 1 builder node
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom single-page-app Nginx config supporting React Router history
# (We handle fallback to index.html manually instead of 404s)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port 80 to the internal bridge network
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
