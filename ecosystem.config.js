module.exports = {
  apps: [
    {
      name: "fastapi-app",
      script: "uvicorn",
      args: "api:app --host 0.0.0.0 --port 8003",
      interpreter: "./venv/bin/python",
      env: {
        PYTHONUNBUFFERED: "1",
      },
      watch: false, // Đặt thành true nếu bạn muốn PM2 theo dõi các thay đổi và tự động khởi động lại
      autorestart: true,
      max_memory_restart: "2G",
      output: "./logs/out.log",
      error: "./logs/error.log",
    },
  ],
};
