FROM nikolaik/python-nodejs:python3.10-nodejs19

# 替换旧的 Debian Buster 源为归档源，并关闭过期校验
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until

# 安装 ffmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/
WORKDIR /app/

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -U -r requirements.txt

# 启动脚本
CMD bash start
